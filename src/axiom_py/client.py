"""Client provides an easy-to use client library to connect to Axiom."""

import atexit
import gzip
import ujson
import os

from enum import Enum
from humps import decamelize
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from requests_toolbelt.sessions import BaseUrlSession
from requests.adapters import HTTPAdapter, Retry
from .datasets import DatasetsClient
from .query import (
    QueryLegacy,
    QueryResult,
    QueryOptions,
    QueryLegacyResult,
    QueryKind,
)
from .annotations import AnnotationsClient
from .users import UsersClient
from .version import __version__
from .util import from_dict, handle_json_serialization, is_personal_token
from .tokens import TokensClient


AXIOM_URL = "https://api.axiom.co"


@dataclass
class IngestFailure:
    """The ingestion failure of a single event"""

    timestamp: datetime
    error: str


@dataclass
class IngestStatus:
    """The status after an event ingestion operation"""

    ingested: int
    failed: int
    failures: List[IngestFailure]
    processed_bytes: int
    blocks_created: int
    wal_length: int


@dataclass
class IngestOptions:
    """IngestOptions specifies the optional parameters for the Ingest and
    IngestEvents method of the Datasets service."""

    # timestamp field defines a custom field to extract the ingestion timestamp
    # from. Defaults to `_time`.
    timestamp_field: str = field(default="_time")
    # timestamp format defines a custom format for the TimestampField.
    # The reference time is `Mon Jan 2 15:04:05 -0700 MST 2006`, as specified
    # in https://pkg.go.dev/time/?tab=doc#Parse.
    timestamp_format: Optional[str] = field(default=None)
    # CSV delimiter is the delimiter that separates CSV fields. Only valid when
    # the content to be ingested is CSV formatted.
    CSV_delimiter: Optional[str] = field(default=None)


class AplResultFormat(Enum):
    """The result format of an APL query."""

    Legacy = "legacy"
    Tabular = "tabular"


class ContentType(Enum):
    """ContentType describes the content type of the data to ingest."""

    JSON = "application/json"
    NDJSON = "application/x-ndjson"
    CSV = "text/csv"


class ContentEncoding(Enum):
    """ContentEncoding describes the content encoding of the data to ingest."""

    IDENTITY = "1"
    GZIP = "gzip"


class WrongQueryKindException(Exception):
    pass


@dataclass
class AplOptions:
    """AplOptions specifies the optional parameters for the apl query method."""

    # Start time for the interval to query.
    start_time: Optional[datetime] = field(default=None)
    # End time for the interval to query.
    end_time: Optional[datetime] = field(default=None)
    # The result format.
    format: AplResultFormat = field(default=AplResultFormat.Legacy)
    # Cursor is the query cursor. It should be set to the Cursor returned with
    # a previous query result if it was partial.
    cursor: Optional[str] = field(default=None)
    # IncludeCursor will return the Cursor as part of the query result, if set
    # to true.
    includeCursor: bool = field(default=False)
    # The query limit.
    limit: Optional[int] = field(default=None)


class AxiomError(Exception):
    """This exception is raised on request errors."""

    status: int
    message: str

    @dataclass
    class Response:
        message: str
        error: Optional[str]

    def __init__(self, status: int, res: Response):
        message = res.error if res.error is not None else res.message
        super().__init__(f"API error {status}: {message}")

        self.status = status
        self.message = message


def raise_response_error(res):
    if res.status_code >= 400:
        try:
            error_res = from_dict(AxiomError.Response, res.json())
        except Exception:
            # Response is not in the Axiom JSON format, create generic error
            # message
            error_res = AxiomError.Response(message=res.reason, error=None)

        raise AxiomError(res.status_code, error_res)


