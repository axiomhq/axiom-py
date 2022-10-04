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

For more information check out the [official documentation](https://axiom.co/docs).

## Usage

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

Otherwise create a personal token in [the Axiom settings](https://cloud.axiom.co/settings/profile) and export it as `AXIOM_TOKEN`. Set `AXIOM_ORG_ID` to the organization ID from the settings page of the organization you want to access.

Create and use a client like this:

### Cloud Example
```py
import os
import axiom

access_token = os.getenv("AXIOM_TOKEN")
org_id = os.getenv("AXIOM_ORG_ID")

client = axiom.Client(access_token, org_id)

client.datasets.ingest("my-dataset", [{"foo": "bar"}])

client.datasets.apl_query(r"['my-dataset'] | where foo == 'bar' | limit 100")
```

## Contributing

This project uses [Poetry](https://python-poetry.org) for dependecy management
and packaging, so make sure that this is installed (see [Poetry Installation](https://python-poetry.org/docs/#installation)).

Run `poetry install` to install dependencies and `poetry shell` to activate a
virtual environment.

## License

Distributed under MIT License (`The MIT License`).

<!-- Badges -->

[ci]: https://github.com/axiomhq/axiom-py/actions/workflows/ci.yml
[ci_badge]: https://github.com/axiomhq/axiom-py/actions/workflows/ci.yml/badge.svg
[pypi]: https://pypi.org/project/axiom-py/
[pypi_badge]: https://img.shields.io/pypi/v/axiom-py.svg
[version_badge]: https://img.shields.io/pypi/pyversions/axiom-py.svg