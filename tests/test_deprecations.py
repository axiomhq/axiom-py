"""
The 0.13.0 runway.

The default is tabular as of 0.14.0. What remains deprecated warns once
before 0.15.0 removes it. The category is FutureWarning on purpose: Python's
default filter only surfaces a DeprecationWarning attributed to __main__,
and an SDK call comes from the caller's own module, so DeprecationWarning
would reach nobody.
"""

import warnings

import pytest
import responses

from axiom_py import AplOptions, AplResultFormat, Client
from axiom_py.query import QueryKind, QueryLegacy, QueryOptions

APL_URL = "http://localhost/v1/datasets/_apl"

RESULT = {
    "status": {
        "elapsedTime": 1,
        "blocksExamined": 0,
        "rowsExamined": 0,
        "rowsMatched": 0,
        "numGroups": 0,
        "isPartial": False,
    },
    "tables": [],
}


@pytest.fixture
def client():
    return Client(token="xaat-t", org_id="o", url="http://localhost")


@responses.activate
def test_implicit_default_is_tabular_and_silent(client):
    responses.add(responses.POST, APL_URL, json=RESULT, status=200)

    with warnings.catch_warnings():
        warnings.simplefilter("error", FutureWarning)
        client.query("['d'] | limit 1")

    assert responses.calls[0].request.params["format"] == "tabular"


@responses.activate
def test_explicit_legacy_warns(client):
    responses.add(responses.POST, APL_URL, json=RESULT, status=200)

    with pytest.warns(FutureWarning, match="AplResultFormat.Legacy"):
        client.query(
            "['d'] | limit 1",
            AplOptions(format=AplResultFormat.Legacy),
        )


@responses.activate
def test_tabular_is_silent(client):
    responses.add(responses.POST, APL_URL, json=RESULT, status=200)

    with warnings.catch_warnings():
        warnings.simplefilter("error", FutureWarning)
        client.query(
            "['d'] | limit 1",
            AplOptions(format=AplResultFormat.Tabular),
        )


@responses.activate
def test_query_legacy_warns(client):
    responses.add(
        responses.POST,
        "http://localhost/v1/datasets/d/query",
        json={
            "status": RESULT["status"],
            "matches": [],
            "buckets": {"series": [], "totals": []},
        },
        status=200,
    )

    with pytest.warns(FutureWarning, match="query_legacy"):
        client.query_legacy(
            "d",
            QueryLegacy(startTime="", endTime=""),
            QueryOptions(saveAsKind=QueryKind.ANALYTICS),
        )


@responses.activate
def test_warning_category_is_futurewarning(client):
    """
    A DeprecationWarning here would be invisible to the callers who need it.
    """
    responses.add(responses.POST, APL_URL, json=RESULT, status=200)

    with pytest.warns(FutureWarning) as caught:
        client.query(
            "['d'] | limit 1",
            AplOptions(format=AplResultFormat.Legacy),
        )

    assert [w.category for w in caught] == [FutureWarning]
    assert not any(issubclass(w.category, DeprecationWarning) for w in caught)
