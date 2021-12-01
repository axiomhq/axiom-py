from datetime import timedelta
from dataclasses import dataclass, field
from .query import QueryKind


@dataclass
class QueryOptions:
    # StreamingDuration of a query.
    streamingDuration: timedelta
    # NoCache omits the query cache.
    nocache: bool
    # SaveKind saves the query on the server with the given query kind. The ID
    # of the saved query is returned with the query result as part of the
    # response. `query.APL` is not a valid kind for this field.
    saveAsKind: QueryKind
