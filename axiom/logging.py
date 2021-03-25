"""Logging contains the AxiomHandler and related methods to do with logging."""
from logging import Handler, NOTSET
from .client import Client


class AxiomHandler(Handler):
    """A logging handler that sends logs to an Axiom instance."""

    client: Client
    dataset: str

    def __init__(self, client: Client, dataset: str, level=NOTSET):
        Handler.__init__(self, level)
        self.client = client
        self.dataset = dataset

    def emit(self, record):
        # FIXME: Don't do an ingest call for every event
        self.client.datasets.ingest(self.dataset, [record.__dict__])
