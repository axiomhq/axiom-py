"""Integration tests for edge-based ingestion and query."""

import asyncio
import os
import time
import unittest
from datetime import datetime, timedelta

import rfc3339

from .helpers import get_random_name
from axiom_py import Client, AplOptions, AplResultFormat, AxiomError
from axiom_py.client_async import AsyncClient
import logging


def get_edge_config():
    """Get edge configuration from environment variables.

    Returns tuple of (edge_url, edge_token, dataset_region).
    Returns (None, None, None) if edge testing is not configured.

    Note: Empty strings are treated as None since GitHub Actions sets
    undefined variables to empty strings.
    """
    edge_url = os.getenv("AXIOM_EDGE_URL") or None
    edge_token = os.getenv("AXIOM_EDGE_TOKEN") or None
    dataset_region = os.getenv("AXIOM_EDGE_DATASET_REGION") or None

    return edge_url, edge_token, dataset_region


def is_edge_configured():
    """Check if edge testing is configured."""
    edge_url, _, _ = get_edge_config()
    return edge_url is not None


class TestEdgeIntegration(unittest.TestCase):
    """Tests for edge-based ingest and query operations.

    These tests verify that edge routing works correctly when configured.
    Tests are skipped if AXIOM_EDGE_URL or AXIOM_EDGE is not set.
    """

    @classmethod
    def setUpClass(cls):
        if not is_edge_configured():
            raise unittest.SkipTest(
                "skipping edge integration tests; " "set AXIOM_EDGE_URL to run"
            )

        edge_url, edge_token, dataset_region = get_edge_config()

        # Dataset region must be set for edge tests to ensure the dataset
        # is created in the same region as the edge endpoint
        if not dataset_region:
            raise unittest.SkipTest(
                "skipping edge integration tests; "
                "AXIOM_EDGE_DATASET_REGION must be set to match edge endpoint"
            )

        org_id = os.getenv("AXIOM_ORG_ID")

        # Use dedicated edge token if provided (edge requires API token)
        # Otherwise fall back to main token
        token_for_edge = edge_token if edge_token else os.getenv("AXIOM_TOKEN")

        # Create edge client for ingest/query
        # Edge client uses edge configuration and edge token
        # Note: edge_url must be passed explicitly as Client does not
        # auto-read from environment (to avoid affecting non-edge tests)
        cls.edge_client = Client(
            token=token_for_edge,
            org_id=org_id,
            url=os.getenv("AXIOM_URL"),
            edge_url=edge_url,
        )

        # Create main API client for dataset management
        # Dataset operations always go through main API with main token
        cls.api_client = Client(
            token=os.getenv("AXIOM_TOKEN"),
            org_id=org_id,
            url=os.getenv("AXIOM_URL"),
        )

        cls.dataset_name = get_random_name()
        cls.dataset_region = dataset_region

        # Log configuration for debugging
        print(f"Edge URL: {edge_url}")
        print(f"Edge Token set: {bool(edge_token)}")
        print(f"Dataset Region: {dataset_region}")
        print(f"Dataset Name: {cls.dataset_name}")

        # Create the test dataset via main API
        # Set dataset region if configured (required for edge routing)
        cls.api_client.datasets.create(
            cls.dataset_name,
            "edge integration test dataset",
            region=dataset_region,
        )

        # Verify the dataset was created in the expected region
        # The API may ignore the region parameter on some environments
        import requests

        resp = requests.get(
            f"{os.getenv('AXIOM_URL')}/v1/datasets/{cls.dataset_name}",
            headers={
                "Authorization": f"Bearer {os.getenv('AXIOM_TOKEN')}",
                "X-Axiom-Org-Id": org_id,
            },
        )
        if resp.status_code == 200:
            actual_region = resp.json().get("region", "")
            if actual_region != dataset_region:
                # Clean up and skip - the server didn't create in expected region
                try:
                    cls.api_client.datasets.delete(cls.dataset_name)
                except Exception:
                    pass
                raise unittest.SkipTest(
                    f"skipping edge tests; dataset created in {actual_region} "
                    f"instead of {dataset_region} (server may not support "
                    "region parameter)"
                )

    @classmethod
    def tearDownClass(cls):
        """Clean up test dataset."""
        try:
            ds = cls.api_client.datasets.get(cls.dataset_name)
            if ds:
                cls.api_client.datasets.delete(cls.dataset_name)
        except AxiomError:
            pass  # Dataset doesn't exist, nothing to clean up

    def test_edge_ingest_events(self):
        """Test ingesting events via edge endpoint."""
        t = datetime.utcnow() - timedelta(minutes=1)
        time_formatted = rfc3339.format(t)

        events = [
            {"foo": "bar", "_time": time_formatted, "source": "edge_test"},
            {"baz": "qux", "_time": time_formatted, "source": "edge_test"},
        ]

        res = self.edge_client.ingest_events(
            dataset=self.dataset_name,
            events=events,
        )

        self.assertEqual(
            res.ingested,
            2,
            f"expected 2 events ingested, got {res.ingested}",
        )
        self.assertEqual(
            res.failed, 0, f"expected 0 failures, got {res.failed}"
        )

    def test_edge_query(self):
        """Test querying via edge endpoint."""
        # First ingest some data
        t = datetime.utcnow() - timedelta(minutes=1)
        time_formatted = rfc3339.format(t)

        events = [
            {"query_test": "value1", "_time": time_formatted},
            {"query_test": "value2", "_time": time_formatted},
        ]

        res = self.edge_client.ingest_events(
            dataset=self.dataset_name,
            events=events,
        )
        self.assertEqual(res.ingested, 2)

        # Query with retry - data may take time to be indexed
        start_time = datetime.utcnow() - timedelta(minutes=5)
        end_time = datetime.utcnow() + timedelta(minutes=1)

        apl = f"['{self.dataset_name}'] | where query_test != ''"
        opts = AplOptions(
            start_time=start_time,
            end_time=end_time,
            format=AplResultFormat.Legacy,
        )

        # Retry up to 10 times with 2s delay for eventual consistency
        # Schema may not be indexed yet, causing "invalid field" errors
        qr = None
        last_error = None
        for attempt in range(10):
            try:
                qr = self.edge_client.query(apl, opts)
                if len(qr.matches) >= 2:
                    break
            except AxiomError as e:
                # Field may not be indexed yet
                last_error = e
                logging.debug(f"Query attempt {attempt + 1} failed: {e}")
            time.sleep(2)

        if qr is None:
            self.fail(f"Query failed after retries: {last_error}")

        self.assertGreaterEqual(
            len(qr.matches),
            2,
            f"expected at least 2 matches, got {len(qr.matches)}",
        )

    def test_edge_ingest_and_query_roundtrip(self):
        """Test full ingest -> query roundtrip via edge."""
        unique_marker = f"roundtrip-{datetime.utcnow().timestamp()}"
        t = datetime.utcnow() - timedelta(seconds=30)
        time_formatted = rfc3339.format(t)

        # Ingest with unique marker
        events = [
            {"marker": unique_marker, "_time": time_formatted},
        ]
        res = self.edge_client.ingest_events(
            dataset=self.dataset_name,
            events=events,
        )
        self.assertEqual(res.ingested, 1)

        # Query for the unique marker
        start_time = datetime.utcnow() - timedelta(minutes=5)
        end_time = datetime.utcnow() + timedelta(minutes=1)

        apl = f"['{self.dataset_name}'] | where marker == '{unique_marker}'"
        opts = AplOptions(
            start_time=start_time,
            end_time=end_time,
            format=AplResultFormat.Legacy,
        )

        # Retry up to 10 times with 2s delay for eventual consistency
        qr = None
        last_error = None
        for attempt in range(10):
            try:
                qr = self.edge_client.query(apl, opts)
                if len(qr.matches) >= 1:
                    break
            except AxiomError as e:
                last_error = e
                logging.debug(f"Query attempt {attempt + 1} failed: {e}")
            time.sleep(2)

        if qr is None:
            self.fail(f"Query failed after retries: {last_error}")

        self.assertEqual(
            len(qr.matches),
            1,
            f"expected 1 match for marker {unique_marker}, "
            f"got {len(qr.matches)}",
        )

    def test_main_client_still_works(self):
        """Verify that main API client operations still work alongside edge.

        This ensures edge configuration doesn't break normal API operations.
        """
        # Use main API client to get dataset info
        ds = self.api_client.datasets.get(self.dataset_name)
        self.assertEqual(ds.name, self.dataset_name)


