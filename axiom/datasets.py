"""This package provides dataset models and methods as well as a DatasetClient"""
from typing import List
from dataclasses import dataclass
from datetime import datetime
from humps import decamelize
from requests import Session
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


class DatasetsClient:  # pylint: disable=R0903
    """DatasetsClient has methods to manipulate datasets."""

    session: Session

    def __init__(self, session: Session):
        self.session = session

    def ingest(self, dataset: str, events: List[dict]) -> IngestStatus:
        """Ingest the events into the named dataset and returns the status."""
        path = "datasets/%s/ingest" % dataset
        # FIXME: Use ndjson
        res = self.session.post(
            path, data=ujson.dumps(events), headers={"Content-Type": "application/json"}
        )
        status_snake = decamelize(res.json())
        return dacite.from_dict(data_class=IngestStatus, data=status_snake)
