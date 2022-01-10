"""This module contains the tests for the DatasetsClient."""
import os
import gzip
import ujson
import unittest
import rfc3339
from typing import List, Dict, Any
from logging import getLogger
from .helpers import get_random_name, parse_time
from axiom import (
    Client,
    DatasetCreateRequest,
    DatasetUpdateRequest,
    ContentEncoding,
    ContentType,
    IngestOptions,
    WrongQueryKindException,
)
from axiom.query import (
    Query,
    QueryOptions,
    QueryKind,
    Filter,
    Order,
    VirtualField,
    Projection,
    FilterOperation,
)
from axiom.query.result import (
    QueryResult,
    QueryStatus,
    Entry,
    EntryGroup,
    Timeseries,
    Interval,
)
from axiom.query.aggregation import Aggregation, AggregationOperation

from requests.exceptions import HTTPError
from datetime import datetime, timedelta


class TestDatasets(unittest.TestCase):

    dataset_name: str
    events: List[Dict[str, Any]]
    client: Client
    events_time_format = "%d/%b/%Y:%H:%M:%S +0000"

    @classmethod
    def setUpClass(cls):
        cls.logger = getLogger()

        cls.dataset_name = get_random_name()
        cls.logger.info(f"generated random dataset name is: {cls.dataset_name}")

        # create events to ingest and query
        # cls.events_time_format = "%d/%b/%Y:%H:%M:%S +0000"
        time = datetime.utcnow() - timedelta(minutes=1)
        time_formatted = time.strftime(cls.events_time_format)
        cls.logger.info(f"time_formatted: {time_formatted}")
        cls.events = [
            {
                "_time": time_formatted,
                "remote_ip": "93.180.71.3",
                "remote_user": "-",
                "request": "GET /downloads/product_1 HTTP/1.1",
                "response": 304,
                "bytes": 0,
                "referrer": "-",
                "agent": "Debian APT-HTTP/1.3 (0.8.16~exp12ubuntu10.21)",
            },
            {
                "_time": time_formatted,
                "remote_ip": "93.180.71.3",
                "remote_user": "-",
                "request": "GET /downloads/product_1 HTTP/1.1",
                "response": 304,
                "bytes": 0,
                "referrer": "-",
                "agent": "Debian APT-HTTP/1.3 (0.8.16~exp12ubuntu10.21)",
            },
        ]
        cls.client = Client(
            os.getenv("AXIOM_URL"),
            os.getenv("AXIOM_TOKEN"),
            os.getenv("AXIOM_ORG_ID"),
        )

    def test_step001_create(self):
        """Tests create dataset endpoint"""
        req = DatasetCreateRequest(
            name=self.dataset_name,
            description="create a dataset to test the python client",
        )
        res = self.client.datasets.create(req)
        self.logger.debug(res)
        assert res.name == self.dataset_name

    def test_step002_ingest(self):
        """Tests the ingest endpoint"""
        data: bytes = ujson.dumps(self.events).encode()
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

    def test_step003_ingest_events(self):
        """Tests the ingest_events method"""
        time = datetime.utcnow() - timedelta(hours=1)
        time_formatted = rfc3339.format(time)

        res = self.client.datasets.ingest_events(
            dataset=self.dataset_name,
            events=[
                {"foo": "bar", "_time": time_formatted},
                {"bar": "baz", "_time": time_formatted},
            ],
        )
        self.logger.debug(res)

        assert (
            res.ingested == 2
        ), f"expected ingested count to equal 2, found {res.ingested}"

    def test_step003_ingest_wrong_encoding(self):
        try:
            self.client.datasets.ingest("", "", ContentType.JSON, "")
        except ValueError as err:
            self.logger.debug(err)
            self.logger.debug(
                "Exceptioin was raised for wrong content-encoding, as expected."
            )
            return

        self.fail("error should have been thrown for wrong content-encoding")

    def test_step003_ingest_wrong_content_type(self):
        try:
            self.client.datasets.ingest("", "", "", ContentEncoding.GZIP)
        except ValueError as err:
            self.logger.debug(err)
            self.logger.debug(
                "Exceptioin was raised for wrong content-type, as expected."
            )
            return

        self.fail("error should have been thrown for wrong content-type")

    def test_step004_get(self):
        """Tests get dataset endpoint"""
        dataset = self.client.datasets.get(self.dataset_name)
        self.logger.debug(dataset)

        assert dataset.name == self.dataset_name

    def test_step005_list(self):
        """Tests list datasets endpoint"""
        datasets = self.client.datasets.get_list()
        self.logger.debug(datasets)

        assert len(datasets) > 0

    def test_step006_update(self):
        """Tests update dataset endpoint"""
        updateReq = DatasetUpdateRequest("updated name through test")
        ds = self.client.datasets.update(self.dataset_name, updateReq)

        assert ds.description == updateReq.description

    def test_step007_query(self):
        """Test querying a dataset"""
        # query the events we ingested in step2
        startTime = datetime.utcnow() - timedelta(minutes=2)
        endTime = datetime.utcnow()

        q = Query(startTime=startTime, endTime=endTime)
        opts = QueryOptions(
            streamingDuration=timedelta(seconds=60),
            nocache=True,
            saveAsKind=QueryKind.ANALYTICS,
        )
        qr = self.client.datasets.query(self.dataset_name, q, opts)

        self.assertIsNotNone(qr.savedQueryID)
        self.assertEqual(len(qr.matches), len(self.events))
        # get history
        history = self.client.datasets.history(qr.savedQueryID)
        self.assertIsNotNone(history)
        self.assertEqual(qr.savedQueryID, history.id)
        self.assertEqual(opts.saveAsKind, history.kind)
        # check that time parsing is correct
        self.assertEqual(history.query.startTime.date(), q.startTime.date())
        self.assertEqual(history.query.startTime.time(), q.startTime.time())
        self.assertEqual(history.query.endTime.date(), q.endTime.date())
        self.assertEqual(history.query.endTime.time(), q.endTime.time())

    def test_step007_wrong_query_kind(self):
        startTime = datetime.utcnow() - timedelta(minutes=2)
        endTime = datetime.utcnow()
        opts = QueryOptions(
            streamingDuration=timedelta(seconds=60),
            nocache=True,
            saveAsKind=QueryKind.APL,
        )
        q = Query(startTime, endTime)

        try:
            self.client.datasets.query(self.dataset_name, q, opts)
        except WrongQueryKindException as err:
            self.logger.info("passing kind apl to query raised exception as expected")
            return

        self.fail("was excepting WrongQueryKindException")

    def test_step007_complex_query(self):
        startTime = datetime.utcnow() - timedelta(minutes=2)
        endTime = datetime.utcnow()
        aggregations = [
            Aggregation(alias="event_count", op=AggregationOperation.COUNT, field="*")
        ]
        q = Query(startTime, endTime, aggregations=aggregations)
        q.groupBy = ["success", "remote_ip"]
        q.filter = Filter(FilterOperation.EQUAL, "response", 304)
        q.order = [
            Order("success", True),
            Order("remote_ip", False),
        ]
        q.virtualFields = [VirtualField("success", "response < 400")]
        q.project = [Projection("remote_ip", "ip")]

        res = self.client.datasets.query(self.dataset_name, q, QueryOptions())

        # self.assertEqual(len(self.events), res.status.rowsExamined)
        self.assertEqual(len(self.events), res.status.rowsMatched)

        if len(res.buckets.totals):
            agg = res.buckets.totals[0].aggregations[0]
            self.assertEqual("event_count", agg.op)

    def test_step008_info(self):
        """Tests dataset info endpoint"""
        info = self.client.datasets.info(self.dataset_name)
        self.assertIsNotNone(info)
        self.assertEqual(info.name, self.dataset_name)
        # number of events ingested in step002 and step003
        self.assertEqual(info.numEvents, 4)
        self.assertTrue(len(info.fields) > 0)

    def test_step009_trim(self):
        """Tests dataset trim endpoint"""
        res = self.client.datasets.trim(self.dataset_name, timedelta(seconds=1))
        # HINT(lukasmalkmus): There are no blocks to trim in this test.
        self.assertEqual(0, res.numDeleted)

    def test_step999_delete(self):
        """Tests delete dataset endpoint"""

        self.client.datasets.delete(self.dataset_name)
        try:
            dataset = self.client.datasets.get(self.dataset_name)

            self.assertIsNone(
                dataset, f"expected test dataset (%{self.dataset_name}) to be deleted"
            )
        except HTTPError as err:
            # the get method returns 404 error if dataset doesn't exist, so that means
            # that our tests passed, otherwise, it should fail.
            if err.response.status_code != 404:
                self.fail(err)

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
