# axiom-py ![ci](https://github.com/axiomhq/axiom-py/workflows/ci/badge.svg)
Axiom API Python bindings.

## Usage

```py
import os
import axiom

deployment_url = os.getenv("AXM_DEPLOYMENT_URL")
access_token = os.getenv("AXM_ACCESS_TOKEN")

client = axiom.Client(deployment_url, access_token))

# Ingest into a dataset
print(client.datasets.ingest("foobar", [{"foo": "bar"}]))
```

## Contributing

This project uses [Poetry](https://python-poetry.org) for dependecy management
and packaging, so make sure that this is installed (see [Poetry Installation](https://python-poetry.org/docs/#installation)).

Run `poetry install` to install dependencies and `poetry shell` to activate a
virtual environment.
