from dataclasses import dataclass, field as dataclass_field
from typing import Any


@dataclass
class Aggregation:
    """Aggregation performed as part of a query."""

    op: str
    field: str = dataclass_field(default="")
    alias: str = dataclass_field(default="")
    argument: Any = dataclass_field(default="")
