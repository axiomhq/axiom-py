"""This package provides dashboard models and methods as well as a DashboardsClient"""

import ujson
from requests import Session
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict, field
from .util import from_dict


@dataclass
class Dashboard:
    """Represents an Axiom dashboard"""

    id: str = field(init=False)
    name: str
    owner: str
    refreshTime: int
    schemaVersion: int
    timeWindowStart: str
    timeWindowEnd: str
    charts: Optional[Dict] = None
    layout: Optional[Dict] = None
    description: Optional[str] = None
    datasets: Optional[List[str]] = None
    against: Optional[str] = None
    againstTimestamp: Optional[str] = None
    overrides: Optional[Dict] = None
    version: Optional[str] = None
    createdAt: Optional[str] = None
    createdBy: Optional[str] = None
    updatedAt: Optional[str] = None
    updatedBy: Optional[str] = None


@dataclass
class DashboardCreateRequest:
    """Request used to create a dashboard"""

    name: str
    owner: str
    refreshTime: int
    schemaVersion: int
    timeWindowStart: str
    timeWindowEnd: str
    charts: Optional[Dict] = None
    layout: Optional[Dict] = None
    description: Optional[str] = None
    datasets: Optional[List[str]] = None
    against: Optional[str] = None
    againstTimestamp: Optional[str] = None
    overrides: Optional[Dict] = None


@dataclass
class DashboardUpdateRequest:
    """Request used to update a dashboard"""

    name: str
    owner: str
    refreshTime: int
    schemaVersion: int
    timeWindowStart: str
    timeWindowEnd: str
    charts: Optional[Dict] = None
    layout: Optional[Dict] = None
    description: Optional[str] = None
    datasets: Optional[List[str]] = None
    against: Optional[str] = None
    againstTimestamp: Optional[str] = None
    overrides: Optional[Dict] = None
    version: Optional[str] = None


class DashboardsClient:  # pylint: disable=R0903
    """DashboardsClient has methods to manipulate dashboards."""

    session: Session

    def __init__(self, session: Session):
        self.session = session

    def get(self, id: str) -> Dashboard:
        """
        Get a dashboard by id.

        See https://axiom.co/docs/restapi/endpoints/getDashboard
        """
        path = "/v1/dashboards/%s" % id
        res = self.session.get(path)
        decoded_response = res.json()
        return from_dict(Dashboard, decoded_response)

    def create(self, req: DashboardCreateRequest) -> Dashboard:
        """
        Create a dashboard with the given properties.

        See https://axiom.co/docs/restapi/endpoints/createDashboard
        """
        path = "/v1/dashboards"
        res = self.session.post(path, data=ujson.dumps(asdict(req)))
        dashboard = from_dict(Dashboard, res.json())
        return dashboard

    def list(self) -> List[Dashboard]:
        """
        List all dashboards.

        See https://axiom.co/docs/restapi/endpoints/getDashboards
        """
        path = "/v1/dashboards"
        res = self.session.get(path)

        dashboards = []
        for record in res.json():
            ds = from_dict(Dashboard, record)
            dashboards.append(ds)

        return dashboards

    def update(self, id: str, req: DashboardUpdateRequest) -> Dashboard:
        """
        Update a dashboard with the given properties.

        See https://axiom.co/docs/restapi/endpoints/updateDashboard
        """
        path = "/v1/dashboards/%s" % id
        res = self.session.put(path, data=ujson.dumps(asdict(req)))
        dashboard = from_dict(Dashboard, res.json())
        return dashboard

    def delete(self, id: str):
        """
        Deletes a dashboard with the given id.

        See https://axiom.co/docs/restapi/endpoints/deleteDashboard
        """
        path = "/v1/dashboards/%s" % id
        self.session.delete(path)
