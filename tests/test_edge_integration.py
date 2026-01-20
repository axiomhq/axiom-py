"""Integration tests for edge-based ingestion and query."""

import os
import unittest
from datetime import datetime, timedelta

import rfc3339

from .helpers import get_random_name
from axiom_py import Client, AplOptions, AplResultFormat, AxiomError


def get_edge_config():
    """Get edge configuration from environment variables.

    Returns tuple of (edge_url, edge_region, edge_token, dataset_region).
    Returns (None, None, None, None) if edge testing is not configured.
    """
    edge_url = os.getenv("AXIOM_EDGE_URL")
    edge_region = os.getenv("AXIOM_EDGE_REGION")
    edge_token = os.getenv("AXIOM_EDGE_TOKEN")
    dataset_region = os.getenv("AXIOM_EDGE_DATASET_REGION")

    return edge_url, edge_region, edge_token, dataset_region


def is_edge_configured():
    """Check if edge testing is configured."""
    edge_url, edge_region, _, _ = get_edge_config()
    return edge_url is not None or edge_region is not None


class TestEdgeIntegration(unittest.TestCase):
    """Tests for edge-based ingest and query operations.

    These tests verify that edge routing works correctly when configured.
    Tests are skipped if AXIOM_EDGE_URL or AXIOM_EDGE_REGION is not set.
    """

    @classmethod
    def setUpClass(cls):
        if not is_edge_configured():
            raise unittest.SkipTest(
                "skipping edge integration tests; "
                "set AXIOM_EDGE_URL or AXIOM_EDGE_REGION to run"
            )

        edge_url, edge_region, edge_token, dataset_region = get_edge_config()

        # Use edge token if provided, otherwise fall back to main token
        token = edge_token or os.getenv("AXIOM_TOKEN")
        org_id = os.getenv("AXIOM_ORG_ID")

        # Create edge client for ingest/query
        # If edge_url is set, it takes precedence over edge_region
        if edge_url:
            cls.edge_client = Client(
                token=token,
                org_id=org_id,
                url=edge_url,
            )
        else:
            cls.edge_client = Client(
                token=token,
                org_id=org_id,
                region=edge_region,
            )

        # Create main API client for dataset management
        # Dataset operations always go through main API
        cls.api_client = Client(
            token=os.getenv("AXIOM_TOKEN"),
            org_id=org_id,
            url=os.getenv("AXIOM_URL"),
        )

        cls.dataset_name = get_random_name()
        cls.dataset_region = dataset_region

        # Create the test dataset via main API
        # TODO: Add region parameter when dataset creation supports it
        cls.api_client.datasets.create(
            cls.dataset_name, "edge integration test dataset"
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
        time = datetime.utcnow() - timedelta(minutes=1)
        time_formatted = rfc3339.format(time)

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
        time = datetime.utcnow() - timedelta(minutes=1)
        time_formatted = rfc3339.format(time)

        events = [
            {"query_test": "value1", "_time": time_formatted},
            {"query_test": "value2", "_time": time_formatted},
        ]

        res = self.edge_client.ingest_events(
            dataset=self.dataset_name,
            events=events,
        )
        self.assertEqual(res.ingested, 2)

        # Now query the data
        start_time = datetime.utcnow() - timedelta(minutes=5)
        end_time = datetime.utcnow() + timedelta(minutes=1)

        apl = f"['{self.dataset_name}'] | where query_test != ''"
        opts = AplOptions(
            start_time=start_time,
            end_time=end_time,
            format=AplResultFormat.Legacy,
        )

        qr = self.edge_client.query(apl, opts)

        self.assertGreaterEqual(
            len(qr.matches),
            2,
            f"expected at least 2 matches, got {len(qr.matches)}",
        )

    def test_edge_ingest_and_query_roundtrip(self):
        """Test full ingest -> query roundtrip via edge."""
        unique_marker = f"roundtrip-{datetime.utcnow().timestamp()}"
        time = datetime.utcnow() - timedelta(seconds=30)
        time_formatted = rfc3339.format(time)

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

        qr = self.edge_client.query(apl, opts)

        self.assertEqual(
            len(qr.matches),
            1,
            f"expected 1 match for marker {unique_marker}, got {len(qr.matches)}",
        )

    def test_main_client_still_works(self):
        """Verify that main API client operations still work alongside edge.

        This ensures edge configuration doesn't break normal API operations.
        """
        # Use main API client to get dataset info
        ds = self.api_client.datasets.get(self.dataset_name)
        self.assertEqual(ds.name, self.dataset_name)


class TestEdgeURLConfiguration(unittest.TestCase):
    """Test AXIOM_EDGE_URL takes precedence over AXIOM_EDGE_REGION."""

    def test_edge_url_precedence(self):
        """When both edge_url and region are set, edge_url should win."""
        # This is a unit test that doesn't require edge secrets
        from unittest.mock import patch

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("AXIOM_URL", None)
            os.environ.pop("AXIOM_EDGE_REGION", None)

            client = Client(
                token="test-token",
                org_id="test-org",
                url="https://custom-edge.example.com",
                region="ignored-region.axiom.co",
            )

            # url takes precedence, region should be None
            self.assertIsNone(client._region)
            self.assertEqual(client._url, "https://custom-edge.example.com")
