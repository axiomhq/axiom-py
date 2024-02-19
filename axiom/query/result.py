from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

from .query import QueryLegacy


class MessageCode(Enum):
    """Message codes represents the code associated with the query."""

    UNKNOWN_MESSAGE_CODE = ""
    VIRTUAL_FIELD_FINALIZE_ERROR = "virtual_field_finalize_error"
    MISSING_COLUMN = "missing_column"
    LICENSE_LIMIT_FOR_QUERY_WARNING = "license_limit_for_query_warning"
    DEFAULT_LIMIT_WARNING = "default_limit_warning"


class MessagePriority(Enum):
    """Message priorities represents the priority of a message associated with a query."""

    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"


@dataclass
class Message:
    """a message associated with a query result."""

    # priority of the message.
    priority: MessagePriority
    # describes how often a message of this type was raised by the query.
    count: int
    # code of the message.
    code: MessageCode
    # a human readable text representation of the message.
    msg: str


@dataclass
class QueryStatus:
    """the status of a query result."""

    # the duration it took the query to execute.
    elapsed_time: int
    # the amount of blocks that have been examined by the query.
    blocks_examined: int
    # the amount of rows that have been examined by the query.
    rows_examined: int
    # the amount of rows that matched the query.
    rows_matched: int
    # the amount of groups returned by the query.
    num_groups: int
    # describes if the query result is a partial result.
    is_partial: bool
    # ContinuationToken is populated when isPartial is true and must be passed
    # to the next query request to retrieve the next result set.
    continuation_token: Optional[str] = field(default=None)
    # describes if the query result is estimated.
    is_estimate: Optional[bool] = field(default=None)
    # the timestamp of the oldest block examined.
    min_block_time: Optional[str] = field(default=None)
    # the timestamp of the newest block examined.
    max_block_time: Optional[str] = field(default=None)
    # messages associated with the query.
    messages: List[Message] = field(default_factory=lambda: [])
    # row id of the newest row, as seen server side.
    max_cursor: Optional[str] = field(default=None)
    # row id of the oldest row, as seen server side.
    min_cursor: Optional[str] = field(default=None)


@dataclass
class Entry:
    """Entry is an event that matched a query and is thus part of the result set."""

    # the time the event occurred. Matches SysTime if not specified
    # during ingestion.
    _time: str
    # the time the event was recorded on the server.
    _sysTime: str
    # the unique ID of the event row.
    _rowId: str
    # contains the raw data of the event (with filters and aggregations
    # applied).
    data: Dict[str, Any]


@dataclass
class EntryGroupAgg:
    """an aggregation which is part of a group of queried events."""

    # alias is the aggregations alias. If it wasn't specified at query time, it
    # is the uppercased string representation of the aggregation operation.
    value: Any
    op: str = field(default="")
    # value is the result value of the aggregation.


@dataclass
class EntryGroup:
    """a group of queried event."""

    # the unique id of the group.
    id: int
    # group maps the fieldnames to the unique values for the entry.
    group: Dict[str, Any]
    # aggregations of the group.
    aggregations: List[EntryGroupAgg]


@dataclass
class Interval:
    """the interval of queried time series."""

    # start_time of the interval.
    start_time: datetime
    # end_time of the interval.
    end_time: datetime
    # groups of the interval.
    groups: Optional[List[EntryGroup]]


@dataclass
class Timeseries:
    """Timeseries are queried time series."""

    # the intervals that build a time series.
    series: List[Interval]
    # totals of the time series.
    totals: Optional[List[EntryGroup]]


@dataclass
class QueryLegacyResult:
    """Result is the result of a query."""

    # Status of the query result.
    status: QueryStatus
    # Matches are the events that matched the query.
    matches: List[Entry]
    # Buckets are the time series buckets.
    buckets: Timeseries
    # query_id is the ID of the query that generated this result when it
    # was saved on the server. This is only set when the query was sent with
    # the `save_as_kind` option specified.
    query_id: Optional[str] = field(default=None)


