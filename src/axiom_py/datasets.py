"""
This package provides dataset models and methods as well as a DatasetClient
"""

import ujson
from requests import Session
from typing import List, Optional
from dataclasses import dataclass, asdict, field
from datetime import timedelta
from .util import from_dict


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
    region: Optional[str] = field(default=None)


@dataclass
class DatasetUpdateRequest:
    """Request used to update a dataset"""

    description: str


@dataclass
class TrimRequest:
    """
    MaxDuration marks the oldest timestamp an event can have before getting
    deleted.
    """

    maxDuration: str


class DatasetsClient:  # pylint: disable=R0903
    """DatasetsClient has methods to manipulate datasets."""

    session: Session

    def __init__(self, session: Session):
        self.session = session

    def get(self, id: str) -> Dataset:
        """
        Get a dataset by id.

        See https://axiom.co/docs/restapi/endpoints/getDataset
        """
        path = "/v1/datasets/%s" % id
        res = self.session.get(path)
        decoded_response = res.json()
        return from_dict(Dataset, decoded_response)

    def create(
        self,
        name: str,
        description: str = "",
        region: Optional[str] = None,
    ) -> Dataset:
        """
        Create a dataset with the given properties.

        Args:
            name: Name of the dataset.
            description: Description of the dataset.
            region: Optional region for the dataset (e.g., "eu-west-1").
                When set, the dataset is created in the specified region.

        See https://axiom.co/docs/restapi/endpoints/createDataset
        """
        path = "/v1/datasets"
        req = DatasetCreateRequest(
            name=name,
            description=description,
            region=region,
        )
        # Filter out None values from the request
        req_dict = {k: v for k, v in asdict(req).items() if v is not None}
        res = self.session.post(
            path,
            data=ujson.dumps(req_dict),
        )
        ds = from_dict(Dataset, res.json())
        return ds

    def get_list(self) -> List[Dataset]:
        """
        List all available datasets.

        See https://axiom.co/docs/restapi/endpoints/getDatasets
        """
        path = "/v1/datasets"
        res = self.session.get(path)

        datasets = []
        for record in res.json():
            ds = from_dict(Dataset, record)
            datasets.append(ds)

        return datasets

    def update(self, id: str, new_description: str) -> Dataset:
        """
        Update a dataset with the given properties.

        See https://axiom.co/docs/restapi/endpoints/updateDataset
        """
        path = "/v1/datasets/%s" % id
        res = self.session.put(
            path,
            data=ujson.dumps(
                asdict(
                    DatasetUpdateRequest(
                        description=new_description,
                    )
                )
            ),
        )
        ds = from_dict(Dataset, res.json())
        return ds

    def delete(self, id: str):
        """
        Deletes a dataset with the given id.

        See https://axiom.co/docs/restapi/endpoints/deleteDataset
        """
        path = "/v1/datasets/%s" % id
        self.session.delete(path)

    def trim(self, id: str, maxDuration: timedelta):
        """
        Trim the dataset identified by its id to a given length. The max
        duration given will mark the oldest timestamp an event can have.
        Older ones will be deleted from the dataset.

        See https://axiom.co/docs/restapi/endpoints/trimDataset
        """
        path = "/v1/datasets/%s/trim" % id
        # prepare request payload and format masDuration to append time unit at
        # the end, e.g `1s`
        req = TrimRequest(f"{maxDuration.seconds}s")
        self.session.post(path, data=ujson.dumps(asdict(req)))
