# axiom-py

<a href="https://axiom.co">
<picture>
  <source media="(prefers-color-scheme: dark) and (min-width: 600px)" srcset="https://axiom.co/assets/github/axiom-github-banner-light-vertical.svg">
  <source media="(prefers-color-scheme: light) and (min-width: 600px)" srcset="https://axiom.co/assets/github/axiom-github-banner-dark-vertical.svg">
  <source media="(prefers-color-scheme: dark) and (max-width: 599px)" srcset="https://axiom.co/assets/github/axiom-github-banner-light-horizontal.svg">
  <img alt="Axiom.co banner" src="https://axiom.co/assets/github/axiom-github-banner-dark-horizontal.svg" align="right">
</picture>
</a>
&nbsp;

[![CI][ci_badge]][ci]
[![PyPI version][pypi_badge]][pypi]
[![Python version][version_badge]][pypi]

[Axiom](https://axiom.co) unlocks observability at any scale.

- **Ingest with ease, store without limits:** Axiom’s next-generation datastore enables ingesting petabytes of data with ultimate efficiency. Ship logs from Kubernetes, AWS, Azure, Google Cloud, DigitalOcean, Nomad, and others.
- **Query everything, all the time:** Whether DevOps, SecOps, or EverythingOps, query all your data no matter its age. No provisioning, no moving data from cold/archive to “hot”, and no worrying about slow queries. All your data, all. the. time.
- **Powerful dashboards, for continuous observability:** Build dashboards to collect related queries and present information that’s quick and easy to digest for you and your team. Dashboards can be kept private or shared with others, and are the perfect way to bring together data from different sources

For more information check out the [official documentation](https://axiom.co/docs)
and our
[community Discord](https://axiom.co/discord).

## Quickstart

Install using `pip`:

```bash
# Linux / MacOS
python3 -m pip install axiom-py

# Windows
py -m pip install axiom-py
```

Alternatively, if you have the [`pip`](https://pip.pypa.io/) package installed, you can install `axiom-py` with the following command:

```bash
pip3 install axiom-py
```

If you use the [Axiom CLI](https://github.com/axiomhq/cli), run `eval $(axiom config export -f)` to configure your environment variables.

Otherwise create a personal token in [the Axiom settings](https://cloud.axiom.co/profile) and export it as `AXIOM_TOKEN`. Set `AXIOM_ORG_ID` to the organization ID from the settings page of the organization you want to access.

You can also configure the client using options passed to the client constructor:

```py
import axiom_py

client = axiom_py.Client("<api token>", "<org id>")
```

Create and use a client like this:

```py
import axiom_py
import rfc3339
from datetime import datetime,timedelta

client = axiom_py.Client()

time = datetime.utcnow() - timedelta(hours=1)
time_formatted = rfc3339.format(time)

client.ingest_events(
    dataset="my-dataset",
    events=[
        {"foo": "bar", "_time": time_formatted},
        {"bar": "baz", "_time": time_formatted},
    ])
client.query(r"['my-dataset'] | where foo == 'bar' | limit 100")
```

For more examples, see [`examples/client.py`](examples/client.py).

## Logger

You can use the `AxiomHandler` to send logs from the `logging` module to Axiom
like this:

```python
import axiom_py
from axiom_py.logging import AxiomHandler
import logging


def setup_logger():
    client = axiom_py.Client()
    handler = AxiomHandler(client, "my-dataset")
    logging.getLogger().addHandler(handler)
```

For a full example, see [`examples/logger.py`](examples/logger.py).

## Contributing

This project uses [uv](https://docs.astral.sh/uv) for dependency management
and packaging, so make sure that this is installed.

## License

Distributed under MIT License (`The MIT License`).

<!-- Badges -->

[ci]: https://github.com/axiomhq/axiom-py/actions/workflows/ci.yml
[ci_badge]: https://img.shields.io/github/actions/workflow/status/axiomhq/axiom-py/ci.yml?branch=main&ghcache=unused
[pypi]: https://pypi.org/project/axiom-py/
[pypi_badge]: https://img.shields.io/pypi/v/axiom-py.svg
[version_badge]: https://img.shields.io/pypi/pyversions/axiom-py.svg
