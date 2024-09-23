"""Logging contains the AxiomHandler and related methods to do with logging."""

import time
import atexit
from threading import Timer

from logging import Handler, NOTSET, getLogger, WARNING
from .client import Client


class AxiomHandler(Handler):
    """A logging handler that sends logs to Axiom."""

    client: Client
    dataset: str
    buffer: list
    interval: int
    last_run: float
    timer: Timer

    def __init__(self, client: Client, dataset: str, level=NOTSET, interval=1):
        super().__init__()
        # Set urllib3 logging level to warning, check:
        # https://github.com/axiomhq/axiom-py/issues/23
        # This is a temp solution that would stop requests library from
        # flooding the logs with debug messages
        getLogger("urllib3").setLevel(WARNING)
        self.client = client
        self.dataset = dataset
        self.buffer = []
        self.last_run = time.monotonic()
        self.interval = interval

        # We use a threading.Timer to make sure we flush every second, even
        # if no more logs are emitted.
        self.timer = Timer(self.interval, self.flush)

        # Register flush on exit,
        atexit.register(self.flush)

    def emit(self, record):
        """Emit sends a log to Axiom."""
        self.buffer.append(record.__dict__)
        if (
            len(self.buffer) >= 1000
            or time.monotonic() - self.last_run > self.interval
        ):
            self.flush()
        else:
            self.timer.cancel()
            self.timer = Timer(self.interval, self.flush)
            self.timer.start()

    def flush(self):
        """Flush sends all logs in the buffer to Axiom."""
        self.timer.cancel()
        self.last_run = time.monotonic()
        if len(self.buffer) == 0:
            return
        self.client.ingest_events(self.dataset, self.buffer)
        self.buffer = []
