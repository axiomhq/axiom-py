![axiom-py: The official Python bindings for the Axiom API](.github/images/banner-dark.svg#gh-dark-mode-only)
![axiom-py: The official Python bindings for the Axiom API](.github/images/banner-light.svg#gh-light-mode-only)

<div align="center">

[![CI][ci_badge]][ci]
[![PyPI version][pypi_badge]][pypi]
[![Python version][version_badge]][pypi]

</div>

[Axiom](https://axiom.co) unlocks observability at any scale.

- **Ingest with ease, store without limits:** Axiom’s next-generation datastore enables ingesting petabytes of data with ultimate efficiency. Ship logs from Kubernetes, AWS, Azure, Google Cloud, DigitalOcean, Nomad, and others.
- **Query everything, all the time:** Whether DevOps, SecOps, or EverythingOps, query all your data no matter its age. No provisioning, no moving data from cold/archive to “hot”, and no worrying about slow queries. All your data, all. the. time.
- **Powerful dashboards, for continuous observability:** Build dashboards to collect related queries and present information that’s quick and easy to digest for you and your team. Dashboards can be kept private or shared with others, and are the perfect way to bring together data from different sources

For more information check out the [official documentation](https://axiom.co/docs)
and our
[community Slack](https://axiomfm.slack.com/join/shared_invite/zt-w7d1vepe-L0upiOL6n6MXfjr33sCBUQ).

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

Otherwise create a personal token in [the Axiom settings](https://app.axiom.co/profile) and export it as `AXIOM_TOKEN`. Set `AXIOM_ORG_ID` to the organization ID from the settings page of the organization you want to access.

You can also configure the client using options passed to the client constructor:

```py
import axiom

client = axiom.Client("<api token>", "<org id>")
```

Create and use a client like this:

```py
import os
import axiom

client = axiom.Client()

time = datetime.utcnow() - timedelta(hours=1)
time_formatted = rfc3339.format(time)

client.datasets.ingest_events(
    dataset="my-dataset",
    events=[
        {"foo": "bar", "_time": time_formatted},
        {"bar": "baz", "_time": time_formatted},
    ])
client.datasets.query(r"['my-dataset'] | where foo == 'bar' | limit 100")
```

for more examples, check out the [examples](examples) directory.

## Contributing

This project uses [Poetry](https://python-poetry.org) for dependecy management
and packaging, so make sure that this is installed (see [Poetry Installation](https://python-poetry.org/docs/#installation)).

Run `poetry install` to install dependencies and `poetry shell` to activate a
virtual environment.

## License

Distributed under MIT License (`The MIT License`).

<!-- Badges -->

[ci]: https://github.com/axiomhq/axiom-py/actions/workflows/ci.yml
[ci_badge]: https://img.shields.io/github/actions/workflow/status/axiomhq/axiom-py/ci.yml?branch=main&ghcache=unused
[pypi]: https://pypi.org/project/axiom-py/
[pypi_badge]: https://img.shields.io/pypi/v/axiom-py.svg
[version_badge]: https://img.shields.io/pypi/pyversions/axiom-py.svg
