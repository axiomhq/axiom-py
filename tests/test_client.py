"""This module contains the tests for the axiom client."""

import os
import unittest
import gzip
import ujson
import rfc3339
import responses
from logging import getLogger
from datetime import datetime, timedelta
from .helpers import get_random_name
from requests.exceptions import HTTPError
from axiom_py import (
    Client,
    AplOptions,
    AplResultFormat,
    ContentEncoding,
    ContentType,
    IngestOptions,
    WrongQueryKindException,
    DatasetCreateRequest,
)
from axiom_py.query import (
    QueryLegacy,
    QueryOptions,
    QueryKind,
    Filter,
    Order,
    VirtualField,
    Projection,
    FilterOperation,
    Aggregation,
    AggregationOperation,
)


class TestClient(unittest.TestCase):
    client: Client

    @classmethod
    def setUpClass(cls):
        cls.logger = getLogger()
        cls.client = Client(
            os.getenv("AXIOM_TOKEN"),
            os.getenv("AXIOM_ORG_ID"),
            os.getenv("AXIOM_URL"),
        )
        cls.dataset_name = get_random_name()
        cls.logger.info(
            f"generated random dataset name is: {cls.dataset_name}"
        )
        events_time_format = "%d/%b/%Y:%H:%M:%S +0000"
        # create events to ingest and query
        time = datetime.utcnow() - timedelta(minutes=1)
        time_formatted = time.strftime(events_time_format)
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
        # create dataset to test the client
        req = DatasetCreateRequest(
            name=cls.dataset_name,
            description="create a dataset to test the python client",
        )
        cls.client.datasets.create(req)

    @responses.activate
    def test_retries(self):
        axiomUrl = os.getenv("AXIOM_URL") or ""
        url = axiomUrl + "/v1/datasets/test"
        responses.add(responses.GET, url, status=500)
        responses.add(responses.GET, url, status=502)
        responses.add(
            responses.GET,
            url,
            status=200,
            json={"name": "test", "description": "", "who": "", "created": ""},
        )

        self.client.datasets.get("test")
        assert len(responses.calls) == 3

    def test_step001_ingest(self):
        """Tests the ingest endpoint"""
        data: bytes = ujson.dumps(self.events).encode()
        payload = gzip.compress(data)
        opts = IngestOptions(
            "_time",
            "2/Jan/2006:15:04:05 +0000",
            # CSV_delimiter obviously not valid for JSON, but perfectly fine to test for its presence in this test.
            ";",
        )
        res = self.client.ingest(
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

    def test_step002_ingest_events(self):
        """Tests the ingest_events method"""
        time = datetime.utcnow() - timedelta(hours=1)
        time_formatted = rfc3339.format(time)

        res = self.client.ingest_events(
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

    def test_step004_query(self):
        """Test querying a dataset"""
        # query the events we ingested in step2
        startTime = datetime.utcnow() - timedelta(minutes=2)
        endTime = datetime.utcnow()

        q = QueryLegacy(startTime=startTime, endTime=endTime)
        opts = QueryOptions(
            streamingDuration=timedelta(seconds=60),
            nocache=True,
            saveAsKind=QueryKind.ANALYTICS,
        )
        qr = self.client.query_legacy(self.dataset_name, q, opts)

        self.assertIsNotNone(qr.savedQueryID)
        self.assertEqual(len(qr.matches), len(self.events))

    def test_step005_apl_query(self):
        """Test apl query"""
        # query the events we ingested in step2
        startTime = datetime.utcnow() - timedelta(minutes=2)
        endTime = datetime.utcnow()

        apl = "['%s']" % self.dataset_name
        opts = AplOptions(
            start_time=startTime,
            end_time=endTime,
            format=AplResultFormat.Legacy,
        )
        qr = self.client.query(apl, opts)

        self.assertEqual(len(qr.matches), len(self.events))

    def test_step005_wrong_query_kind(self):
        """Test wrong query kind"""
        startTime = datetime.utcnow() - timedelta(minutes=2)
        endTime = datetime.utcnow()
        opts = QueryOptions(
            streamingDuration=timedelta(seconds=60),
            nocache=True,
            saveAsKind=QueryKind.APL,
        )
        q = QueryLegacy(startTime, endTime)

        try:
            self.client.query_legacy(self.dataset_name, q, opts)
        except WrongQueryKindException:
            self.logger.info(
                "passing kind apl to query raised exception as expected"
            )
            return

        self.fail("was excepting WrongQueryKindException")

    def test_step005_complex_query(self):
        """Test complex query"""
        startTime = datetime.utcnow() - timedelta(minutes=2)
        endTime = datetime.utcnow()
        aggregations = [
            Aggregation(
                alias="event_count", op=AggregationOperation.COUNT, field="*"
            )
        ]
        q = QueryLegacy(startTime, endTime, aggregations=aggregations)
        q.groupBy = ["success", "remote_ip"]
        q.filter = Filter(FilterOperation.EQUAL, "response", 304)
        q.order = [
            Order("success", True),
            Order("remote_ip", False),
        ]
        q.virtualFields = [VirtualField("success", "response < 400")]
        q.project = [Projection("remote_ip", "ip")]

        res = self.client.query_legacy(self.dataset_name, q, QueryOptions())

        # self.assertEqual(len(self.events), res.status.rowsExamined)
        self.assertEqual(len(self.events), res.status.rowsMatched)

        if res.buckets.totals and len(res.buckets.totals):
            agg = res.buckets.totals[0].aggregations[0]
            self.assertEqual("event_count", agg.op)

    @classmethod
    def tearDownClass(cls):
        """A teardown that checks if the dataset still exists and deletes it,
        otherwise we might run into zombie datasets on failures."""
        cls.logger.info("cleaning up after TestClient...")
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
        cls.logger.info("finish cleaning up after TestClient")
