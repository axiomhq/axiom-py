"""
The sync and async clients are two copies of the same logic.

Nothing but this test stops them drifting, and they have drifted before: the
legacy default and the dead `limit` serialization each existed twice. Every
query behavior change has to satisfy both.
"""

from datetime import datetime, timezone

import pytest

from axiom_py import AplOptions, AplResultFormat, AsyncClient, Client
from axiom_py.query import QueryKind, QueryOptions

START = datetime(2026, 1, 1, tzinfo=timezone.utc)
END = datetime(2026, 1, 2, tzinfo=timezone.utc)

APL_CASES = [
    pytest.param(None, id="no-options"),
    pytest.param(AplOptions(), id="defaults"),
    pytest.param(AplOptions(format=AplResultFormat.Tabular), id="tabular"),
    pytest.param(AplOptions(format=AplResultFormat.Legacy), id="legacy"),
    pytest.param(AplOptions(start_time=START, end_time=END), id="time-range"),
    pytest.param(AplOptions(cursor="abc", includeCursor=True), id="cursor"),
]

QUERY_OPTION_CASES = [
    pytest.param(QueryOptions(), id="defaults"),
    pytest.param(QueryOptions(saveAsKind=QueryKind.STREAM), id="stream"),
    pytest.param(QueryOptions(nocache=True), id="nocache"),
]


@pytest.fixture
def clients():
    kwargs = dict(token="xaat-t", org_id="o", url="http://localhost")
    return Client(**kwargs), AsyncClient(**kwargs)


@pytest.mark.parametrize("opts", APL_CASES)
def test_apl_query_params_match(clients, opts, recwarn):
    sync, asyn = clients
    assert sync._prepare_apl_options(opts) == asyn._prepare_apl_options(opts)


@pytest.mark.parametrize("opts", APL_CASES)
def test_apl_payload_matches(clients, opts, recwarn):
    sync, asyn = clients
    assert sync._prepare_apl_payload("['d'] | limit 1", opts) == (
        asyn._prepare_apl_payload("['d'] | limit 1", opts)
    )


@pytest.mark.parametrize("opts", QUERY_OPTION_CASES)
def test_legacy_query_params_match(clients, opts):
    sync, asyn = clients
    assert sync._prepare_query_options(opts) == (
        asyn._prepare_query_options(opts)
    )


def test_ingest_params_match(clients):
    from axiom_py import IngestOptions

    sync, asyn = clients
    for opts in (
        None,
        IngestOptions(),
        IngestOptions(timestamp_field="ts", CSV_delimiter=";"),
    ):
        assert sync._prepare_ingest_options(opts) == (
            asyn._prepare_ingest_options(opts)
        )


def test_both_clients_default_to_tabular(clients):
    sync, asyn = clients
    for client in (sync, asyn):
        assert client._prepare_apl_options(None)["format"] == "tabular"
        assert client._prepare_apl_options(AplOptions())["format"] == "tabular"


ENV_CASES = [
    pytest.param({"AXIOM_URL": "https://api.example.com"}, id="url"),
    pytest.param({"AXIOM_URL": ""}, id="empty-url"),
    pytest.param({}, id="unset"),
]


@pytest.mark.parametrize("env", ENV_CASES)
def test_environment_is_read_the_same_way(env, monkeypatch):
    """
    AsyncClient ignored AXIOM_URL and always talked to production, so an
    async caller pointed at dev silently wrote to prod.
    """
    for key in ("AXIOM_URL", "AXIOM_TOKEN", "AXIOM_ORG_ID"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("AXIOM_TOKEN", "xaat-t")
    monkeypatch.setenv("AXIOM_ORG_ID", "o")
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    assert str(Client().session.base_url).rstrip("/") == (
        str(AsyncClient().client.base_url).rstrip("/")
    )
