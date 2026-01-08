"""
Async version of dataset models and methods with AsyncDatasetsClient.
"""

import ujson
import httpx
from typing import List
from dataclasses import asdict
from datetime import timedelta

from .datasets import Dataset, DatasetCreateRequest, DatasetUpdateRequest, TrimRequest
from .util import from_dict
from ._error_handling import check_response_error


class AsyncDatasetsClient:
    """AsyncDatasetsClient has async methods to manipulate datasets."""

    client: httpx.AsyncClient

    def __init__(self, client: httpx.AsyncClient):
        """
        Initialize the async datasets client.

        Args:
            client: httpx AsyncClient instance for making HTTP requests
        """
        self.client = client

    async def get(self, id: str) -> Dataset:
        """
        Asynchronously get a dataset by id.

        Args:
            id: Dataset identifier

        Returns:
            Dataset object

        See https://axiom.co/docs/restapi/endpoints/getDataset
        """
        path = f"/v1/datasets/{id}"
        response = await self.client.get(path)
        check_response_error(response.status_code, response.json())
        return from_dict(Dataset, response.json())

    async def create(self, name: str, description: str = "") -> Dataset:
        """
        Asynchronously create a dataset with the given properties.

        Args:
            name: Dataset name
            description: Optional dataset description

        Returns:
            Created Dataset object

        See https://axiom.co/docs/restapi/endpoints/createDataset
        """
        path = "/v1/datasets"
        payload = ujson.dumps(
            asdict(
                DatasetCreateRequest(
                    name=name,
                    description=description,
                )
            )
        )
        response = await self.client.post(path, content=payload)
        check_response_error(response.status_code, response.json())
        return from_dict(Dataset, response.json())

    async def get_list(self) -> List[Dataset]:
        """
        Asynchronously list all available datasets.

        Returns:
            List of Dataset objects

        See https://axiom.co/docs/restapi/endpoints/getDatasets
        """
        path = "/v1/datasets"
        response = await self.client.get(path)
        check_response_error(response.status_code, response.json())

        datasets = []
        for record in response.json():
            ds = from_dict(Dataset, record)
            datasets.append(ds)

        return datasets

    async def update(self, id: str, new_description: str) -> Dataset:
        """
        Asynchronously update a dataset with the given properties.

        Args:
            id: Dataset identifier
            new_description: New description for the dataset

        Returns:
            Updated Dataset object

        See https://axiom.co/docs/restapi/endpoints/updateDataset
        """
        path = f"/v1/datasets/{id}"
        payload = ujson.dumps(
            asdict(
                DatasetUpdateRequest(
                    description=new_description,
                )
            )
        )
        response = await self.client.put(path, content=payload)
        check_response_error(response.status_code, response.json())
        return from_dict(Dataset, response.json())

    async def delete(self, id: str):
        """
        Asynchronously delete a dataset with the given id.

        Args:
            id: Dataset identifier

        See https://axiom.co/docs/restapi/endpoints/deleteDataset
        """
        path = f"/v1/datasets/{id}"
        response = await self.client.delete(path)
        check_response_error(response.status_code, response.json())

    async def trim(self, id: str, maxDuration: timedelta):
        """
        Asynchronously trim the dataset identified by its id to a given length.
        The max duration given will mark the oldest timestamp an event can have.
        Older ones will be deleted from the dataset.

        Args:
            id: Dataset identifier
            maxDuration: Maximum duration to keep data

        See https://axiom.co/docs/restapi/endpoints/trimDataset
        """
        path = f"/v1/datasets/{id}/trim"
        # prepare request payload and format maxDuration to append time unit
        req = TrimRequest(f"{maxDuration.seconds}s")
        payload = ujson.dumps(asdict(req))
        response = await self.client.post(path, content=payload)
        check_response_error(response.status_code, response.json())
