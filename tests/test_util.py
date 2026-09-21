"""Serialization helpers."""

from datetime import datetime, timedelta, timezone

from axiom_py.util import handle_json_serialization

MICROS = 624703


def test_naive_datetime_serializes_as_utc():
    value = datetime(2026, 9, 7, 10, 5, 4, MICROS)

    assert handle_json_serialization(value) == "2026-09-07T10:05:04.624703Z"


def test_aware_datetime_serializes_as_utc():
    """
    isoformat() + "Z" produced "...+00:00Z", which the API rejects with
    `parsing time ...: extra text: "Z"`.
    """
    value = datetime(2026, 9, 7, 10, 5, 4, MICROS, tzinfo=timezone.utc)

    assert handle_json_serialization(value) == "2026-09-07T10:05:04.624703Z"


def test_offset_datetime_is_converted_to_utc():
    value = datetime(2026, 9, 7, 12, 5, 4, tzinfo=timezone(timedelta(hours=2)))

    assert handle_json_serialization(value) == "2026-09-07T10:05:04.000000Z"


def test_timedelta_serializes_as_seconds():
    assert handle_json_serialization(timedelta(seconds=30)) == "30s"
