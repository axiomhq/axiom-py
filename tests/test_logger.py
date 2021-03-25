"""This module contains test for the logging Handler."""
import os
import logging
from axiom import Client
from axiom.logging import AxiomHandler


def test_log():
    """Tests a simple log"""
    client = Client(os.getenv("AXIOM_DEPLOYMENT_URL"), os.getenv("AXIOM_TOKEN"))
    axiom_handler = AxiomHandler(client, os.getenv("AXIOM_DATASET"))

    root = logging.getLogger()
    root.addHandler(axiom_handler)

    root.warning("foo")
