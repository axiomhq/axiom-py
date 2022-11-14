from enum import Enum
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from .aggregation import Aggregation
from .filter import Filter


class QueryKind(Enum):
    """represents kind of query"""

    ANALYTICS = "analytics"
    STREAM = "stream"
    APL = "apl"


@dataclass
class Order:
    """Order specifies the order a queries result will be in."""

    # Field to order on. Must be present in `GroupBy` or used by an
    # aggregation.
    field: str
    # Desc specifies if the field is ordered ascending or descending.
    desc: bool


@dataclass
class VirtualField:
    """
    A VirtualField is not part of a dataset and its value is derived from an
    expression. Aggregations, filters and orders can reference this field like
    any other field.
    """

    # Alias the virtual field is referenced by.
    alias: str
    # Expression which specifies the virtual fields value.
    expr: str


@dataclass
class Projection:
    """A Projection is a field that is projected to the query result."""

    # Field to project to the query result.
    field: str
    # Alias to reference the projected field by. Optional.
    alias: str


@dataclass
class QueryLegacy:
    """represents a query that gets executed on a dataset."""

    # start time of the query. Required.
    startTime: datetime
    # end time of the query. Required.
    endTime: datetime
    # resolution of the queries graph. Valid values are the queries time
    # range / 100 at maximum and / 1000 at minimum. Use zero value for
    # serve-side auto-detection.
    resolution: str = field(default="auto")
    # Aggregations performed as part of the query.
    aggregations: Optional[List[Aggregation]] = field(default_factory=lambda: [])
    # GroupBy is a list of field names to group the query result by. Only valid
    # when at least one aggregation is specified.
    groupBy: Optional[List[str]] = field(default_factory=lambda: [])
    # Filter applied on the queried results.
    filter: Optional[Filter] = field(default=None)
    # Order is a list of order rules that specify the order of the query
    # result.
    order: Optional[List[Order]] = field(default_factory=lambda: [])
    # Limit the amount of results returned from the query.
    limit: int = field(default=10)
    # VirtualFields is a list of virtual fields that can be referenced by
    # aggregations, filters and orders.
    virtualFields: Optional[List[VirtualField]] = field(default_factory=lambda: [])
    # Projections is a list of projections that can be referenced by
    # aggregations, filters and orders. Leaving it empty projects all available
    # fields to the query result.
    project: Optional[List[Projection]] = field(default_factory=lambda: [])
    # Cursor is the query cursor. It should be set to the Cursor returned with
    # a previous query result if it was partial.
    cursor: str = field(default=None)
    # IncludeCursor will return the Cursor as part of the query result, if set
    # to true.
    includeCursor: bool = field(default=False)
    # ContinuationToken is used to get more results of a previous query. It is
    # not valid for starred queries or otherwise stored queries.
    continuationToken: str = field(default=None)
