"""Client provides an easy-to use client library to connect to your Axiom
instance or Axiom Cloud."""
from requests_toolbelt.sessions import BaseUrlSession

from .datasets import DatasetsClient


def raise_response_error(r):
    print(r.json())
    r.raise_for_status()


class Client:  # pylint: disable=R0903
    """The client class allows you to connect to your self-hosted Axiom
    instance or Axiom Cloud."""

    datasets: DatasetsClient

    def __init__(self, url_base: str, token: str, org_id: str = None):
        # Append /api/v1 to the url_base
        url_base = url_base.rstrip("/") + "/api/v1/"

        session = BaseUrlSession(url_base)
        # hook on responses, raise error when response is not successfull
        session.hooks = {"response": lambda r, *args, **kwargs: raise_response_error(r)}
        session.headers.update(
            {"Authorization": "Bearer %s" % token, "Content-Type": "application/json"}
        )

        # if there is and organization id passed,
        # set it in the header
        if org_id:
            session.headers.update({"X-Axiom-Org-Id": org_id})

        self.datasets = DatasetsClient(session)
