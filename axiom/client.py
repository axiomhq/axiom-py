"""Client provides an easy-to use client library to connect to Axiom."""

import ndjson
import dacite
import gzip
import ujson
import rfc3339
import os
from .util import Util
from enum import Enum
from humps import decamelize
from typing import Optional, List, Dict, Any, Union
from logging import getLogger
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from requests_toolbelt.sessions import BaseUrlSession
from requests_toolbelt.utils.dump import dump_response
from requests.adapters import HTTPAdapter, Retry
from .datasets import DatasetsClient
from .query import (
    QueryLegacy,
    LegacyQueryResult,
    QueryOptions,
    QueryLegacyResult,
    QueryKind,
    TabularQueryResult,
)
from .users import UsersClient
from .__init__ import __version__
import concurrent.futures
import pandas as pd

AXIOM_URL = "https://api.axiom.co"


@dataclass
class Error:
    status: Optional[int] = field(default=None)
    message: Optional[str] = field(default=None)
    error: Optional[str] = field(default=None)


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

    start_time: Optional[datetime] = field(default=None)
    end_time: Optional[datetime] = field(default=None)
    no_cache: bool = field(default=False)
    save: bool = field(default=False)
    format: AplResultFormat = field(default=AplResultFormat.Legacy)
    include_cursor: bool = field(default=False)
    cursor: str = field(default=None)


def raise_response_error(r):
    if r.status_code >= 400:
        print("==== Response Debugging ====")
        print("##Request Headers", r.request.headers)

        # extract content type
        ct = r.headers["content-type"].split(";")[0]
        if ct == ContentType.JSON.value:
            dump = dump_response(r)
            print(dump)
            print("##Response:", dump.decode("UTF-8"))
            err = dacite.from_dict(data_class=Error, data=r.json())
            print(err)
        elif ct == ContentType.NDJSON.value:
            decoded = ndjson.loads(r.text)
            print("##Response:", decoded)

        r.raise_for_status()
        # TODO: Decode JSON https://github.com/axiomhq/axiom-go/blob/610cfbd235d3df17f96a4bb156c50385cfbd9edd/axiom/error.go#L35-L50


