"""AsyncClient provides an easy-to-use async client library to connect to Axiom."""

import os
import gzip
import ujson
import httpx
from typing import Optional, List, Dict
from dataclasses import asdict
from urllib.parse import urlparse
from humps import decamelize

from .client import (
    IngestStatus,
    IngestOptions,
    ContentType,
    ContentEncoding,
    WrongQueryKindException,
    AplOptions,
    AXIOM_URL,
    PersonalTokenNotSupportedForEdgeError,
)
from .datasets_async import AsyncDatasetsClient
from .annotations_async import AsyncAnnotationsClient
from .tokens_async import AsyncTokensClient
from .users_async import AsyncUsersClient
from .query import (
    QueryLegacy,
    QueryResult,
    QueryOptions,
    QueryLegacyResult,
    QueryKind,
)
from .util import from_dict, handle_json_serialization, is_personal_token
from ._http_client import get_common_headers, async_retry, DEFAULT_TIMEOUT
from ._error_handling import check_response_error


class AsyncClient:
    """The async client class allows you to connect to Axiom using async/await."""

    datasets: AsyncDatasetsClient
    users: AsyncUsersClient
    annotations: AsyncAnnotationsClient
    tokens: AsyncTokensClient
    client: httpx.AsyncClient

    def __init__(
        self,
        token: Optional[str] = None,
        org_id: Optional[str] = None,
        url: Optional[str] = None,
        edge_url: Optional[str] = None,
    ):
        """
        Initialize the async Axiom client.

        Args:
            token: API token for authentication (or set AXIOM_TOKEN env var).
                Edge endpoints require API tokens (xaat-), not personal
                tokens (xapt-).
            org_id: Optional organization ID (or set AXIOM_ORG_ID env var)
            url: Optional base URL (defaults to https://api.axiom.co)
            edge_url: Edge URL for ingest/query operations (e.g.,
                "https://eu-central-1.aws.edge.axiom.co"). When set, ingest
                requests use `/v1/ingest/{dataset}` and query requests use
                `/v1/query/_apl`.
                Must be passed explicitly (not read from environment).

        Example:
            ```python
            async with AsyncClient(token="your-token") as client:
                await client.ingest_events("dataset", [{"field": "value"}])
            ```
        """
        # fallback to env variables if token, org_id or url are not provided
        if token is None:
            token = os.getenv("AXIOM_TOKEN")
        if org_id is None:
            org_id = os.getenv("AXIOM_ORG_ID")
        if url is None:
            url = AXIOM_URL

        # Note: edge_url is NOT auto-read from environment.
        # Edge configuration must be explicit to avoid accidentally routing
        # all requests through edge when AXIOM_EDGE_URL is set for
        # edge-specific tests. Create a separate AsyncClient with edge_url
        # for edge operations.

        # Normalize empty strings to None for edge config
        edge_url = edge_url or None

        # Store for building ingest/query endpoints
        self._token = token
        self._edge_url = edge_url

        # Get common headers
        headers = get_common_headers(token, org_id)

        # Create httpx async client
        self.client = httpx.AsyncClient(
            base_url=url.rstrip("/"),
            timeout=DEFAULT_TIMEOUT,
            headers=headers,
            follow_redirects=True,
        )

        # Initialize sub-clients
        self.datasets = AsyncDatasetsClient(self.client)
        self.users = AsyncUsersClient(self.client, is_personal_token(token))
        self.annotations = AsyncAnnotationsClient(self.client)
        self.tokens = AsyncTokensClient(self.client)

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically closes the client."""
        await self.close()

    async def close(self):
        """
        Close the underlying HTTP client.

        This should be called when you're done with the client to clean up resources.
        If using the context manager (async with), this is called automatically.
        """
        await self.client.aclose()

    def is_edge_configured(self) -> bool:
        """Check if edge is configured."""
        return self._edge_url is not None

    def _get_edge_ingest_url(self, dataset: str) -> Optional[str]:
        """
        Get the full edge ingest URL for a dataset.
        Returns None if edge is not configured.
        """
        if self._edge_url is None:
            return None

        url = self._edge_url.rstrip("/")
        parsed = urlparse(url)
        path = parsed.path

        # If path is empty or just "/", append edge ingest format
        if path == "" or path == "/":
            return f"{parsed.scheme}://{parsed.netloc}/v1/ingest/{dataset}"

        # edge_url has a custom path, use as-is
        return url

    def _get_edge_query_url(self) -> Optional[str]:
        """
        Get the full edge query URL.
        Returns None if edge is not configured.
        """
        if self._edge_url is None:
            return None

        url = self._edge_url.rstrip("/")
        parsed = urlparse(url)
        path = parsed.path

        # If path is empty or just "/", append edge query format
        if path == "" or path == "/":
            return f"{parsed.scheme}://{parsed.netloc}/v1/query/_apl"

        # edge_url has a custom path, use as-is
        return url

    async def ingest(
        self,
        dataset: str,
        payload: bytes,
        contentType: ContentType,
        enc: ContentEncoding,
        opts: Optional[IngestOptions] = None,
    ) -> IngestStatus:
        """
        Asynchronously ingest the payload into the named dataset and return the status.

        If edge is configured, uses the edge endpoint. Edge endpoints require
        API tokens (xaat-), not personal tokens (xapt-).

        Args:
            dataset: Dataset name
            payload: Raw bytes to ingest
            contentType: Content type (JSON, NDJSON, CSV)
            enc: Content encoding (IDENTITY, GZIP)
            opts: Optional ingestion options

        Returns:
            IngestStatus with details about the ingestion

        See https://axiom.co/docs/restapi/endpoints/ingestIntoDataset
        """
        # Check if edge is configured and build appropriate URL
        edge_url = self._get_edge_ingest_url(dataset)
        if edge_url is not None:
            # Edge endpoints only support API tokens, not personal tokens
            if is_personal_token(self._token):
                raise PersonalTokenNotSupportedForEdgeError()
            path = edge_url
        else:
            # Legacy path format for backwards compatibility
            path = f"/v1/datasets/{dataset}/ingest"

        # set headers
        headers = {
            "Content-Type": contentType.value,
            "Content-Encoding": enc.value,
        }

        # prepare query params
        params = self._prepare_ingest_options(opts)

        # Make request with retry logic
        @async_retry()
        async def _make_request():
            return await self.client.post(
                path, content=payload, headers=headers, params=params
            )

        response = await _make_request()
        check_response_error(response.status_code, response.json())

        status_snake = decamelize(response.json())
        return from_dict(IngestStatus, status_snake)

    async def ingest_events(
        self,
        dataset: str,
        events: List[dict],
        opts: Optional[IngestOptions] = None,
    ) -> IngestStatus:
        """
        Asynchronously ingest the events into the named dataset and return the status.

        Args:
            dataset: Dataset name
            events: List of event dictionaries to ingest
            opts: Optional ingestion options

        Returns:
            IngestStatus with details about the ingestion

        Example:
            ```python
            async with AsyncClient(token="...") as client:
                status = await client.ingest_events(
                    "my-dataset",
                    [{"field": "value"}, {"field": "value2"}]
                )
                print(f"Ingested {status.ingested} events")
            ```

        See https://axiom.co/docs/restapi/endpoints/ingestIntoDataset
        """
        # encode request payload to NDJSON
        content = "\n".join(
            ujson.dumps(event, default=handle_json_serialization)
            for event in events
        ).encode("UTF-8")
        gzipped = gzip.compress(content)

        return await self.ingest(
            dataset, gzipped, ContentType.NDJSON, ContentEncoding.GZIP, opts
        )

    async def query_legacy(
        self, id: str, query: QueryLegacy, opts: QueryOptions
    ) -> QueryLegacyResult:
        """
        Asynchronously execute the given structured query on the dataset
        identified by its id.

        Args:
            id: Dataset identifier
            query: Legacy query object
            opts: Query options

        Returns:
            QueryLegacyResult with query results

        See https://axiom.co/docs/restapi/endpoints/queryDataset
        """
        if not opts.saveAsKind or (opts.saveAsKind == QueryKind.APL):
            raise WrongQueryKindException(
                "invalid query kind %s: must be %s or %s"
                % (opts.saveAsKind, QueryKind.ANALYTICS, QueryKind.STREAM)
            )

        path = f"/v1/datasets/{id}/query"
        payload = ujson.dumps(asdict(query), default=handle_json_serialization)
        params = self._prepare_query_options(opts)

        @async_retry()
        async def _make_request():
            return await self.client.post(path, content=payload, params=params)

        response = await _make_request()
        check_response_error(response.status_code, response.json())

        result = from_dict(QueryLegacyResult, response.json())
        query_id = response.headers.get("X-Axiom-History-Query-Id")
        result.savedQueryID = query_id
        return result

    async def apl_query(
        self, apl: str, opts: Optional[AplOptions] = None
    ) -> QueryResult:
        """
        Asynchronously execute the given APL query.

        This is an alias for query().

        Args:
            apl: APL query string
            opts: Optional APL query options

        Returns:
            QueryResult with query results

        See https://axiom.co/docs/restapi/endpoints/queryApl
        """
        return await self.query(apl, opts)

    async def query(
        self, apl: str, opts: Optional[AplOptions] = None
    ) -> QueryResult:
        """
        Asynchronously execute the given APL query.

        If edge is configured, uses the edge endpoint. Edge endpoints require
        API tokens (xaat-), not personal tokens (xapt-).

        Args:
            apl: APL query string
            opts: Optional APL query options

        Returns:
            QueryResult with query results

        Example:
            ```python
            async with AsyncClient(token="...") as client:
                result = await client.query("['my-dataset'] | limit 100")
                for match in result.matches:
                    print(match)
            ```

        See https://axiom.co/docs/restapi/endpoints/queryApl
        """
        # Check if edge is configured and build appropriate URL
        edge_url = self._get_edge_query_url()
        if edge_url is not None:
            # Edge endpoints only support API tokens, not personal tokens
            if is_personal_token(self._token):
                raise PersonalTokenNotSupportedForEdgeError()
            path = edge_url
        else:
            # Legacy path format for backwards compatibility
            path = "/v1/datasets/_apl"

        payload = ujson.dumps(
            self._prepare_apl_payload(apl, opts),
            default=handle_json_serialization,
        )
        params = self._prepare_apl_options(opts)

        @async_retry()
        async def _make_request():
            return await self.client.post(path, content=payload, params=params)

        response = await _make_request()
        check_response_error(response.status_code, response.json())

        result = from_dict(QueryResult, response.json())
        query_id = response.headers.get("X-Axiom-History-Query-Id")
        result.savedQueryID = query_id

        return result

    def _prepare_query_options(self, opts: QueryOptions) -> Dict[str, object]:
        """
        Return the query options as a Dict, handles any renaming for key fields.

        Args:
            opts: Query options

        Returns:
            Dictionary of query parameters
        """
        if opts is None:
            return {}
        params = {}
        if opts.streamingDuration:
            params["streaming-duration"] = (
                opts.streamingDuration.seconds.__str__() + "s"
            )
        if opts.saveAsKind:
            params["saveAsKind"] = opts.saveAsKind.value

        params["nocache"] = opts.nocache.__str__()

        return params

    def _prepare_ingest_options(
        self, opts: Optional[IngestOptions]
    ) -> Dict[str, object]:
        """
        The query params for ingest api are expected in a format
        that couldn't be defined as a variable name because it has a dash.
        As a work around, we create the params dict manually.

        Args:
            opts: Ingest options

        Returns:
            Dictionary of ingest parameters
        """
        if opts is None:
            return {}

        params = {}
        if opts.timestamp_field:
            params["timestamp-field"] = opts.timestamp_field
        if opts.timestamp_format:
            params["timestamp-format"] = opts.timestamp_format
        if opts.CSV_delimiter:
            params["csv-delimiter"] = opts.CSV_delimiter

        return params

    def _prepare_apl_options(
        self, opts: Optional[AplOptions]
    ) -> Dict[str, object]:
        """
        Prepare the APL query options for the request.

        Args:
            opts: APL options

        Returns:
            Dictionary of APL parameters
        """
        from .client import AplResultFormat

        params: Dict[str, object] = {"format": AplResultFormat.Legacy.value}

        if opts is not None:
            if opts.format:
                params["format"] = opts.format.value
            if opts.limit is not None:
                params["request"] = {"limit": opts.limit}

        return params

    def _prepare_apl_payload(
        self, apl: str, opts: Optional[AplOptions]
    ) -> Dict[str, object]:
        """
        Prepare the APL query payload for the request.

        Args:
            apl: APL query string
            opts: APL options

        Returns:
            Dictionary to be serialized as JSON payload
        """
        params = {}
        params["apl"] = apl

        if opts is not None:
            if opts.start_time is not None:
                params["startTime"] = opts.start_time
            if opts.end_time is not None:
                params["endTime"] = opts.end_time
            if opts.cursor is not None:
                params["cursor"] = opts.cursor
            if opts.includeCursor:
                params["includeCursor"] = opts.includeCursor

        return params
