from datetime import timedelta
from dataclasses import dataclass, field
from .query import QueryKind


@dataclass
class QueryOptions:
    # StreamingDuration of a query.
    streamingDuration: timedelta = field(default=None)
    # NoCache omits the query cache.
    nocache: bool = field(default=False)
    # SaveKind saves the query on the server with the given query kind. The ID
    # of the saved query is returned with the query result as part of the
    # response. `query.APL` is not a valid kind for this field.
    saveAsKind: QueryKind = field(default=QueryKind.ANALYTICS)
