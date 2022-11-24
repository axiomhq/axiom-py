"""Logging contains the AxiomHandler and related methods to do with logging."""
import time
import atexit

from logging import Handler, NOTSET, getLogger, WARNING
from .client import Client


class AxiomHandler(Handler):
    """A logging handler that sends logs to Axiom."""

    client: Client
    dataset: str
    logcache: list
    interval: int
    last_run: float

    def __init__(self, client: Client, dataset: str, level=NOTSET, interval=3):
        Handler.__init__(self, level)
        # set urllib3 logging level to warning, check:
        # https://github.com/axiomhq/axiom-py/issues/23
        # This is a temp solution that would stop requests
        # library from flooding the logs with debug messages
        getLogger("urllib3").setLevel(WARNING)
        self.client = client
        self.dataset = dataset
        self.logcache = []
        self.last_run = time.time()
        self.interval = interval

        # register flush on exit,
        atexit.register(self.flush)

    def emit(self, record):
        """emit sends a log to Axiom."""
        self.logcache.append(record)
        if time.time() - self.last_run > self.interval:
            self.client.ingest_events(self.dataset, self.logcache)
            self.last_run = time.time()
            self.logcache = []
        else:
            return

    def flush(self):
        """flush sends all logs in the logcache to Axiom."""
        self.client.ingest_events(self.dataset, self.logcache)
        self.logcache = []
