"""Tests for the logging Handler."""

import logging
import os
import time
import unittest
import uuid

import pytest

from axiom_py import Client
from axiom_py.logging import AxiomHandler

from .helpers import get_random_name


class _RecordingClient:
    """Stands in for Client. Records what the handler tries to send."""

    def __init__(self):
        self.batches = []

    def before_shutdown(self, func):
        pass

    def ingest_events(self, dataset, events):
        self.batches.append(list(events))


class _FakeTimer:
    """
    Replaces threading.Timer so the scheduled flush fires on demand.

    A fake clock cannot drive a real Timer: it blocks in C on a lock with
    an OS timeout, so nothing in Python can advance it.
    """

    def __init__(self, interval, function):
        self.interval = interval
        self.function = function
        self.started = False
        self.cancelled = False

    def start(self):
        self.started = True

    def cancel(self):
        self.cancelled = True

    def fire(self):
        self.function()


class _Clock:
    def __init__(self):
        self.now = 1000.0

    def monotonic(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture
def handler(monkeypatch):
    """An AxiomHandler with the clock and the timer under test control."""
    import axiom_py.logging as module

    clock = _Clock()
    timers = []

    def make_timer(interval, function):
        timer = _FakeTimer(interval, function)
        timers.append(timer)
        return timer

    monkeypatch.setattr(module, "time", clock)
    monkeypatch.setattr(module, "Timer", make_timer)

    client = _RecordingClient()
    h = AxiomHandler(client, "ds", interval=1)
    h.clock = clock
    h.timers = timers
    h.recorded = client
    return h


def _record(msg="hello"):
    return logging.LogRecord(
        "t", logging.WARNING, __file__, 1, msg, None, None
    )


def test_record_stays_buffered_before_the_interval(handler):
    handler.emit(_record())

    assert handler.recorded.batches == []
    assert len(handler.buffer) == 1


def test_flush_sends_the_buffer_once(handler):
    handler.emit(_record())

    handler.flush()
    handler.flush()

    assert len(handler.recorded.batches) == 1
    assert len(handler.recorded.batches[0]) == 1
    assert handler.buffer == []


def test_emit_flushes_once_the_interval_has_passed(handler):
    handler.emit(_record("first"))
    assert handler.recorded.batches == []

    handler.clock.advance(1.5)
    handler.emit(_record("second"))

    assert len(handler.recorded.batches) == 1
    assert len(handler.recorded.batches[0]) == 2


def test_a_full_buffer_flushes_without_waiting(handler):
    for i in range(999):
        handler.emit(_record(f"m{i}"))
    assert handler.recorded.batches == []

    handler.emit(_record("m999"))

    assert len(handler.recorded.batches) == 1
    assert len(handler.recorded.batches[0]) == 1000


def test_emit_replaces_the_pending_timer(handler):
    handler.emit(_record("first"))
    first = handler.timers[-1]

    handler.emit(_record("second"))

    assert first.cancelled
    assert handler.timers[-1] is not first
    assert handler.timers[-1].started


def test_the_timer_flushes_without_another_emit(handler):
    handler.emit(_record())
    assert handler.recorded.batches == []

    handler.timers[-1].fire()

    assert len(handler.recorded.batches) == 1


class TestLoggerIntegration(unittest.TestCase):
    def test_a_logged_event_reaches_the_dataset(self):
        """
        The only part that needs the network: an emitted record survives
        ingestion and comes back from a query.

        Uses its own logger rather than the root logger. On the root
        logger any other thread's records enter this handler, which can
        itself trigger a flush and restart the timer.
        """
        client = Client(
            token=os.getenv("AXIOM_TOKEN"),
            org_id=os.getenv("AXIOM_ORG_ID"),
            url=os.getenv("AXIOM_URL"),
        )
        dataset_name = get_random_name()
        marker = uuid.uuid4().hex
        client.datasets.create(dataset_name, "axiom-py logger test")

        axiom_handler = AxiomHandler(client, dataset_name, interval=1.0)
        logger = logging.getLogger(f"axiom-py-test-{marker}")
        logger.addHandler(axiom_handler)
        logger.propagate = False
        logger.setLevel(logging.WARNING)

        try:
            logger.warning(marker)
            axiom_handler.flush()

            apl = f"['{dataset_name}'] | where msg == '{marker}'"
            deadline = time.monotonic() + 30
            rows = 0
            while time.monotonic() < deadline:
                rows = client.apl_query(apl).status.rowsMatched
                if rows >= 1:
                    break
                time.sleep(0.5)

            self.assertGreaterEqual(
                rows, 1, f"event {marker} never arrived in {dataset_name}"
            )
        finally:
            logger.removeHandler(axiom_handler)
            axiom_handler.timer.cancel()
            client.datasets.delete(dataset_name)
