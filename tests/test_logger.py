"""This module contains test for the logging Handler."""

import os
import logging
import unittest
import time

from .helpers import get_random_name
from axiom_py import Client
from axiom_py.logging import AxiomHandler


class TestLogger(unittest.TestCase):
    def test_log(self):
        """Tests the logger"""
        client = Client(
            os.getenv("AXIOM_TOKEN"),
            os.getenv("AXIOM_ORG_ID"),
            os.getenv("AXIOM_URL"),
        )
        # Create a dataset for that purpose
        dataset_name = get_random_name()
        client.datasets.create(
            dataset_name, "A dataset to test axiom-py logger"
        )

        axiom_handler = AxiomHandler(client, dataset_name, interval=1.0)

        logger = logging.getLogger()
        logger.addHandler(axiom_handler)

        logger.warning("This is a log!")

        # This log shouldn't be ingested yet
        res = client.apl_query(dataset_name)
        self.assertEqual(0, res.status.rowsExamined)

        # Flush events
        axiom_handler.flush()

        # Wait a bit for the ingest to finish
        time.sleep(0.5)

        # Now we should have a log
        res = client.apl_query(dataset_name)
        self.assertEqual(1, res.status.rowsExamined)

        logger.warning(
            "This log should be ingested without any subsequent call"
        )

        # Wait for the background flush.
        time.sleep(1.5)

        # Now we should have two logs
        res = client.apl_query(dataset_name)
        self.assertEqual(2, res.status.rowsExamined)

        # Cleanup created dataset
        client.datasets.delete(dataset_name)
