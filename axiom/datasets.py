"""This package provides dataset models and methods as well as a DatasetClient"""
from typing import List, Dict
from enum import Enum
from dataclasses import dataclass, asdict, field
from datetime import datetime
from humps import decamelize
from requests import Session
from logging import Logger
import csv
import ujson
import gzip
import dacite
import ndjson


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
        self.logger.debug("request url", res.request.url)
        status_snake = decamelize(res.json())
        return dacite.from_dict(data_class=IngestStatus, data=status_snake)

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
        return dacite.from_dict(data_class=Dataset, data=decoded_response)

    def create(self, req: DatasetCreateRequest) -> Dataset:
        """Create a dataset with the given properties."""
        path = "datasets"
        res = self.session.post(path, data=ujson.dumps(asdict(req)))
        ds = dacite.from_dict(data_class=Dataset, data=res.json())
        self.logger.info(f"created new dataset: {ds.name}")
        return ds

    def get_list(self) -> List[Dataset]:
        """List all available datasets."""
        path = "datasets"
        res = self.session.get(path)

        datasets = []
        for record in res.json():
            ds = dacite.from_dict(data_class=Dataset, data=record)
            datasets.append(ds)

        return datasets

    def update(self, id: str, req: DatasetUpdateRequest) -> Dataset:
        """Update a dataset with the given properties."""
        path = "datasets/%s" % id
        res = self.session.put(path, data=ujson.dumps(asdict(req)))
        ds = dacite.from_dict(data_class=Dataset, data=res.json())
        self.logger.info(f"updated dataset({ds.name}) with new desc: {ds.description}")
        return ds

    def delete(self, id: str):
        """Deletes a dataset with the given id."""
        path = "datasets/%s" % id
        self.session.delete(path)

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
