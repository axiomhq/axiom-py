<!---
Keep this page in sync with https://github.com/axiomhq/docs/blob/main/guides/python.mdx
-->

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

- **Ingest with ease, store without limits:** Axiom's next-generation datastore
  enables ingesting petabytes of data with ultimate efficiency. Ship logs from
  Kubernetes, AWS, Azure, Google Cloud, DigitalOcean, Nomad, and others.
- **Query everything, all the time:** Whether DevOps, SecOps, or EverythingOps,
  query all your data no matter its age. No provisioning, no moving data from
  cold/archive to "hot", and no worrying about slow queries. All your data, all.
  the. time.
- **Powerful dashboards, for continuous observability:** Build dashboards to
  collect related queries and present information that's quick and easy to
  digest for you and your team. Dashboards can be kept private or shared with
  others, and are the perfect way to bring together data from different sources.

For more information check out the
[official documentation](https://axiom.co/docs) and our
[community Discord](https://axiom.co/discord).

## Prerequisites

- [Create an Axiom account](https://app.axiom.co/register).
- [Create a dataset in Axiom](https://axiom.co/docs/reference/datasets) where you send your data.
- [Create an API token in Axiom](https://axiom.co/docs/reference/tokens) with permissions to update the dataset you have created.

## Install SDK

Linux / MacOS

```shell
python3 -m pip install axiom-py
```

Windows

```shell
py -m pip install axiom-py
```

pip

```shell
pip3 install axiom-py
```

If you use the [Axiom CLI](https://axiom.co/docs/reference/cli), run `eval $(axiom config export -f)` to configure your environment variables. Otherwise, [create an API token](https://axiom.co/docs/reference/tokens) and export it as `AXIOM_TOKEN`.

You can also configure the client using options passed to the client constructor:

```py
import axiom_py

client = axiom_py.Client("API_TOKEN")
```

## Use client

```py
import axiom_py
import rfc3339
from datetime import datetime,timedelta

client = axiom_py.Client()

client.ingest_events(
    dataset="DATASET_NAME",
    events=[
        {"foo": "bar"},
        {"bar": "baz"},
    ])
client.query(r"['DATASET_NAME'] | where foo == 'bar' | limit 100")
```

See a [full example](https://github.com/axiomhq/axiom-py/tree/main/examples/client_example.py).

## Example with `AxiomHandler`

The example below uses `AxiomHandler` to send logs from the `logging` module to Axiom:

```python
import axiom_py
from axiom_py.logging import AxiomHandler
import logging

def setup_logger():
    client = axiom_py.Client()
    handler = AxiomHandler(client, "DATASET_NAME")
    logging.getLogger().addHandler(handler)
```

See a [full example](https://github.com/axiomhq/axiom-py/tree/main/examples/logger_example.py).

## Example with `structlog`

The example below uses [structlog](https://github.com/hynek/structlog) to send logs to Axiom:

```python
from axiom_py import Client
from axiom_py.structlog import AxiomProcessor

def setup_logger():
    client = Client()

    structlog.configure(
        processors=[
            # ...
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", key="_time"),
            AxiomProcessor(client, "DATASET_NAME"),
            # ...
        ]
    )
```

See a [full example](https://github.com/axiomhq/axiom-py/tree/main/examples/structlog_example.py).

<!-- Badges -->

[ci]: https://github.com/axiomhq/axiom-py/actions/workflows/ci.yml
[ci_badge]: https://img.shields.io/github/actions/workflow/status/axiomhq/axiom-py/ci.yml?branch=main&ghcache=unused
[pypi]: https://pypi.org/project/axiom-py/
[pypi_badge]: https://img.shields.io/pypi/v/axiom-py.svg
[version_badge]: https://img.shields.io/pypi/pyversions/axiom-py.svg