class Client:  # pylint: disable=R0903
    """The client class allows you to connect to Axiom."""

    datasets: DatasetsClient
    users: UsersClient

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
        # Append /v1 to the url_base
        url_base = url_base.rstrip("/") + "/v1/"

        self.logger = getLogger()
        self.session = BaseUrlSession(url_base)
        # set exponential retries
        retries = Retry(
            total=3, backoff_factor=2, status_forcelist=[500, 502, 503, 504]
        )
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
            self.logger.info("found organization id: %s" % org_id)
            self.session.headers.update({"X-Axiom-Org-Id": org_id})

        self.datasets = DatasetsClient(self.session, self.logger)
        self.users = UsersClient(self.session)

    def ingest(
        self,
        dataset: str,
        payload: bytes,
        content_type: ContentType,
        enc: ContentEncoding,
        opts: Optional[IngestOptions] = None,
    ) -> IngestStatus:
        """Ingest the events into the named dataset and returns the status."""
        path = "datasets/%s/ingest" % dataset

        # check if passed content type and encoding are correct
        if not content_type:
            raise ValueError("unknown content-type, choose one of json,x-ndjson or csv")

        if not enc:
            raise ValueError("unknown content-encoding")

        # set headers
        headers = {"Content-Type": content_type.value, "Content-Encoding": enc.value}
        # prepare query params
        params = self._prepare_ingest_options(opts)

        # override the default header and set the value from the passed parameter
        res = self.session.post(path, data=payload, headers=headers, params=params)
        status_snake = decamelize(res.json())
        return Util.from_dict(IngestStatus, status_snake)

    def ingest_events(
        self,
        dataset: str,
        events: List[dict],
        opts: Optional[IngestOptions] = None,
    ) -> IngestStatus:
        """Ingest the events into the named dataset and returns the status."""
        # encode request payload to NDJSON
        content = ndjson.dumps(events, default=Util.handle_json_serialization).encode(
            "UTF-8"
        )
        gzipped = gzip.compress(content)

        return self.ingest(
            dataset, gzipped, ContentType.NDJSON, ContentEncoding.GZIP, opts
        )

    def query_legacy(
        self, id: str, query: QueryLegacy, opts: QueryOptions
    ) -> QueryLegacyResult:
        """Executes the given query on the dataset identified by its id."""
        if not opts.save_as_kind or (opts.save_as_kind == QueryKind.APL):
            raise WrongQueryKindException(
                "invalid query kind %s: must be %s or %s"
                % (opts.save_as_kind, QueryKind.ANALYTICS, QueryKind.STREAM)
            )

        path = "datasets/%s/query" % id
        payload = ujson.dumps(asdict(query), default=Util.handle_json_serialization)
        self.logger.debug("sending query %s" % payload)
        params = self._prepare_query_options(opts)
        res = self.session.post(path, data=payload, params=params)
        result = Util.from_dict(QueryLegacyResult, res.json())
        self.logger.debug(f"query result: {result}")
        query_id = res.headers.get("X-Axiom-History-Query-Id")
        self.logger.info(f"received query result with query_id: {query_id}")
        result.query_id = query_id
        return result

    def apl_query(
        self, apl: str, opts: Optional[AplOptions] = None
    ) -> Union[LegacyQueryResult, TabularQueryResult]:
        """Executes the given apl query on the dataset identified by its id."""
        return self.query(apl, opts)

    def query(
        self, apl: str, opts: Optional[AplOptions] = None
    ) -> Union[LegacyQueryResult, TabularQueryResult]:
        """Executes the given apl query on the dataset identified by its id."""
        path = "datasets/_apl"
        payload = ujson.dumps(
            self._prepare_apl_payload(apl, opts),
            default=Util.handle_json_serialization,
        )
        self.logger.debug("sending query %s" % payload)
        params = self._prepare_apl_options(opts)
        res = self.session.post(path, data=payload, params=params)
        result = Util.from_dict(
            (
                LegacyQueryResult
                if opts is None or opts.format == AplResultFormat.Legacy
                else TabularQueryResult
            ),
            res.json(),
        )
        self.logger.debug(f"apl query result: {result}")
        query_id = res.headers.get("X-Axiom-History-Query-Id")
        self.logger.info(f"received query result with query_id: {query_id}")
        result.query_id = query_id
        return result

    def df(
        self,
        dataset_name: str,
        start_time: datetime,
        end_time: datetime,
        apl: str = "sort by _time asc",
    ):
        """
        Query the dataset for a specified time range and return the result as a DataFrame.

        Args:
            dataset_name (str): Name of the dataset to query.
            start_time (datetime): Start time of the query range.
            end_time (datetime): End time of the query range.
            apl (str, optional): APL query to execute. Defaults to '| sort by _time asc'. N.B. the apl *must*
                                 include a | sort by _time asc for this to function correctly.

        Returns:
            pd.DataFrame: Result of the query as a pandas DataFrame.
        """
        times = self._chunk_time_range(start_time, end_time)
        apl = f"['{dataset_name}'] | {apl}"

        def loop_query_until_finished(time_chunk: (datetime, datetime)):
            opts = AplOptions(
                no_cache=True,
                save=False,
                start_time=time_chunk[0],
                end_time=time_chunk[1],
                include_cursor=True,
                format=AplResultFormat.Tabular,
            )
            result = self.query(apl, opts)
            table = result.tables[0]
            df = pd.DataFrame()
            if len(table.columns) == 0 or len(table.columns[0]) == 0:
                return df

            while table.columns[0]:
                new_df = pd.DataFrame([c for c in table.columns]).T
                new_df.columns = [f.name for f in table.fields]
                df = pd.concat([df, new_df], ignore_index=True)
                if new_df.shape[0] != 1000:
                    break
                opts.cursor = result.status.max_cursor
                result = self.query(apl, opts)
                table = result.tables[0]
            df["_time"] = pd.to_datetime(df["_time"])
            df["_sysTime"] = pd.to_datetime(df["_sysTime"])
            return df

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(loop_query_until_finished, chunk) for chunk in times
            ]
            for future in concurrent.futures.as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    for f in futures:
                        f.cancel()
                    raise e

        return pd.concat(results)

    def _prepare_query_options(self, opts: QueryOptions) -> Dict[str, Any]:
        """returns the query options as a Dict, handles any renaming for key fields."""
        if opts is None:
            return {}
        params = {}
        if opts.streaming_duration:
            params["streaming-duration"] = (
                opts.streaming_duration.seconds.__str__() + "s"
            )
        if opts.save_as_kind:
            params["saveAsKind"] = opts.save_as_kind.value

        params["nocache"] = opts.nocache.__str__()

        return params

    def _prepare_ingest_options(self, opts: Optional[IngestOptions]) -> Dict[str, Any]:
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

    def _prepare_apl_options(self, opts: Optional[AplOptions]) -> Dict[str, Any]:
        """Prepare the apl query options for the request."""
        params = {}

        if opts is None:
            params["format"] = AplResultFormat.Legacy.value
            return params

        if opts.no_cache:
            params["nocache"] = opts.no_cache.__str__()
        if opts.save:
            params["save"] = opts.save
        if opts.format:
            params["format"] = opts.format.value

        return params

    def _prepare_apl_payload(
        self, apl: str, opts: Optional[AplOptions]
    ) -> Dict[str, Any]:
        """Prepare the apl query options for the request."""
        params = {}
        params["apl"] = apl

        if opts is not None:
            if opts.start_time:
                params["startTime"] = rfc3339.format(opts.start_time)
            if opts.end_time:
                params["endTime"] = rfc3339.format(opts.end_time)
            if opts.include_cursor:
                params["includeCursor"] = opts.include_cursor
            if opts.cursor:
                params["cursor"] = opts.cursor
        return params

    def _chunk_time_range(self, start_time: datetime, end_time: datetime):
        chunk_size = timedelta(minutes=1)
        max_chunks = 100

        total_chunks = int((end_time - start_time) / chunk_size)

        if total_chunks > max_chunks:
            chunk_size = timedelta(
                minutes=(end_time - start_time).total_seconds() / max_chunks / 60
            )
            total_chunks = max_chunks

        chunked_ranges = []

        for i in range(total_chunks):
            chunk_start = start_time + i * chunk_size
            chunk_end = min(chunk_start + chunk_size, end_time)
            chunked_ranges.append((chunk_start, chunk_end))

        return chunked_ranges
