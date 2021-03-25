# axiom-py [![CI](https://github.com/axiomhq/axiom-py/actions/workflows/ci.yml/badge.svg)](https://github.com/axiomhq/axiom-py/actions/workflows/ci.yml)

Axiom API Python bindings.

### NOTE: This is a development in progress library. Querying is not supported yet. Only ingestion.

## Table of Contents

1. [Introduction](#introduction)
1. [Installation](#installation)
1. [Authentication](#authentication)
1. [Usage](#usage)
1. [Documentation](#documentation)
1. [Contributing](#contributing)
1. [License](#license)

## Introduction

Axiom Py is a Python client library for accessing the Axiom API.

Currently, **Axiom Py requires Python3 or greater.**


## Installation

### Install from source:

```
git clone `https://github.com/axiomhq/axiom-py`
cd axiom-py
```
## Authentication

The Client is initialized with the url of the deployment and an access token. The access token can be a personal token retreived from the users profile page or an ingest token retrieved from the settings of the Axiom deployment.

**The personal access token grants access to all resources available to the user on his behalf.**

**The ingest token just allows ingestion into the datasets the token is configured for.**

## Usage

```py
import os
import axiom

deployment_url = os.getenv("AXIOM_DEPLOYMENT_URL")
access_token = os.getenv("AXIOM_ACCESS_TOKEN")

client = axiom.Client(deployment_url, access_token)

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
