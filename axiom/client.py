"""Client provides an easy-to use client library to connect to your Axiom
instance or Axiom Cloud."""
from requests_toolbelt.sessions import BaseUrlSession

from .datasets import DatasetsClient


class Client:  # pylint: disable=R0903
    """The client class allows you to connect to your self-hosted Axiom
    instance or Axiom Cloud."""

    datasets: DatasetsClient

    def __init__(self, url_base: str, token: str):
        # Append /api/v1 to the url_base
        url_base = url_base.rstrip("/") + "/api/v1/"

        session = BaseUrlSession(url_base)
        session.headers.update({"Authorization": "Bearer " + token})

        self.datasets = DatasetsClient(session)
