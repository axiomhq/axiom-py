"""
Deprecation warnings for the legacy query surface.

These use FutureWarning rather than DeprecationWarning. Python's default
filter only shows a DeprecationWarning attributed to `__main__`, and an SDK
call almost always comes from a caller's own module, so DeprecationWarning
would warn nobody.
"""

import warnings

_GUIDE = "See https://github.com/axiomhq/axiom-py/blob/main/MIGRATING.md"


def warn_implicit_legacy_format(stacklevel: int) -> None:
    warnings.warn(
        "APL queries still default to the legacy result format. The default "
        "becomes tabular in 0.14.0 and the legacy format is removed in "
        "0.15.0. Pass AplOptions(format=AplResultFormat.Tabular) and read "
        f"rows with result.tables[0].events() to move now. {_GUIDE}",
        FutureWarning,
        stacklevel=stacklevel,
    )


def warn_explicit_legacy_format(stacklevel: int) -> None:
    warnings.warn(
        "AplResultFormat.Legacy is deprecated and is removed in 0.15.0, "
        "along with QueryResult.matches and QueryResult.buckets. Switch to "
        f"AplResultFormat.Tabular. {_GUIDE}",
        FutureWarning,
        stacklevel=stacklevel,
    )


def warn_query_legacy(stacklevel: int) -> None:
    warnings.warn(
        "query_legacy() and the QueryLegacy request types are deprecated "
        "and are removed in 0.15.0. Express the query in APL and call "
        f"query() instead. {_GUIDE}",
        FutureWarning,
        stacklevel=stacklevel,
    )


def warn_apl_limit(stacklevel: int) -> None:
    warnings.warn(
        "AplOptions.limit has never reached the server: it was serialized "
        "as an unknown query parameter and dropped. It is removed in "
        "0.14.0. Put `| limit N` in the APL query instead.",
        FutureWarning,
        stacklevel=stacklevel,
    )


def warn_legacy_query_options(opts, stacklevel: int) -> None:
    """
    Emit whichever deprecations apply to a single query() call.

    `stacklevel` is how far above this frame the caller's own code sits.
    Compares the format by value so this module stays importable from
    client.py without a cycle.
    """
    if opts is None or opts.format is None:
        warn_implicit_legacy_format(stacklevel + 1)
    elif opts.format.value == "legacy":
        warn_explicit_legacy_format(stacklevel + 1)

    if opts is not None and opts.limit is not None:
        warn_apl_limit(stacklevel + 1)
