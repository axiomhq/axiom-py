import dacite
import iso8601
from enum import Enum
from uuid import UUID
from typing import Type, TypeVar
from datetime import datetime, timedelta

from .query import QueryKind
from .query.aggregation import AggregationOperation
from .query.result import MessageCode, MessagePriority
from .query.filter import FilterOperation


T = TypeVar("T")


class Util:
    """A collection of helper methods."""

    @classmethod
    def from_dict(cls, data_class: Type[T], data) -> T:
        cfg = dacite.Config(
            type_hooks={
                QueryKind: QueryKind,
                datetime: cls.convert_string_to_datetime,
                AggregationOperation: AggregationOperation,
                FilterOperation: FilterOperation,
                MessageCode: MessageCode,
                MessagePriority: MessagePriority,
                timedelta: cls.convert_string_to_timedelta,
            }
        )

        return dacite.from_dict(data_class=data_class, data=data, config=cfg)

    @classmethod
    def convert_string_to_datetime(cls, val: str) -> datetime:
        d = iso8601.parse_date(val)
        return d

    @classmethod
    def convert_string_to_timedelta(cls, val: str) -> timedelta:
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

    @classmethod
    def handle_json_serialization(cls, obj):
        if isinstance(obj, datetime):
            return obj.isoformat("T") + "Z"
        elif isinstance(obj, timedelta):
            return str(obj.seconds) + "s"
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, UUID):
            return str(obj)
