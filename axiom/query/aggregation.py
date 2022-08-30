from enum import Enum
from dataclasses import dataclass, field as dataclass_field


class AggregationOperation(Enum):
    # Works with all types, field should be `*`.
    COUNT = "count"
    COUNTIF = "countif"
    COUNT_DISTINCT = "distinct"
    COUNTDISTINCTIF = "distinctif"
    MAKE_SET = "makeset"
    MAKE_SET_IF = "makesetif"

    # Only works for numbers.
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    TOPK = "topk"
    PERCENTILES = "percentiles"
    HISTOGRAM = "histogram"
    STDEV = "stdev"
    VARIANCE = "variance"
    ARGMIN = "argmin"
    ARGMAX = "argmax"


@dataclass
class Aggregation:
    """Aggregation performed as part of a query."""

    op: AggregationOperation
    field: str = dataclass_field(default="")
    alias: str = dataclass_field(default="")
    argument: any = dataclass_field(default="")
