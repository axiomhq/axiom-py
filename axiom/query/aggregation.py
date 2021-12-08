from enum import Enum
from dataclasses import dataclass, field


class AggregationOperation(Enum):
    # Works with all types, field should be `*`.
    COUNT = "count"
    COUNT_DISTINCT = "distinct"

    # Only works for numbers.
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    TOPK = "topk"
    PERCENTILES = "percentiles"
    HISTOGRAM = "histogram"
    VARIANCE = "variance"
    STDEV = "stdev"


@dataclass
class Aggregation:
    """Aggregation performed as part of a query."""

    op: AggregationOperation
    field: str
    alias: str = field(default="")
    argument: any = field(default="")
