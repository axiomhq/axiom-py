"""
Deprecation warnings for the legacy query surface.

These use FutureWarning rather than DeprecationWarning. Python's default
filter only shows a DeprecationWarning attributed to `__main__`, and an SDK
call almost always comes from a caller's own module, so DeprecationWarning
would warn nobody.
"""

import warnings

_GUIDE = "See https://github.com/axiomhq/axiom-py/blob/main/MIGRATING.md"


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


def warn_legacy_query_options(opts, stacklevel: int) -> None:
    """
    Emit whichever deprecations apply to a single query() call.

    `stacklevel` is how far above this frame the caller's own code sits.
    Compares the format by value so this module stays importable from
    client.py without a cycle.
    """
    if opts is not None and opts.format is not None:
        if opts.format.value == "legacy":
            warn_explicit_legacy_format(stacklevel + 1)
