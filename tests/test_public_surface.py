"""
The public surface after the legacy removal.

`test_imports.py` used to cover this by importing names and printing, which
asserted nothing. These assert.
"""

import importlib

import pytest

import axiom_py

REMOVED = [
    "AplResultFormat",
    "WrongQueryKindException",
    "QueryLegacy",
    "QueryLegacyResult",
    "QueryOptions",
    "QueryKind",
]

REMOVED_MODULES = [
    "axiom_py.query.query",
    "axiom_py.query.filter",
    "axiom_py.query.aggregation",
    "axiom_py.query.options",
    "axiom_py._deprecation",
]

EXPORTED = [
    "Client",
    "AsyncClient",
    "AplOptions",
    "AxiomError",
    "Dataset",
    "Annotation",
    "AxiomHandler",
    "AxiomProcessor",
    "AsyncAxiomHandler",
    "AsyncAxiomProcessor",
    "AsyncDatasetsClient",
    "AsyncAnnotationsClient",
    "AsyncTokensClient",
    "AsyncUsersClient",
]


@pytest.mark.parametrize("name", REMOVED)
def test_legacy_names_are_gone(name):
    assert not hasattr(axiom_py, name)


@pytest.mark.parametrize("module", REMOVED_MODULES)
def test_legacy_modules_are_gone(module):
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(module)


@pytest.mark.parametrize("name", EXPORTED)
def test_supported_names_are_exported(name):
    assert hasattr(axiom_py, name)


def test_query_result_has_no_legacy_fields():
    from dataclasses import fields

    from axiom_py.query import QueryResult

    names = {f.name for f in fields(QueryResult)}
    assert names == {"status", "tables", "dataset_names", "savedQueryID"}


def test_query_always_requests_tabular():
    client = axiom_py.Client(
        token="xaat-t", org_id="o", url="http://localhost"
    )
    assert client._prepare_apl_options(None) == {"format": "tabular"}
    assert client._prepare_apl_options(axiom_py.AplOptions()) == (
        {"format": "tabular"}
    )