class TestEdgeURLConfiguration(unittest.TestCase):
    """Test edge_url configuration."""

    def test_edge_url_builds_correct_urls(self):
        """Test edge_url builds correct ingest and query URLs."""
        from unittest.mock import patch

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("AXIOM_URL", None)
            os.environ.pop("AXIOM_EDGE_URL", None)

            client = Client(
                token="xaat-test-token",
                org_id="test-org",
                edge_url="https://custom-edge.example.com",
            )

            self.assertEqual(
                client._edge_url, "https://custom-edge.example.com"
            )
            # Should use edge path format
            url = client._get_edge_ingest_url("my-dataset")
            self.assertEqual(
                url, "https://custom-edge.example.com/v1/ingest/my-dataset"
            )

    def test_edge_url_uses_edge_path_format(self):
        """Test that edge_url uses edge path format, not legacy."""
        from unittest.mock import patch

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("AXIOM_URL", None)
            os.environ.pop("AXIOM_EDGE_URL", None)

            client = Client(
                token="xaat-test-token",
                org_id="test-org",
                edge_url="https://eu-central-1.aws.edge.axiom.co",
            )

            url = client._get_edge_ingest_url("logs")
            self.assertEqual(
                url, "https://eu-central-1.aws.edge.axiom.co/v1/ingest/logs"
            )

            query_url = client._get_edge_query_url()
            self.assertEqual(
                query_url,
                "https://eu-central-1.aws.edge.axiom.co/v1/query/_apl",
            )


