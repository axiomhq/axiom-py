"""This package provides dataset models and methods as well as a DatasetClient"""
from typing import List
from dataclasses import dataclass, asdict, field
from datetime import datetime
from humps import decamelize
from requests import Session
from logging import Logger
import ujson
import dacite


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


class DatasetsClient:  # pylint: disable=R0903
    """DatasetsClient has methods to manipulate datasets."""

    session: Session

    def __init__(self, session: Session, logger: Logger):
        self.session = session
        self.logger = logger

    def ingest(self, dataset: str, events: List[dict]) -> IngestStatus:
        """Ingest the events into the named dataset and returns the status."""
        path = "datasets/%s/ingest" % dataset
        # FIXME: Use ndjson
        res = self.session.post(path, data=ujson.dumps(events))
        status_snake = decamelize(res.json())
        return dacite.from_dict(data_class=IngestStatus, data=status_snake)

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
