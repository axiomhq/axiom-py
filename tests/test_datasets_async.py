"""Tests for the async datasets client."""

import pytest
import respx
import httpx
from datetime import timedelta

from axiom_py import AsyncClient


@pytest.mark.asyncio
class TestAsyncDatasetsClient:
    """Test suite for AsyncDatasetsClient."""

    @respx.mock
    async def test_get_dataset(self):
        """Test getting a dataset by ID."""
        mock_dataset = {
            "name": "test-dataset",
            "description": "Test description",
            "who": "test-user",
            "created": "2024-01-01T00:00:00Z",
        }

        respx.get("/v1/datasets/test-dataset").mock(
            return_value=httpx.Response(200, json=mock_dataset)
        )

        async with AsyncClient(
            token="test-token", url_base="http://localhost"
        ) as client:
            dataset = await client.datasets.get("test-dataset")
            assert dataset.name == "test-dataset"
            assert dataset.description == "Test description"

    @respx.mock
    async def test_create_dataset(self):
        """Test creating a new dataset."""
        mock_dataset = {
            "name": "new-dataset",
            "description": "New dataset",
            "who": "test-user",
            "created": "2024-01-01T00:00:00Z",
        }

        respx.post("/v1/datasets").mock(
            return_value=httpx.Response(200, json=mock_dataset)
        )

        async with AsyncClient(
            token="test-token", url_base="http://localhost"
        ) as client:
            dataset = await client.datasets.create(
                "new-dataset", "New dataset"
            )
            assert dataset.name == "new-dataset"
            assert dataset.description == "New dataset"

    @respx.mock
    async def test_list_datasets(self):
        """Test listing all datasets."""
        mock_datasets = [
            {
                "name": "dataset1",
                "description": "First dataset",
                "who": "test-user",
                "created": "2024-01-01T00:00:00Z",
            },
            {
                "name": "dataset2",
                "description": "Second dataset",
                "who": "test-user",
                "created": "2024-01-02T00:00:00Z",
            },
        ]

        respx.get("/v1/datasets").mock(
            return_value=httpx.Response(200, json=mock_datasets)
        )

        async with AsyncClient(
            token="test-token", url_base="http://localhost"
        ) as client:
            datasets = await client.datasets.get_list()
            assert len(datasets) == 2
            assert datasets[0].name == "dataset1"
            assert datasets[1].name == "dataset2"

    @respx.mock
    async def test_update_dataset(self):
        """Test updating a dataset."""
        mock_dataset = {
            "name": "test-dataset",
            "description": "Updated description",
            "who": "test-user",
            "created": "2024-01-01T00:00:00Z",
        }

        respx.put("/v1/datasets/test-dataset").mock(
            return_value=httpx.Response(200, json=mock_dataset)
        )

        async with AsyncClient(
            token="test-token", url_base="http://localhost"
        ) as client:
            dataset = await client.datasets.update(
                "test-dataset", "Updated description"
            )
            assert dataset.name == "test-dataset"
            assert dataset.description == "Updated description"

    @respx.mock
    async def test_delete_dataset(self):
        """Test deleting a dataset."""
        respx.delete("/v1/datasets/test-dataset").mock(
            return_value=httpx.Response(204, json={})
        )

        async with AsyncClient(
            token="test-token", url_base="http://localhost"
        ) as client:
            # Should not raise an exception
            await client.datasets.delete("test-dataset")

    @respx.mock
    async def test_trim_dataset(self):
        """Test trimming a dataset."""
        respx.post("/v1/datasets/test-dataset/trim").mock(
            return_value=httpx.Response(204, json={})
        )

        async with AsyncClient(
            token="test-token", url_base="http://localhost"
        ) as client:
            # Should not raise an exception
            await client.datasets.trim("test-dataset", timedelta(days=7))

    @respx.mock
    async def test_retry_on_error(self):
        """Test that datasets client retries on 5xx errors."""
        mock_dataset = {
            "name": "test-dataset",
            "description": "Test description",
            "who": "test-user",
            "created": "2024-01-01T00:00:00Z",
        }

        route = respx.get("/v1/datasets/test-dataset")
        route.side_effect = [
            httpx.Response(503, json={"message": "Service unavailable"}),
            httpx.Response(200, json=mock_dataset),
        ]

        async with AsyncClient(
            token="test-token", url_base="http://localhost"
        ) as client:
            dataset = await client.datasets.get("test-dataset")
            assert dataset.name == "test-dataset"

        # Verify 2 calls were made (1 retry + 1 success)
        assert route.call_count == 2
