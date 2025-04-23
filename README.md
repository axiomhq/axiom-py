> [!WARNING]
> Version [v0.9.0](https://github.com/axiomhq/axiom-py/releases/tag/v0.9.0) removes the aggregation operation enum, see [#158](https://github.com/axiomhq/axiom-py/pull/158).

# axiom-py [![CI][ci_badge]][ci] [![PyPI version][pypi_badge]][pypi] [![Python version][version_badge]][pypi]

```py
import axiom_py

client = axiom_py.Client()

client.ingest_events(dataset="DATASET_NAME", events=[{"foo": "bar"}, {"bar": "baz"}])
client.query(r"['DATASET_NAME'] | where foo == 'bar' | limit 100")
```

## Install

```sh
pip install axiom-py
```

## Documentation

Read documentation on [axiom.co/docs/guides/python](https://axiom.co/docs/guides/python).

## License

[MIT](./LICENSE)

<!-- Badges -->

[ci]: https://github.com/axiomhq/axiom-py/actions/workflows/ci.yml
[ci_badge]: https://img.shields.io/github/actions/workflow/status/axiomhq/axiom-py/ci.yml?branch=main&ghcache=unused
[pypi]: https://pypi.org/project/axiom-py/
[pypi_badge]: https://img.shields.io/pypi/v/axiom-py.svg
[version_badge]: https://img.shields.io/pypi/pyversions/axiom-py.svg
