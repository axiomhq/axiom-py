"""Structlog contains the AxiomProcessor for structlog."""

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

    def __init__(self, client: Client, dataset: str, interval=1):
        self.client = client
        self.dataset = dataset
        self.buffer = []
        self.last_run = time.monotonic()
        self.interval = interval

        atexit.register(self.flush)

    def flush(self):
        self.last_run = time.monotonic()
        if len(self.buffer) == 0:
            return
        self.client.ingest_events(self.dataset, self.buffer)
        self.buffer = []

    def __call__(self, logger: object, method_name: str, event_dict: object):
        self.buffer.append(event_dict.copy())
        if (
            len(self.buffer) >= 1000
            or time.monotonic() - self.last_run > self.interval
        ):
            self.flush()
        return event_dict