@dataclass
class LegacyQueryResult:
    """Result is the result of apl query."""

    request: QueryLegacy
    # Status of the apl query result.
    status: QueryStatus
    # Matches are the events that matched the apl query.
    matches: List[Entry]
    # Buckets are the time series buckets.
    buckets: Timeseries
    # Dataset names are the datasets that were used in the apl query.
    dataset_names: List[str] = field(default_factory=lambda: [])
    # query_id is the ID of the apl query that generated this result when it
    # was saved on the server. This is only set when the apl query was sent with
    # the `save_as_kind` option specified.
    query_id: Optional[str] = field(default=None)


@dataclass
class Field:
    """
    Represents a field in a table, including its name and data type.

    Attributes:
        name (str): The name of the field.
        type (str): The data type of the field.
    """

    name: str
    type: str


@dataclass
class Source:
    """
    Represents the source of data for a table.

    Attributes:
        name (str): The name of the source.
    """

    name: str


@dataclass
class Order:
    """
    Specifies the ordering of rows in a table.

    Attributes:
        field (str): The name of the field to sort by.
        desc (bool): Specifies whether the sorting should be in descending order.
    """

    field: str
    desc: bool


@dataclass
class Range:
    """
    Defines a range of values for filtering data in a table based on a specific field.

    Attributes:
        field (str): The name of the field to filter by.
        start (str): The starting value of the range (inclusive).
        end (str): The ending value of the range (inclusive).
    """

    field: str
    start: str
    end: str


@dataclass
class Table:
    """
    Represents a table of data, including its structure and contents.

    Attributes:
        name (str): The name of the table.
        sources (List[Source]): A list of data sources for the table.
        fields (List[Field]): The fields (columns) in the table.
        order (List[Order]): The sorting order of rows in the table.
        range (Range): The range filter applied to the table.
        columns (List[List[Any]]): The data contained in the table, organized by columns.
        groups (List[Any]): Groups of aggregated data in the table (default is an empty list).
    """

    name: str
    sources: List[Source]
    fields: List[Field]
    order: List[Order]
    range: Range
    columns: List[List[Any]]
    groups: List[Any] = field(default_factory=list)


@dataclass
class Request:
    """
    Represents a request for querying data, including filters and parameters for the query.

    Attributes:
        start_time (str): The start time for the query range.
        end_time (str): The end time for the query range.
        resolution (str): The resolution of the aggregated data.
        aggregations (Optional[Any]): Specifies aggregation functions to be applied.
        group_by (Optional[Any]): Specifies the fields to group by in the aggregation.
        order (List[Order]): Specifies the ordering of the results.
        limit (int): The maximum number of rows to return.
        virtual_fields (Optional[Any]): Specifies virtual fields to be calculated.
        project (List[Dict[str, str]]): Specifies the fields to include in the result set.
        cursor (str): A cursor for pagination.
        include_cursor (bool): Indicates whether to include the cursor in the response.
    """

    start_time: str
    end_time: str
    resolution: str
    aggregations: Optional[Any]
    group_by: Optional[Any]
    order: List[Order]
    limit: int
    virtual_fields: Optional[Any]
    project: List[Dict[str, str]]
    cursor: str
    include_cursor: bool


@dataclass
class TabularQueryResult:
    """
    Represents the result of a tabular query, including the data format and status.

    Attributes:
        format (str): The format of the query result.
        status (QueryStatus): The status of the query execution.
        tables (List[Table]): The tables resulting from the query.
        request (Request): The request that generated this result.
        dataset_names (List[str]): The names of datasets included in the result.
        fields_meta_map (Dict[str, List[Any]]): Metadata for the fields in the result.
        query_id (Optional[str]): The ID of the saved query that generated this result, if applicable.
    """

    format: str
    status: QueryStatus
    tables: List[Table]
    request: Request
    # query_id is the ID of the query that generated this result when it
    # was saved on the server. This is only set when the query was sent with
    # the `save_as_kind` option specified.
    query_id: Optional[str] = field(default=None)
