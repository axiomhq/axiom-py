"""Client provides an easy-to use client library to connect to your Axiom
instance or Axiom Cloud."""
import ndjson
import dacite
import ujson
from logging import getLogger
from dataclasses import dataclass, field
from requests_toolbelt.sessions import BaseUrlSession
from requests_toolbelt.utils.dump import dump_response, dump_all
from .datasets import DatasetsClient, ContentType


@dataclass
class Error:
    status: int = field(default=None)
    message: str = field(default=None)
    error: str = field(default=None)


def raise_response_error(r):
    if r.status_code >= 400:
        print("==== Response Debugging ====")
        print("##Request Headers", r.request.headers)

        # extract content type
        ct = r.headers["content-type"].split(";")[0]
        if ct == ContentType.JSON.value:
            dump = dump_response(r)
            print(dump)
            print("##Response:", dump.decode("UTF-8"))
            err = dacite.from_dict(data_class=Error, data=r.json())
            print(err)
        elif ct == ContentType.NDJSON.value:
            decoded = ndjson.loads(r.text)
            print("##Response:", decoded)

        r.raise_for_status()
        # TODO: Decode JSON https://github.com/axiomhq/axiom-go/blob/610cfbd235d3df17f96a4bb156c50385cfbd9edd/axiom/error.go#L35-L50


class Client:  # pylint: disable=R0903
    """The client class allows you to connect to your self-hosted Axiom
    instance or Axiom Cloud."""

    datasets: DatasetsClient

    def __init__(self, url_base: str, token: str, org_id: str = None):
        # Append /api/v1 to the url_base
        url_base = url_base.rstrip("/") + "/api/v1/"

        logger = getLogger()
        session = BaseUrlSession(url_base)
        # hook on responses, raise error when response is not successfull
        session.hooks = {"response": lambda r, *args, **kwargs: raise_response_error(r)}
        session.headers.update(
            {
                "Authorization": "Bearer %s" % token,
                # set a default Content-Type header, can be overriden by requests.
                "Content-Type": "application/json",
            }
        )

        # if there is and organization id passed,
        # set it in the header
        if org_id:
            logger.info("found organization id: %s" % org_id)
            session.headers.update({"X-Axiom-Org-Id": org_id})

        self.datasets = DatasetsClient(session, logger)
