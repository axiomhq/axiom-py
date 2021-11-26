"""This module contains test for the logging Handler."""
import os
import logging
import unittest
from .helpers import get_random_name
from axiom import Client, DatasetCreateRequest
from axiom.logging import AxiomHandler


class TestLogger(unittest.TestCase):
    def test_log(self):
        """Tests a simple log"""
        client = Client(
            os.getenv("AXIOM_URL"),
            os.getenv("AXIOM_TOKEN"),
            os.getenv("AXIOM_ORG_ID"),
        )
        # create a dataset for that purpose
        dataset_name = get_random_name()
        req = DatasetCreateRequest(
            name=dataset_name,
            description="a dataset to test axiom-py logger",
        )
        client.datasets.create(req)

        axiom_handler = AxiomHandler(client, dataset_name)

        root = logging.getLogger()
        root.addHandler(axiom_handler)

        root.warning("foo")
        # cleanup created dataset
        client.datasets.delete(dataset_name)
