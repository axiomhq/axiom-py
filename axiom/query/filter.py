from enum import Enum
from typing import List
from dataclasses import dataclass, field as dataclass_field


class FilterOperation(Enum):
    """A FilterOperatuib can be applied on queries to filter based on different conditions."""

    EMPTY = ""
    AND = "and"
    OR = "or"
    NOT = "not"

    # Works for strings and numbers.
    EQUAL = "=="
    NOT_EQUAL = "!="
    EXISTS = "exists"
    NOT_EXISTS = "not-exists"

    # Only works for numbers.
    GREATER_THAN = ">"
    GREATER_THAN_EQUAL = ">="
    LESS_THAN = "<"
    LESS_THAN_EQUAL = "<="

    # Only works for strings.
    STARTS_WITH = "starts-with"
    NOT_STARTS_WITH = "not-starts-with"
    ENDS_WITH = "ends-with"
    NOT_ENDS_WITH = "not-ends-with"
    REGEXP = "regexp"
    NOT_REGEXP = "not-regexp"

    # Works for strings and arrays.
    CONTAINS = "contains"
    NOT_CONTAINS = "not-contains"


@dataclass
class BaseFilter:
    op: FilterOperation
    field: str
    value: any
    caseSensitive: bool = dataclass_field(default=False)


@dataclass
class Filter(BaseFilter):
    children: List[BaseFilter] = dataclass_field(default=lambda: [])
