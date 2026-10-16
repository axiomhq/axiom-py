import json
from datetime import timedelta

import httpx
import pytest
import responses
from requests_toolbelt.sessions import BaseUrlSession

from axiom_py.datasets import DatasetsClient
from axiom_py.datasets_async import AsyncDatasetsClient
from axiom_py.util import handle_json_serialization


CASES = [
    (timedelta(), "0s"),
    (timedelta(seconds=30), "30s"),
    (timedelta(days=7), "604800s"),
    (timedelta(days=7, seconds=30), "604830s"),
    (timedelta(microseconds=500000), "0.5s"),
    (timedelta(days=7, microseconds=1), "604800.000001s"),
]


@pytest.mark.parametrize("duration, expected", CASES)
def test_sync_trim_duration(duration, expected):
    url = "https://axiom.invalid/v1/datasets/test-dataset/trim"
    with BaseUrlSession(base_url="https://axiom.invalid") as session:
        with responses.RequestsMock() as mock:
            mock.add(responses.POST, url, json={}, status=200)
            DatasetsClient(session).trim("test-dataset", duration)
            assert json.loads(mock.calls[0].request.body) == {
                "maxDuration": expected
            }


@pytest.mark.parametrize("duration, expected", CASES)
async def test_async_trim_duration(duration, expected):
    bodies = []

    def handle(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json={})

    async with httpx.AsyncClient(
        base_url="https://axiom.invalid",
        transport=httpx.MockTransport(handle),
    ) as client:
        await AsyncDatasetsClient(client).trim("test-dataset", duration)
    assert bodies == [{"maxDuration": expected}]


@pytest.mark.parametrize(
    "duration, expected",
    CASES + [(timedelta(microseconds=-500000), "-0.5s")],
)
def test_json_duration(duration, expected):
    assert handle_json_serialization(duration) == expected
