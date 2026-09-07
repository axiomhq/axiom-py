# Migrating off the legacy result format

axiom-py returns APL query results in the legacy format by default. The
tabular format replaces it. This guide shows what changes, when it changes,
and how to update your code.

## What changes, and when

| Version | Change |
| --- | --- |
| 0.13.0 | Every legacy path warns. Nothing else changes. |
| 0.14.0 | The default format becomes tabular. `AplOptions.limit` is removed. |
| 0.15.0 | The legacy format, `query_legacy()` and the `QueryLegacy` types are removed. |

The warnings use `FutureWarning`, so Python shows them by default. Each
warning points at the line in your own code that made the query.

## Move to the tabular format

1. Upgrade to axiom-py 0.13.0.
2. Run your test suite and read the warnings. Each one names the call to change.
3. Pass `AplOptions(format=AplResultFormat.Tabular)` to every `query()` call.
4. Replace the code that reads `result.matches` and `result.buckets`.
5. When no warnings are left, upgrade to 0.14.0 and remove the explicit format.

## Read the results

The tabular format returns one table for every result set. `events()` gives
you one dictionary per row, keyed by field name.

### Filter queries

The legacy format put matching events in `result.matches`, with the fields
under `.data`.

```python
result = client.query("['my-dataset'] | where svc == 'api'")
for match in result.matches:
    print(match.data["svc"], match.data["ms"])
```

The tabular format puts the same events in the first table.

```python
result = client.query(
    "['my-dataset'] | where svc == 'api'",
    AplOptions(format=AplResultFormat.Tabular),
)
for event in result.tables[0].events():
    print(event["svc"], event["ms"])
```

### Aggregations

This is the larger change. In the legacy format an aggregation left
`result.matches` empty and put the results in `result.buckets`. The group
values and the aggregated values were separate objects.

```python
result = client.query("['my-dataset'] | summarize avg(ms) by svc")
for total in result.buckets.totals:
    print(total.group["svc"], total.aggregations[0].value)
```

The tabular format returns a single flat row for each group. The group field
and the aggregated field sit side by side, and the aggregation takes the
alias from the query.

```python
result = client.query(
    "['my-dataset'] | summarize avg(ms) by svc",
    AplOptions(format=AplResultFormat.Tabular),
)
for event in result.tables[0].events():
    print(event["svc"], event["avg_ms"])
```

Filter queries and aggregations now read the same way.

### Column and field metadata

`result.tables[0].fields` describes each column, in the order of the data.

```python
for field in result.tables[0].fields:
    print(field.name, field.type)
```

## AplOptions.limit is removed

`AplOptions.limit` never reached the server. It was serialized as an unknown
query parameter and the server dropped it. Any query that appeared to use it
returned the default number of rows.

Put the limit in the APL query instead.

```python
client.query("['my-dataset'] | limit 100")
```

## query_legacy() is removed

`query_legacy()` calls the structured query API, which came before APL. It is
unrelated to the result format, and 0.15.0 removes both.

Express the query in APL and call `query()`. The `QueryLegacy`, `QueryOptions`
and `Aggregation` types under `axiom_py.query` are removed with it.

## Silence the warnings

If you cannot migrate yet, filter the warnings.

```python
import warnings

warnings.filterwarnings("ignore", category=FutureWarning, module="axiom_py")
```

CAUTION: Do not pin to 0.13.x as a long-term answer. That release line gets
no further fixes after 0.15.0.
