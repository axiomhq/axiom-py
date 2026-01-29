"""Tests for the async Axiom client."""

import pytest
import respx
import httpx
import os
from datetime import datetime

from axiom_py import (
    AsyncClient,
    IngestOptions,
    AplOptions,
    AplResultFormat,
)


@pytest.mark.asyncio
class TestAsyncClient:
    """Test suite for AsyncClient."""

    @respx.mock
    async def test_context_manager(self):
        """Test that context manager properly manages client lifecycle."""
        async with AsyncClient(
            token=os.getenv("AXIOM_TOKEN"), url=os.getenv("AXIOM_URL")
        ) as client:
            assert client.client is not None
            assert not client.client.is_closed

        # After exiting context, client should be closed
        assert client.client.is_closed

    @respx.mock
    async def test_ingest_events(self):
        """Test async event ingestion."""
        mock_response = {
            "ingested": 2,
            "failed": 0,
            "failures": [],
            "processedBytes": 100,
            "blocksCreated": 1,
            "walLength": 1,
        }

        respx.post("/v1/datasets/test-dataset/ingest").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with AsyncClient(
            token="test-token", url="http://localhost"
        ) as client:
            result = await client.ingest_events(
                "test-dataset", [{"field": "value1"}, {"field": "value2"}]
            )
            assert result.ingested == 2
            assert result.failed == 0
            assert result.processed_bytes == 100

    @respx.mock
    async def test_ingest_with_options(self):
        """Test ingestion with custom options."""
        mock_response = {
            "ingested": 1,
            "failed": 0,
            "failures": [],
            "processedBytes": 50,
            "blocksCreated": 1,
            "walLength": 1,
        }

        respx.post("/v1/datasets/test-dataset/ingest").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with AsyncClient(
            token="test-token", url="http://localhost"
        ) as client:
            opts = IngestOptions(
                timestamp_field="_time", timestamp_format=None
            )
            result = await client.ingest_events(
                "test-dataset", [{"field": "value"}], opts
            )
            assert result.ingested == 1

    @respx.mock
    async def test_query(self):
        """Test async APL query."""
        mock_response = {
            "status": {
                "elapsedTime": 100,
                "blocksExamined": 1,
                "rowsExamined": 100,
                "rowsMatched": 1,
                "numGroups": 0,
                "isPartial": False,
                "minCursor": "0",
                "maxCursor": "100",
            },
            "matches": [
                {
                    "_time": "2024-01-01T00:00:00Z",
                    "_sysTime": "2024-01-01T00:00:00Z",
                    "_rowId": "row-1",
                    "data": {"field": "value", "count": 1},
                }
            ],
            "buckets": {"series": [], "totals": []},
        }

        respx.post("/v1/datasets/_apl").mock(
            return_value=httpx.Response(
                200,
                json=mock_response,
                headers={"X-Axiom-History-Query-Id": "query-123"},
            )
        )

        async with AsyncClient(
            token="test-token", url="http://localhost"
        ) as client:
            result = await client.query("['test-dataset'] | limit 100")
            assert len(result.matches) == 1
            assert result.matches[0].data["field"] == "value"
            assert result.savedQueryID == "query-123"

    @respx.mock
    async def test_query_with_options(self):
        """Test APL query with options."""
        mock_response = {
            "status": {
                "elapsedTime": 50,
                "blocksExamined": 1,
                "rowsExamined": 50,
                "rowsMatched": 0,
                "numGroups": 0,
                "isPartial": False,
                "minCursor": "0",
                "maxCursor": "100",
            },
            "matches": [],
            "buckets": {"series": [], "totals": []},
        }

        respx.post("/v1/datasets/_apl").mock(
            return_value=httpx.Response(
                200,
                json=mock_response,
                headers={"X-Axiom-History-Query-Id": "query-456"},
            )
        )

        async with AsyncClient(
            token="test-token", url="http://localhost"
        ) as client:
            opts = AplOptions(
                start_time=datetime(2024, 1, 1),
                end_time=datetime(2024, 1, 2),
                format=AplResultFormat.Legacy,
                limit=50,
            )
            result = await client.query("['test-dataset']", opts)
            assert result.savedQueryID == "query-456"

    @respx.mock
    async def test_retry_on_5xx(self):
        """Test that client retries on 5xx errors."""
        url = "/v1/datasets/test-dataset/ingest"

        # First two calls return 500, third succeeds
        mock_response = {
            "ingested": 1,
            "failed": 0,
            "failures": [],
            "processedBytes": 50,
            "blocksCreated": 1,
            "walLength": 1,
        }

        route = respx.post(url)
        route.side_effect = [
            httpx.Response(500, json={"message": "Server error"}),
            httpx.Response(502, json={"message": "Bad gateway"}),
            httpx.Response(200, json=mock_response),
        ]

        async with AsyncClient(
            token="test-token", url="http://localhost"
        ) as client:
            result = await client.ingest_events(
                "test-dataset", [{"field": "value"}]
            )
            assert result.ingested == 1

        # Verify 3 calls were made (2 retries + 1 success)
        assert route.call_count == 3

    @respx.mock
    async def test_error_handling(self):
        """Test that client properly handles API errors."""
        respx.post("/v1/datasets/test-dataset/ingest").mock(
            return_value=httpx.Response(
                400,
                json={"message": "Bad request", "error": "Invalid payload"},
            )
        )

        async with AsyncClient(
            token="test-token", url="http://localhost"
        ) as client:
            with pytest.raises(Exception) as exc_info:
                await client.ingest_events(
                    "test-dataset", [{"field": "value"}]
                )
            assert "400" in str(exc_info.value) or "Bad request" in str(
                exc_info.value
            )

    @respx.mock
    async def test_environment_variables(self, monkeypatch):
        """Test that client uses environment variables."""
        monkeypatch.setenv("AXIOM_TOKEN", "env-token")
        monkeypatch.setenv("AXIOM_ORG_ID", "env-org")

        async with AsyncClient(url="http://localhost") as client:
            # Check that headers were set correctly
            assert (
                client.client.headers.get("Authorization")
                == "Bearer env-token"
            )
            assert client.client.headers.get("X-Axiom-Org-Id") == "env-org"