class TestAsyncEdgeIntegration(unittest.TestCase):
    """Tests for async edge-based ingest and query operations.

    These tests verify that edge routing works correctly with AsyncClient.
    Tests are skipped if AXIOM_EDGE_URL is not set.
    """

    @classmethod
    def setUpClass(cls):
        if not is_edge_configured():
            raise unittest.SkipTest(
                "skipping async edge integration tests; "
                "set AXIOM_EDGE_URL to run"
            )

        edge_url, edge_token, dataset_region = get_edge_config()

        cls.edge_url = edge_url
        cls.edge_token = edge_token or os.getenv("AXIOM_TOKEN")
        cls.org_id = os.getenv("AXIOM_ORG_ID")
        cls.dataset_region = dataset_region
        cls.dataset_name = get_random_name()

        # Create main API client for dataset management (sync)
        cls.api_client = Client(
            token=os.getenv("AXIOM_TOKEN"),
            org_id=cls.org_id,
            url=os.getenv("AXIOM_URL"),
        )

        # Log configuration for debugging
        print(f"Async Edge URL: {edge_url}")
        print(f"Async Edge Token set: {bool(edge_token)}")
        print(f"Async Dataset Region: {dataset_region}")
        print(f"Async Dataset Name: {cls.dataset_name}")

        # Create the test dataset via main API
        # Pass region if configured (optional for edge tests)
        cls.api_client.datasets.create(
            cls.dataset_name,
            "async edge integration test dataset",
            region=dataset_region,
        )

    @classmethod
    def tearDownClass(cls):
        """Clean up test dataset."""
        try:
            ds = cls.api_client.datasets.get(cls.dataset_name)
            if ds:
                cls.api_client.datasets.delete(cls.dataset_name)
        except AxiomError:
            pass

    def test_async_edge_ingest_events(self):
        """Test ingesting events via async edge endpoint."""

        async def run_test():
            async with AsyncClient(
                token=self.edge_token,
                org_id=self.org_id,
                url=os.getenv("AXIOM_URL"),
                edge_url=self.edge_url,
            ) as client:
                t = datetime.utcnow() - timedelta(minutes=1)
                time_formatted = rfc3339.format(t)

                events = [
                    {
                        "foo": "bar",
                        "_time": time_formatted,
                        "source": "async_edge_test",
                    },
                    {
                        "baz": "qux",
                        "_time": time_formatted,
                        "source": "async_edge_test",
                    },
                ]

                res = await client.ingest_events(
                    dataset=self.dataset_name,
                    events=events,
                )

                self.assertEqual(
                    res.ingested,
                    2,
                    f"expected 2 events ingested, got {res.ingested}",
                )
                self.assertEqual(
                    res.failed, 0, f"expected 0 failures, got {res.failed}"
                )

        asyncio.run(run_test())

    def test_async_edge_query(self):
        """Test querying via async edge endpoint."""

        async def run_test():
            async with AsyncClient(
                token=self.edge_token,
                org_id=self.org_id,
                url=os.getenv("AXIOM_URL"),
                edge_url=self.edge_url,
            ) as client:
                # First ingest some data
                t = datetime.utcnow() - timedelta(minutes=1)
                time_formatted = rfc3339.format(t)

                events = [
                    {"async_query_test": "value1", "_time": time_formatted},
                    {"async_query_test": "value2", "_time": time_formatted},
                ]

                res = await client.ingest_events(
                    dataset=self.dataset_name,
                    events=events,
                )
                self.assertEqual(res.ingested, 2)

                # Query with retry
                start_time = datetime.utcnow() - timedelta(minutes=5)
                end_time = datetime.utcnow() + timedelta(minutes=1)

                apl = f"['{self.dataset_name}'] | where async_query_test != ''"
                opts = AplOptions(
                    start_time=start_time,
                    end_time=end_time,
                    format=AplResultFormat.Legacy,
                )

                # Retry up to 10 times with 2s delay
                qr = None
                last_error = None
                for attempt in range(10):
                    try:
                        qr = await client.query(apl, opts)
                        if len(qr.matches) >= 2:
                            break
                    except AxiomError as e:
                        last_error = e
                        logging.debug(
                            f"Async query attempt {attempt + 1} failed: {e}"
                        )
                    await asyncio.sleep(2)

                if qr is None:
                    self.fail(
                        f"Async query failed after retries: {last_error}"
                    )

                self.assertGreaterEqual(
                    len(qr.matches),
                    2,
                    f"expected at least 2 matches, got {len(qr.matches)}",
                )

        asyncio.run(run_test())

    def test_async_edge_ingest_and_query_roundtrip(self):
        """Test full ingest -> query roundtrip via async edge."""

        async def run_test():
            async with AsyncClient(
                token=self.edge_token,
                org_id=self.org_id,
                url=os.getenv("AXIOM_URL"),
                edge_url=self.edge_url,
            ) as client:
                unique_marker = (
                    f"async-roundtrip-{datetime.utcnow().timestamp()}"
                )
                t = datetime.utcnow() - timedelta(seconds=30)
                time_formatted = rfc3339.format(t)

                # Ingest with unique marker
                events = [
                    {"marker": unique_marker, "_time": time_formatted},
                ]
                res = await client.ingest_events(
                    dataset=self.dataset_name,
                    events=events,
                )
                self.assertEqual(res.ingested, 1)

                # Query for the unique marker
                start_time = datetime.utcnow() - timedelta(minutes=5)
                end_time = datetime.utcnow() + timedelta(minutes=1)

                apl = (
                    f"['{self.dataset_name}'] "
                    f"| where marker == '{unique_marker}'"
                )
                opts = AplOptions(
                    start_time=start_time,
                    end_time=end_time,
                    format=AplResultFormat.Legacy,
                )

                # Retry up to 10 times with 2s delay
                qr = None
                last_error = None
                for attempt in range(10):
                    try:
                        qr = await client.query(apl, opts)
                        if len(qr.matches) >= 1:
                            break
                    except AxiomError as e:
                        last_error = e
                        logging.debug(
                            f"Async query attempt {attempt + 1} failed: {e}"
                        )
                    await asyncio.sleep(2)

                if qr is None:
                    self.fail(
                        f"Async query failed after retries: {last_error}"
                    )

                self.assertEqual(
                    len(qr.matches),
                    1,
                    f"expected 1 match for marker {unique_marker}, "
                    f"got {len(qr.matches)}",
                )

        asyncio.run(run_test())

    def test_async_edge_is_configured(self):
        """Test is_edge_configured() method on AsyncClient."""

        async def run_test():
            async with AsyncClient(
                token=self.edge_token,
                org_id=self.org_id,
                edge_url=self.edge_url,
            ) as client:
                self.assertTrue(client.is_edge_configured())

            async with AsyncClient(
                token=self.edge_token,
                org_id=self.org_id,
            ) as client:
                self.assertFalse(client.is_edge_configured())

        asyncio.run(run_test())


