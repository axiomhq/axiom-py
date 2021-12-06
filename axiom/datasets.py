"""This package provides dataset models and methods as well as a DatasetClient"""
import csv
import gzip
import ujson
import ndjson
from enum import Enum
from logging import Logger
from humps import decamelize
from requests import Session
from typing import List, Dict
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta, timezone

from .util import Util
from .query import Query, QueryOptions, QueryKind
from .query.result import QueryResult


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
    timestamp_format: str = field(default=None)
    # CSV delimiter is the delimiter that separates CSV fields. Only valid when
    # the content to be ingested is CSV formatted.
    CSV_delimiter: str = field(default=None)


@dataclass
class Dataset:
    """Represents an Axiom dataset"""

    id: str = field(init=False)
    name: str
    description: str
    who: str
    created: str


@dataclass
class DatasetCreateRequest:
    """Request used to create a dataset"""

    name: str
    description: str


@dataclass
class DatasetUpdateRequest:
    """Request used to update a dataset"""

    description: str


class ContentType(Enum):
    """ContentType describes the content type of the data to ingest."""

    JSON = "application/json"
    NDJSON = "application/x-ndjson"
    CSV = "text/csv"


class ContentEncoding(Enum):
    """ContentEncoding describes the content encoding of the data to ingest."""

    IDENTITY = "1"
    GZIP = "gzip"


@dataclass
class TrimRequest:
    """MaxDuration marks the oldest timestamp an event can have before getting deleted."""

    maxDuration: str


@dataclass
class TrimResult:
    """TrimResult is the result of a trim operation."""

    # the amount of blocks deleted by the trim operation.
    numDeleted: int


@dataclass
class Field:
    """Represents a field of an Axiom dataset."""

    name: str
    description: str
    type: str
    unit: str
    hidden: bool


class WrongQueryKindException(Exception):
    pass


@dataclass
class DatasetInfo:
    """Represents the details of the information stored inside an Axiom dataset."""

    name: str
    numBlocks: int
    numEvents: int
    numFields: int
    inputBytes: int
    inputBytesHuman: str
    compressedBytes: int
    compressedBytesHuman: str
    minTime: str
    maxTime: str
    fields: List[Field]
    who: str
    created: str


@dataclass
class History:
    """represents a query stored inside the query history."""

    id: str = field(init=False)
    kind: QueryKind
    dataset: str
    who: str
    query: Query
    created: datetime


class DatasetsClient:  # pylint: disable=R0903
    """DatasetsClient has methods to manipulate datasets."""

    session: Session

    def __init__(self, session: Session, logger: Logger):
        self.session = session
        self.logger = logger

    def ingest(
        self,
        dataset: str,
        payload: bytes,
        contentType: ContentType,
        enc: ContentEncoding,
        opts: IngestOptions = None,
    ) -> IngestStatus:
        """Ingest the events into the named dataset and returns the status."""
        path = "datasets/%s/ingest" % dataset

        # check if passed content type and encoding are correct
        if not contentType:
            raise ValueError("unknown content-type, choose one of json,x-ndjson or csv")

        if not enc:
            raise ValueError("unknown content-encoding")

        # set headers
        headers = {"Content-Type": contentType.value, "Content-Encoding": enc.value}
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
        opts: IngestOptions = None,
    ) -> IngestStatus:
        """Ingest the events into the named dataset and returns the status."""
        path = "datasets/%s/ingest" % dataset

        # encode request payload to NDJSON
        content = ndjson.dumps(events).encode("UTF-8")
        gzipped = gzip.compress(content)

        return self.ingest(dataset, gzipped, ContentType.NDJSON, ContentEncoding.GZIP)

    def get(self, id: str) -> Dataset:
        """Get a dataset by id."""
        path = "datasets/%s" % id
        res = self.session.get(path)
        decoded_response = res.json()
        return Util.from_dict(Dataset, decoded_response)

    def create(self, req: DatasetCreateRequest) -> Dataset:
        """Create a dataset with the given properties."""
        path = "datasets"
        res = self.session.post(path, data=ujson.dumps(asdict(req)))
        ds = Util.from_dict(Dataset, res.json())
        self.logger.info(f"created new dataset: {ds.name}")
        return ds

    def get_list(self) -> List[Dataset]:
        """List all available datasets."""
        path = "datasets"
        res = self.session.get(path)

        datasets = []
        for record in res.json():
            ds = Util.from_dict(Dataset, record)
            datasets.append(ds)

        return datasets

    def update(self, id: str, req: DatasetUpdateRequest) -> Dataset:
        """Update a dataset with the given properties."""
        path = "datasets/%s" % id
        res = self.session.put(path, data=ujson.dumps(asdict(req)))
        ds = Util.from_dict(Dataset, res.json())
        self.logger.info(f"updated dataset({ds.name}) with new desc: {ds.description}")
        return ds

    def delete(self, id: str):
        """Deletes a dataset with the given id."""
        path = "datasets/%s" % id
        self.session.delete(path)

    def query(self, id: str, query: Query, opts: QueryOptions) -> QueryResult:
        """Executes the given query on the dataset identified by its id."""
        if not opts.saveAsKind or (opts.saveAsKind == QueryKind.APL):
            raise WrongQueryKindException(
                "invalid query kind %s: must be %s or %s"
                % (opts.saveAsKind, QueryKind.ANALYTICS, QueryKind.STREAM)
            )

        path = "datasets/%s/query" % id
        payload = ujson.dumps(asdict(query), default=Util.handle_json_serialization)
        self.logger.debug("sending query %s" % payload)
        params = self._prepare_query_options(opts)
        res = self.session.post(path, data=payload, params=params)
        result = Util.from_dict(QueryResult, res.json())
        self.logger.debug(f"query result: {result}")
        query_id = res.headers.get("X-Axiom-History-Query-Id")
        self.logger.info(f"received query result with query_id: {query_id}")
        result.savedQueryID = query_id
        return result

    def info(self, id: str) -> DatasetInfo:
        """Retrieves the information of the dataset identified by its id."""
        path = "datasets/%s/info" % id
        res = self.session.get(path)
        decoded_response = res.json()

        return Util.from_dict(DatasetInfo, decoded_response)

    def trim(self, id: str, maxDuration: timedelta) -> TrimResult:
        """
        Trim the dataset identified by its id to a given length. The max duration
        given will mark the oldest timestamp an event can have. Older ones will be
        deleted from the dataset.
        """
        path = "datasets/%s/trim" % id
        # prepare request payload and format masDuration to append time unit at the end, e.g `1s`
        req = TrimRequest(f"{maxDuration.seconds}s")
        res = self.session.post(path, data=ujson.dumps(asdict(req)))
        decoded_response = res.json()

        return Util.from_dict(TrimResult, decoded_response)

    def history(self, id: str) -> History:
        """
        History retrieves the query stored inside the query history dataset
        identified by its id.
        """
        path = "datasets/_history/%s" % id
        res = self.session.get(path)
        decoded_response = res.json()

        # return history
        history = Util.from_dict(History, decoded_response)
        return history

    def _prepare_ingest_options(self, opts: IngestOptions) -> Dict[str, any]:
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

    def _prepare_query_options(self, opts: QueryOptions) -> Dict[str, any]:
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
