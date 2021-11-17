"""This module contains the tests for the DatasetsClient."""
import os
from axiom import Client


def test_ingest():
    """Tests the ingest endpoint"""
    client = Client(os.getenv("AXIOM_DEPLOYMENT_URL"), os.getenv("AXIOM_TOKEN"), os.getenv('AXIOM_ORG_ID'))
    print(
        client.datasets.ingest(
            os.getenv("AXIOM_DATASET"), [{"foo": "bar"}, {"bar": "baz"}]
        )
    )
