from axiom_py import AplOptions, AplResultFormat, Client


def test_apl_options_default_to_tabular():
    opts = AplOptions()
    assert opts.format == AplResultFormat.Tabular


def test_client_prepare_apl_options_defaults_to_tabular():
    client = Client(token="test-token", url="http://localhost")
    try:
        params = client._prepare_apl_options(None)
        assert params["format"] == AplResultFormat.Tabular.value
    finally:
        client.shutdown_hook()