class TestAsyncEdgeURLConfiguration(unittest.TestCase):
    """Test async edge_url configuration."""

    def test_async_edge_url_builds_correct_urls(self):
        """Test async edge_url builds correct ingest and query URLs."""
        from unittest.mock import patch

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("AXIOM_URL", None)
            os.environ.pop("AXIOM_EDGE_URL", None)

            client = AsyncClient(
                token="xaat-test-token",
                org_id="test-org",
                edge_url="https://custom-edge.example.com",
            )

            self.assertEqual(
                client._edge_url, "https://custom-edge.example.com"
            )
            # Should use edge path format
            url = client._get_edge_ingest_url("my-dataset")
            self.assertEqual(
                url, "https://custom-edge.example.com/v1/ingest/my-dataset"
            )

    def test_async_edge_url_uses_edge_path_format(self):
        """Test that async edge_url uses edge path format, not legacy."""
        from unittest.mock import patch

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("AXIOM_URL", None)
            os.environ.pop("AXIOM_EDGE_URL", None)

            client = AsyncClient(
                token="xaat-test-token",
                org_id="test-org",
                edge_url="https://eu-central-1.aws.edge.axiom.co",
            )

            url = client._get_edge_ingest_url("logs")
            self.assertEqual(
                url, "https://eu-central-1.aws.edge.axiom.co/v1/ingest/logs"
            )

            query_url = client._get_edge_query_url()
            self.assertEqual(
                query_url,
                "https://eu-central-1.aws.edge.axiom.co/v1/query/_apl",
            )
