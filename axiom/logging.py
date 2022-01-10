"""Logging contains the AxiomHandler and related methods to do with logging."""
from logging import Handler, NOTSET, getLogger, WARNING
from .client import Client


class AxiomHandler(Handler):
    """A logging handler that sends logs to an Axiom instance."""

    client: Client
    dataset: str

    def __init__(self, client: Client, dataset: str, level=NOTSET):
        Handler.__init__(self, level)
        # set urllib3 logging level to warning, check:
        # https://github.com/axiomhq/axiom-py/issues/23
        # This is a temp solution that would stop requests
        # library from flooding the logs with debug messages
        getLogger("urllib3").setLevel(WARNING)
        self.client = client
        self.dataset = dataset

    def emit(self, record):
        # FIXME: Don't do an ingest call for every event
        self.client.datasets.ingest_events(self.dataset, [record.__dict__])
