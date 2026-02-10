"""
Async version of dashboard models and methods with AsyncDashboardsClient.
"""

import ujson
import httpx
from typing import List
from dataclasses import asdict

from .dashboards import (
    Dashboard,
    DashboardCreateRequest,
    DashboardUpdateRequest,
)
from .util import from_dict
from ._error_handling import check_response_error


class AsyncDashboardsClient:
    """AsyncDashboardsClient has async methods to manipulate dashboards."""

    client: httpx.AsyncClient

    def __init__(self, client: httpx.AsyncClient):
        """
        Initialize the async dashboards client.

        Args:
            client: httpx AsyncClient instance for making HTTP requests
        """
        self.client = client

    async def get(self, id: str) -> Dashboard:
        """
        Asynchronously get a dashboard by id.

        Args:
            id: Dashboard identifier

        Returns:
            Dashboard object

        See https://axiom.co/docs/restapi/endpoints/getDashboard
        """
        path = f"/v1/dashboards/{id}"
        response = await self.client.get(path)
        check_response_error(response.status_code, response.json())
        return from_dict(Dashboard, response.json())

    async def create(self, req: DashboardCreateRequest) -> Dashboard:
        """
        Asynchronously create a dashboard with the given properties.

        Args:
            req: Dashboard creation request

        Returns:
            Created Dashboard object

        See https://axiom.co/docs/restapi/endpoints/createDashboard
        """
        path = "/v1/dashboards"
        payload = ujson.dumps(asdict(req))
        response = await self.client.post(path, content=payload)
        check_response_error(response.status_code, response.json())
        return from_dict(Dashboard, response.json())

    async def list(self) -> List[Dashboard]:
        """
        Asynchronously list all dashboards.

        Returns:
            List of Dashboard objects

        See https://axiom.co/docs/restapi/endpoints/getDashboards
        """
        path = "/v1/dashboards"
        response = await self.client.get(path)
        check_response_error(response.status_code, response.json())

        dashboards = []
        for record in response.json():
            ds = from_dict(Dashboard, record)
            dashboards.append(ds)

        return dashboards

    async def update(self, id: str, req: DashboardUpdateRequest) -> Dashboard:
        """
        Asynchronously update a dashboard with the given properties.

        Args:
            id: Dashboard identifier
            req: Dashboard update request

        Returns:
            Updated Dashboard object

        See https://axiom.co/docs/restapi/endpoints/updateDashboard
        """
        path = f"/v1/dashboards/{id}"
        payload = ujson.dumps(asdict(req))
        response = await self.client.put(path, content=payload)
        check_response_error(response.status_code, response.json())
        return from_dict(Dashboard, response.json())

    async def delete(self, id: str):
        """
        Asynchronously delete a dashboard with the given id.

        Args:
            id: Dashboard identifier

        See https://axiom.co/docs/restapi/endpoints/deleteDashboard
        """
        path = f"/v1/dashboards/{id}"
        response = await self.client.delete(path)
        check_response_error(response.status_code, response.json())