class Client:  # pylint: disable=R0903
    """The client class allows you to connect to Axiom."""

    datasets: DatasetsClient
    users: UsersClient
    annotations: AnnotationsClient
    tokens: TokensClient
    is_closed: bool = False  # track if the client has been closed (for tests)
    before_shutdown_funcs: List[Callable] = []

    def __init__(
        self,
        token: Optional[str] = None,
        org_id: Optional[str] = None,
        url_base: Optional[str] = None,
    ):
        # fallback to env variables if token, org_id or url are not provided
        if token is None:
            token = os.getenv("AXIOM_TOKEN")
        if org_id is None:
            org_id = os.getenv("AXIOM_ORG_ID")
        if url_base is None:
            url_base = AXIOM_URL

        # set exponential retries
        retries = Retry(
            total=3, backoff_factor=2, status_forcelist=[500, 502, 503, 504]
        )

        self.session = BaseUrlSession(url_base.rstrip("/"))
        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        # hook on responses, raise error when response is not successfull
        self.session.hooks = {
            "response": lambda r, *args, **kwargs: raise_response_error(r)
        }
        self.session.headers.update(
            {
                "Authorization": "Bearer %s" % token,
                # set a default Content-Type header, can be overriden by requests.
                "Content-Type": "application/json",
                "User-Agent": f"axiom-py/{__version__}",
            }
        )

        # if there is an organization id passed,
        # set it in the header
        if org_id:
            self.session.headers.update({"X-Axiom-Org-Id": org_id})

        self.datasets = DatasetsClient(self.session)
        self.users = UsersClient(self.session, is_personal_token(token))
        self.annotations = AnnotationsClient(self.session)
        self.tokens = TokensClient(self.session)

        # wrap shutdown hook in a lambda passing in self as a ref
        atexit.register(self.shutdown_hook)

    def before_shutdown(self, func: Callable):
        self.before_shutdown_funcs.append(func)

    def shutdown_hook(self):
        for func in self.before_shutdown_funcs:
            func()
        self.session.close()
        self.is_closed = True

    def ingest(
        self,
        dataset: str,
        payload: bytes,
        contentType: ContentType,
        enc: ContentEncoding,
        opts: Optional[IngestOptions] = None,
    ) -> IngestStatus:
        """
        Ingest the payload into the named dataset and returns the status.

        See https://axiom.co/docs/restapi/endpoints/ingestIntoDataset
        """
        path = "/v1/datasets/%s/ingest" % dataset

        # set headers
        headers = {
            "Content-Type": contentType.value,
            "Content-Encoding": enc.value,
        }
        # prepare query params
        params = self._prepare_ingest_options(opts)

        # override the default header and set the value from the passed parameter
        res = self.session.post(
            path, data=payload, headers=headers, params=params
        )
        status_snake = decamelize(res.json())
        return from_dict(IngestStatus, status_snake)

    def ingest_events(
        self,
        dataset: str,
        events: List[dict],
        opts: Optional[IngestOptions] = None,
    ) -> IngestStatus:
        """
        Ingest the events into the named dataset and returns the status.

        See https://axiom.co/docs/restapi/endpoints/ingestIntoDataset
        """
        # encode request payload to NDJSON
        content = "\n".join(
            ujson.dumps(event, default=handle_json_serialization)
            for event in events
        ).encode("UTF-8")
        gzipped = gzip.compress(content)

        return self.ingest(
            dataset, gzipped, ContentType.NDJSON, ContentEncoding.GZIP, opts
        )

    def query_legacy(
        self, id: str, query: QueryLegacy, opts: QueryOptions
    ) -> QueryLegacyResult:
        """
        Executes the given structured query on the dataset identified by its id.

        See https://axiom.co/docs/restapi/endpoints/queryDataset
        """
        if not opts.saveAsKind or (opts.saveAsKind == QueryKind.APL):
            raise WrongQueryKindException(
                "invalid query kind %s: must be %s or %s"
                % (opts.saveAsKind, QueryKind.ANALYTICS, QueryKind.STREAM)
            )

        path = "/v1/datasets/%s/query" % id
        payload = ujson.dumps(asdict(query), default=handle_json_serialization)
        params = self._prepare_query_options(opts)
        res = self.session.post(path, data=payload, params=params)
        result = from_dict(QueryLegacyResult, res.json())
        query_id = res.headers.get("X-Axiom-History-Query-Id")
        result.savedQueryID = query_id
        return result

    def apl_query(
        self, apl: str, opts: Optional[AplOptions] = None
    ) -> QueryResult:
        """
        Executes the given apl query on the dataset identified by its id.

        See https://axiom.co/docs/restapi/endpoints/queryApl
        """
        return self.query(apl, opts)

    def query(
        self, apl: str, opts: Optional[AplOptions] = None
    ) -> QueryResult:
        """
        Executes the given apl query on the dataset identified by its id.

        See https://axiom.co/docs/restapi/endpoints/queryApl
        """
        path = "/v1/datasets/_apl"
        payload = ujson.dumps(
            self._prepare_apl_payload(apl, opts),
            default=handle_json_serialization,
        )
        params = self._prepare_apl_options(opts)
        res = self.session.post(path, data=payload, params=params)
        result = from_dict(QueryResult, res.json())
        query_id = res.headers.get("X-Axiom-History-Query-Id")
        result.savedQueryID = query_id

        return result

    def _prepare_query_options(self, opts: QueryOptions) -> Dict[str, object]:
        """returns the query options as a Dict, handles any renaming for key fields."""
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
        """the query params for ingest api are expected in a format
        that couldn't be defined as a variable name because it has a dash.
        As a work around, we create the params dict manually."""

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
        """Prepare the apl query options for the request."""
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
        """Prepare the apl query options for the request."""
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
