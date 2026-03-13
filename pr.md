This switches `axiom-py` APL query defaults from `legacy` to `tabular` for both sync and async clients, aligning SDK behavior with the format migration plan.

Slack context: <https://watchlyhq.slack.com/archives/C0ABV843Y9M/p1773440506177029|#gilfoyle-sessions thread>

The change updates `AplOptions` defaults and both `_prepare_apl_options` code paths, while preserving explicit `format=AplResultFormat.Legacy` behavior for callers that still need it. Tests now assert the tabular default behavior directly.

Validation:
- `python3 -m pytest tests/test_query_defaults.py tests/test_client_async.py -q`
