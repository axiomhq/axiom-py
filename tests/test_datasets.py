"""This module contains the tests for the DatasetsClient."""
import os
import gzip
import ujson
import unittest
from logging import getLogger
from .helpers import get_random_name
from axiom import (
    Client,
    DatasetCreateRequest,
    DatasetUpdateRequest,
    ContentEncoding,
    ContentType,
    IngestOptions,
)
from requests.exceptions import HTTPError


class TestDatasets(unittest.TestCase):

    dataset_name: str
    client: Client

    @classmethod
    def setUpClass(cls):
        cls.dataset_name = get_random_name()
        cls.client = Client(
            os.getenv("AXIOM_URL"),
            os.getenv("AXIOM_TOKEN"),
            os.getenv("AXIOM_ORG_ID"),
        )
        cls.logger = getLogger()
        cls.logger.info(f"generated random dataset name is: {cls.dataset_name}")

    def test_step1_create(self):
        """Tests create dataset endpoint"""
        req = DatasetCreateRequest(
            name=self.dataset_name,
            description="create a dataset to test the python client",
        )
        res = self.client.datasets.create(req)
        self.logger.debug(res)
        assert res.name == self.dataset_name

    def test_step2_ingest(self):
        """Tests the ingest endpoint"""
        events = [
            {
                "time": "17/May/2015:08:05:32 +0000",
                "remote_ip": "93.180.71.3",
                "remote_user": "-",
                "request": "GET /downloads/product_1 HTTP/1.1",
                "response": 304,
                "bytes": 0,
                "referrer": "-",
                "agent": "Debian APT-HTTP/1.3 (0.8.16~exp12ubuntu10.21)",
            },
            {
                "time": "17/May/2015:08:05:32 +0000",
                "remote_ip": "93.180.71.3",
                "remote_user": "-",
                "request": "GET /downloads/product_1 HTTP/1.1",
                "response": 304,
                "bytes": 0,
                "referrer": "-",
                "agent": "Debian APT-HTTP/1.3 (0.8.16~exp12ubuntu10.21)",
            },
        ]
        data: bytes = ujson.dumps(events).encode()
        payload = gzip.compress(data)
        opts = IngestOptions(
            "time",
            "2/Jan/2006:15:04:05 +0000",
            # CSV_delimiter obviously not valid for JSON, but perfectly fine to test for its presence in this test.
            ";",
        )
        res = self.client.datasets.ingest(
            self.dataset_name,
            payload=payload,
            contentType=ContentType.JSON,
            enc=ContentEncoding.GZIP,
            opts=opts,
        )
        self.logger.debug(res)

        assert (
            res.ingested == 2
        ), f"expected ingested count to equal 2, found {res.ingested}"
        self.logger.info("ingested 2 events successfully.")

    def test_step3_ingest_events(self):
        """Tests the ingest_events method"""
        res = self.client.datasets.ingest_events(
            dataset=self.dataset_name,
            events=[{"foo": "bar"}, {"bar": "baz"}],
        )
        self.logger.debug(res)

        assert (
            res.ingested == 2
        ), f"expected ingested count to equal 2, found {res.ingested}"

    def test_step3_ingest_wrong_encoding(self):
        try:
            self.client.datasets.ingest("", "", ContentType.JSON, "")
        except ValueError as err:
            self.logger.debug(err)
            self.logger.debug(
                "Exceptioin was raised for wrong content-encoding, as expected."
            )
            return

        self.fail("error should have been thrown for wrong content-encoding")

    def test_step3_ingest_wrong_content_type(self):
        try:
            self.client.datasets.ingest("", "", "", ContentEncoding.GZIP)
        except ValueError as err:
            self.logger.debug(err)
            self.logger.debug(
                "Exceptioin was raised for wrong content-type, as expected."
            )
            return

        self.fail("error should have been thrown for wrong content-type")

    def test_step4_get(self):
        """Tests get dataset endpoint"""
        dataset = self.client.datasets.get(self.dataset_name)
        self.logger.debug(dataset)

        assert dataset.name == self.dataset_name

    def test_step5_list(self):
        """Tests list datasets endpoint"""
        datasets = self.client.datasets.get_list()
        self.logger.debug(datasets)

        assert len(datasets) > 0

    def test_step6_update(self):
        """Tests update dataset endpoint"""
        updateReq = DatasetUpdateRequest("updated name through test")
        ds = self.client.datasets.update(self.dataset_name, updateReq)

        assert ds.description == updateReq.description

    def test_step7_delete(self):
        """Tests delete dataset endpoint"""

        try:
            self.client.datasets.delete(self.dataset_name)
            datasets = self.client.datasets.get_list()

            self.assertEqual(len(datasets), 0, "expected test dataset to be deleted")
        except HTTPError as err:
            self.logger.error(err)
            self.fail(f"dataset {self.dataset_name} not found")

    @classmethod
    def tearDownClass(cls):
        """A teardown that checks if the dataset still exists and deletes it would be great,
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
        except HTTPError as err:
            # nothing to do here, since the dataset doesn't exist
            cls.logger.warning(err)
        cls.logger.info("finish cleaning up after TestDatasets")
