import dacite
import iso8601
from enum import Enum
from uuid import UUID
from typing import Type, TypeVar
from datetime import datetime, timedelta

from .query import QueryKind
from .query.result import MessagePriority
from .query.filter import FilterOperation


T = TypeVar("T")


def _convert_string_to_datetime(val: str) -> datetime:
    d = iso8601.parse_date(val)
    return d


def _convert_string_to_timedelta(val: str) -> timedelta:
    if val == "0":
        return timedelta(seconds=0)

    exp = "^([0-9]?)([a-z])$"
    import re

    found = re.search(exp, val)
    if not found:
        raise Exception(f"failed to parse timedelta field from value {val}")

    v = int(found.groups()[0])
    unit = found.groups()[1]

    if unit == "s":
        return timedelta(seconds=v)
    elif unit == "m":
        return timedelta(minutes=v)
    elif unit == "h":
        return timedelta(hours=v)
    elif unit == "d":
        return timedelta(days=v)
    else:
        raise Exception(f"failed to parse timedelta field from value {val}")


def from_dict(data_class: Type[T], data) -> T:
    cfg = dacite.Config(
        type_hooks={
            QueryKind: QueryKind,
            datetime: _convert_string_to_datetime,
            FilterOperation: FilterOperation,
            MessagePriority: MessagePriority,
            timedelta: _convert_string_to_timedelta,
        }
    )

    return dacite.from_dict(data_class=data_class, data=data, config=cfg)


def handle_json_serialization(obj):
    if isinstance(obj, datetime):
        return obj.isoformat("T") + "Z"
    elif isinstance(obj, timedelta):
        return str(obj.seconds) + "s"
    elif isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, UUID):
        return str(obj)


def is_personal_token(token: str):
    return token.startswith("xapt-")
