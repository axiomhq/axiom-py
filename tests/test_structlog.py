"""Tests for the structlog Processor."""

import pytest

from axiom_py.structlog import AxiomProcessor


class _RecordingClient:
    """Stands in for Client. Records what the processor tries to send."""

    def __init__(self):
        self.batches = []
        self.shutdown_funcs = []

    def before_shutdown(self, func):
        self.shutdown_funcs.append(func)

    def ingest_events(self, dataset, events):
        self.batches.append(list(events))


class _FakeTimer:
    """Replaces threading.Timer so the scheduled flush fires on demand."""

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
def processor(monkeypatch):
    """An AxiomProcessor with the clock and the timer under test control."""
    import axiom_py.structlog as module

    clock = _Clock()
    timers = []

    def make_timer(interval, function):
        timer = _FakeTimer(interval, function)
        timers.append(timer)
        return timer

    monkeypatch.setattr(module, "time", clock)
    monkeypatch.setattr(module, "Timer", make_timer)

    client = _RecordingClient()
    p = AxiomProcessor(client, "ds", interval=1)
    p.clock = clock
    p.timers = timers
    p.recorded = client
    return p


def test_event_stays_buffered_before_the_interval(processor):
    processor(None, "info", {"event": "hello"})

    assert processor.recorded.batches == []
    assert len(processor.buffer) == 1


def test_flush_sends_the_buffer_once(processor):
    processor(None, "info", {"event": "hello"})

    processor.flush()
    processor.flush()

    assert len(processor.recorded.batches) == 1
    assert len(processor.recorded.batches[0]) == 1
    assert processor.buffer == []


def test_call_replaces_the_pending_timer(processor):
    processor(None, "info", {"event": "first"})
    first = processor.timers[-1]

    processor(None, "info", {"event": "second"})

    assert first.cancelled
    assert processor.timers[-1] is not first
    assert processor.timers[-1].started


def test_the_timer_flushes_without_another_event(processor):
    processor(None, "info", {"event": "hello"})
    assert processor.recorded.batches == []

    processor.timers[-1].fire()

    assert len(processor.recorded.batches) == 1
    assert processor.recorded.batches[0] == [{"event": "hello"}]
    assert processor.buffer == []


def test_shutdown_flushes_and_cancels_timer(processor):
    processor(None, "info", {"event": "hello"})
    timer = processor.timers[-1]

    for fn in processor.recorded.shutdown_funcs:
        fn()

    assert timer.cancelled
    assert len(processor.recorded.batches) == 1
    assert processor.buffer == []
