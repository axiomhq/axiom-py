"""This module contains the tests for the DatasetsClient."""
import os
import unittest
from axiom import Client


class TestDatasets(unittest.TestCase):
    def setUp(self):
        self.client = Client(os.getenv("AXIOM_DEPLOYMENT_URL"), os.getenv("AXIOM_TOKEN"), os.getenv('AXIOM_ORG_ID'))

    def test_ingest(self):
        """Tests the ingest endpoint"""
        print(
            self.client.datasets.ingest(
                os.getenv("AXIOM_DATASET"), [{"foo": "bar"}, {"bar": "baz"}]
            )
        )
