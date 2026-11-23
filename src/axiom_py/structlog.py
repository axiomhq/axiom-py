"""Structlog contains the AxiomProcessor for structlog."""

from threading import Timer
from typing import List
import time
import atexit

from .client import Client


class AxiomProcessor:
    """A processor for sending structlogs to Axiom."""

    client: Client
    dataset: str
    buffer: List[object]
    interval: int
    last_run: float
    timer: Timer

    def __init__(self, client: Client, dataset: str, interval=1):
        self.client = client
        self.dataset = dataset
        self.buffer = []
        self.last_run = time.monotonic()
        self.interval = interval

        self.timer = Timer(self.interval, self.flush)

        def before_shutdown():
            self.flush()
            self.timer.cancel()

        if hasattr(client, "before_shutdown"):
            client.before_shutdown(before_shutdown)
        atexit.register(before_shutdown)

    def flush(self):
        self.last_run = time.monotonic()
        if len(self.buffer) == 0:
            return
        local_buffer, self.buffer = self.buffer, []
        self.client.ingest_events(self.dataset, local_buffer)

    def __call__(self, logger: object, method_name: str, event_dict: object):
        self.buffer.append(event_dict.copy())
        if (
            len(self.buffer) >= 1000
            or time.monotonic() - self.last_run > self.interval
        ):
            self.flush()

        self.timer.cancel()
        self.timer = Timer(self.interval, self.flush)
        self.timer.daemon = True
        self.timer.start()
        return event_dict
