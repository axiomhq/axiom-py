from dataclasses import dataclass, field as dataclass_field


@dataclass
class Aggregation:
    """Aggregation performed as part of a query."""

    op: str
    field: str = dataclass_field(default="")
    alias: str = dataclass_field(default="")
    argument: any = dataclass_field(default="")
