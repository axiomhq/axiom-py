"""This module contains test for the logging Handler."""
import os
import logging
import unittest
from axiom import Client
from axiom.logging import AxiomHandler


class TestLogger(unittest.TestCase):
    def test_log(self):
        """Tests a simple log"""
        client = Client(os.getenv("AXIOM_DEPLOYMENT_URL"), os.getenv("AXIOM_TOKEN"))
        axiom_handler = AxiomHandler(client, os.getenv("AXIOM_DATASET"))

        root = logging.getLogger()
        root.addHandler(axiom_handler)

        root.warning("foo")
