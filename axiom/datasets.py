"""This package provides dataset models and methods as well as a DatasetClient"""
import ujson
from logging import Logger
from requests import Session
from typing import List, Dict
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from .util import Util


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


@dataclass
class TrimRequest:
    """MaxDuration marks the oldest timestamp an event can have before getting deleted."""

    maxDuration: str


@dataclass
class Field:
    """A field of a dataset"""

    name: str
    description: str
    type: str
    unit: str
    hidden: bool


@dataclass
class DatasetInfo:
    """Information and statistics stored inside a dataset"""

    name: str
    numBlocks: int
    numEvents: int
    numFields: int
    inputBytes: int
    inputBytesHuman: str
    compressedBytes: int
    compressedBytesHuman: str
    minTime: datetime
    maxTime: datetime
    fields: List[Field]
    who: str
    created: datetime


class DatasetsClient:  # pylint: disable=R0903
    """DatasetsClient has methods to manipulate datasets."""

    session: Session

    def __init__(self, session: Session, logger: Logger):
        self.session = session
        self.logger = logger

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

    def trim(self, id: str, maxDuration: timedelta):
        """
        Trim the dataset identified by its id to a given length. The max duration
        given will mark the oldest timestamp an event can have. Older ones will be
        deleted from the dataset.
        """
        path = "datasets/%s/trim" % id
        # prepare request payload and format masDuration to append time unit at the end, e.g `1s`
        req = TrimRequest(f"{maxDuration.seconds}s")
        self.session.post(path, data=ujson.dumps(asdict(req)))

    def info(self, id: str) -> DatasetInfo:
        """Returns the info about a dataset."""
        path = "datasets/%s/info" % id
        res = self.session.get(path)
        decoded_response = res.json()
        return Util.from_dict(DatasetInfo, decoded_response)
