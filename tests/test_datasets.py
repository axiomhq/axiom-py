"""This module contains the tests for the DatasetsClient."""

import os

import unittest
from typing import List, Dict
from logging import getLogger
from datetime import timedelta
from .helpers import get_random_name
from axiom_py import Client, AxiomError


class TestDatasets(unittest.TestCase):
    dataset_name: str
    events: List[Dict[str, object]]
    client: Client
    events_time_format = "%d/%b/%Y:%H:%M:%S +0000"

    @classmethod
    def setUpClass(cls):
        cls.logger = getLogger()

        cls.dataset_name = get_random_name()
        cls.logger.info(
            f"generated random dataset name is: {cls.dataset_name}"
        )

        cls.client = Client(
            os.getenv("AXIOM_TOKEN"),
            os.getenv("AXIOM_ORG_ID"),
            os.getenv("AXIOM_URL"),
        )

    def test_step001_create(self):
        """Tests create dataset endpoint"""
        res = self.client.datasets.create(
            self.dataset_name, "create a dataset to test the python client"
        )
        self.logger.debug(res)
        assert res.name == self.dataset_name

    def test_step002_get(self):
        """Tests get dataset endpoint"""
        dataset = self.client.datasets.get(self.dataset_name)
        self.logger.debug(dataset)

        assert dataset.name == self.dataset_name

    def test_step003_list(self):
        """Tests list datasets endpoint"""
        datasets = self.client.datasets.get_list()
        self.logger.debug(datasets)

        assert len(datasets) > 0

    def test_step004_update(self):
        """Tests update dataset endpoint"""
        newDescription = "updated name through test"
        ds = self.client.datasets.update(self.dataset_name, newDescription)

        assert ds.description == newDescription

    def test_step005_trim(self):
        """Tests dataset trim endpoint"""
        self.client.datasets.trim(self.dataset_name, timedelta(seconds=1))

    def test_step999_delete(self):
        """Tests delete dataset endpoint"""

        self.client.datasets.delete(self.dataset_name)
        try:
            dataset = self.client.datasets.get(self.dataset_name)

            self.assertIsNone(
                dataset,
                f"expected test dataset (%{self.dataset_name}) to be deleted",
            )
        except AxiomError as e:
            # the get method returns 404 error if dataset doesn't exist, so
            # that means that our tests passed, otherwise, it should fail.
            if e.status != 404:
                self.fail(e)

    @classmethod
    def tearDownClass(cls):
        """A teardown that checks if the dataset still exists and deletes it,
        otherwise we might run into zombie datasets on failures."""
        cls.logger.info("cleaning up after TestDatasets...")
        try:
            ds = cls.client.datasets.get(cls.dataset_name)
            if ds:
                cls.client.datasets.delete(cls.dataset_name)
                cls.logger.info(
                    "dataset (%s) was not deleted as part of the test, deleting it now."
                    % cls.dataset_name
                )
        except AxiomError as e:
            # nothing to do here, since the dataset doesn't exist
            cls.logger.warning(e)
        cls.logger.info("finish cleaning up after TestDatasets")
