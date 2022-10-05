# axiom-py

[![CI](https://github.com/axiomhq/axiom-py/actions/workflows/ci.yml/badge.svg)](https://github.com/axiomhq/axiom-py/actions/workflows/ci.yml) [![PyPI version](https://img.shields.io/pypi/v/axiom-py.svg)](https://pypi.org/project/axiom-py/) [![Python version](https://img.shields.io/pypi/pyversions/axiom-py.svg)](https://pypi.org/project/axiom-py/) 

Axiom API Python bindings.

⚠️ This library is still a work-in-progress.

## Table of Contents

- [axiom-py](#axiom-py)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Standard Installation](#standard-installation)
  - [Install from Source](#install-from-source)
  - [Authentication](#authentication)
  - [Usage](#usage)
    - [Example](#example)
  - [Documentation](#documentation)
  - [Contributing](#contributing)
  - [License](#license)

## Introduction

`axiom-py` is a Python library that handles client connections and wraps API functions for interacting with the Axiom API.

## Standard Installation

The library can be found in the [Python Package Index (PyPI)](https://pypi.org/) as `axiom-py`, located [here](https://pypi.org/project/axiom-py/).

You can install `axiom-py` with the following command:

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

## Install from Source

```
git clone `https://github.com/axiomhq/axiom-py`
cd axiom-py
```

## Authentication

The Client is initialized with the url of the deployment and an access token. The access token can be a personal token retreived from the users profile page or an ingest token retrieved from the settings of the Axiom deployment.

**The personal access token grants access to all resources available to the user on his behalf.**

**The ingest token just allows ingestion into the datasets the token is configured for.**

## Usage

1. import axiom
2. set axiom token, organization id and create the client

### Example
```py
import os
import axiom

access_token = os.getenv("AXIOM_TOKEN")
org_id = os.getenv("AXIOM_ORG_ID")

client = axiom.Client(access_token, org_id)

# Ingest into a dataset
print(client.datasets.ingest("foobar", [{"foo": "bar"}]))
```

## Documentation

You can find the Axiom and Axiom Py documentation on the [docs website.](https://docs.axiom.co/)

## Contributing

This project uses [Poetry](https://python-poetry.org) for dependecy management
and packaging, so make sure that this is installed (see [Poetry Installation](https://python-poetry.org/docs/#installation)).

Run `poetry install` to install dependencies and `poetry shell` to activate a
virtual environment.

## License

&copy; Axiom, Inc., 2021

Distributed under MIT License (`The MIT License`).

See [LICENSE](LICENSE) for more information.
