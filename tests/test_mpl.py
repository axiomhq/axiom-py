"""Tests for MPL (Metrics Processing Language) query support."""

import asyncio
import os
import unittest
from datetime import datetime, timedelta, timezone

import httpx
import respx
import responses
import ujson

from axiom_py import (
    Client,
    EdgeResolutionError,
    MplOptions,
    MplResult,
    PersonalTokenNotSupportedForEdgeError,
)
from axiom_py.client_async import AsyncClient


AXIOM_URL = os.getenv("AXIOM_URL") or "https://api.axiom.co"
EDGE_URL = "https://us-east-1.aws.edge.axiom.co"

_MPL_RESPONSE = {
    "metadata": {"group_keys": ["method"]},
    "series": [
        {
            "metric": "http.server.duration",
            "tags": {"method": "GET"},
            "start": 1700000000,
            "resolution": 300,
            "data": [1.5, 2.3, None, 4.1],
            "summary": 2.6,
        }
    ],
}


def _make_client(**kwargs):
    return Client(token="xaat-test-token", org_id="test-org", **kwargs)


class TestEdgeMplUrl(unittest.TestCase):
    """Unit tests for _get_edge_mpl_url."""

    def test_from_edge_param(self):
        client = _make_client(edge="us-east-1.aws.edge.axiom.co")
        self.assertEqual(
            client._get_edge_mpl_url(),
            "https://us-east-1.aws.edge.axiom.co/v1/query/_mpl",
        )

    def test_from_edge_url_param(self):
        client = _make_client(edge_url=EDGE_URL)
        self.assertEqual(
            client._get_edge_mpl_url(),
            f"{EDGE_URL}/v1/query/_mpl",
        )

    def test_none_when_not_configured(self):
        client = _make_client(url=AXIOM_URL)
        self.assertIsNone(client._get_edge_mpl_url())

    def test_edge_url_with_custom_path_used_as_is(self):
        client = _make_client(edge_url="http://localhost:3400/my-custom-mpl")
        self.assertEqual(
            client._get_edge_mpl_url(),
            "http://localhost:3400/my-custom-mpl",
        )

    def test_async_from_edge_param(self):
        client = AsyncClient(
            token="xaat-test-token",
            org_id="test-org",
            edge="us-east-1.aws.edge.axiom.co",
        )
        self.assertEqual(
            client._get_edge_mpl_url(),
            "https://us-east-1.aws.edge.axiom.co/v1/query/_mpl",
        )


class TestMplQuery(unittest.TestCase):
    """Unit tests for Client.mpl_query."""

    def setUp(self):
        self.client = _make_client(url=AXIOM_URL, edge_url=EDGE_URL)
        self.mpl = (
            "`my-metrics`:`http.server.duration` " "| align to 5m using avg"
        )
        self.opts = MplOptions(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
        )

    @responses.activate
    def test_queries_edge_endpoint(self):
        responses.add(
            responses.POST,
            f"{EDGE_URL}/v1/query/_mpl",
            json=_MPL_RESPONSE,
            headers={"X-Axiom-History-Query-Id": "q-123"},
        )

        result = self.client.mpl_query(self.mpl, self.opts)

        self.assertIsInstance(result, MplResult)
        self.assertEqual(len(result.series), 1)
        self.assertEqual(result.series[0].metric, "http.server.duration")
        self.assertEqual(result.series[0].tags, {"method": "GET"})
        self.assertEqual(result.series[0].data, [1.5, 2.3, None, 4.1])
        self.assertEqual(result.series[0].summary, 2.6)
        self.assertEqual(result.metadata.group_keys, ["method"])
        self.assertEqual(result.savedQueryID, "q-123")

    @responses.activate
    def test_request_body_and_format_param(self):
        responses.add(
            responses.POST, f"{EDGE_URL}/v1/query/_mpl", json=_MPL_RESPONSE
        )

        self.client.mpl_query(self.mpl, self.opts)

        call = responses.calls[0]
        body = ujson.loads(call.request.body)
        self.assertEqual(body["mpl"], self.mpl)
        self.assertEqual(body["startTime"], "2024-01-01T00:00:00.000000Z")
        self.assertEqual(body["endTime"], "2024-01-02T00:00:00.000000Z")
        self.assertIn("format=metrics-v2", call.request.url)

    @responses.activate
    def test_aware_datetimes_serialized_as_rfc3339_utc(self):
        responses.add(
            responses.POST, f"{EDGE_URL}/v1/query/_mpl", json=_MPL_RESPONSE
        )
        opts = MplOptions(
            start_time=datetime(
                2024,
                1,
                1,
                5,
                30,
                tzinfo=timezone(timedelta(hours=5, minutes=30)),
            ),
            end_time=datetime(
                2024,
                1,
                2,
                5,
                30,
                tzinfo=timezone(timedelta(hours=5, minutes=30)),
            ),
        )
        self.client.mpl_query(self.mpl, opts)

        body = ujson.loads(responses.calls[0].request.body)
        self.assertEqual(body["startTime"], "2024-01-01T00:00:00.000000Z")
        self.assertEqual(body["endTime"], "2024-01-02T00:00:00.000000Z")
        self.assertNotIn("+00:00Z", body["startTime"])

    @responses.activate
    def test_nocache_param_forwarded(self):
        responses.add(
            responses.POST, f"{EDGE_URL}/v1/query/_mpl", json=_MPL_RESPONSE
        )
        opts = MplOptions(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            nocache=True,
        )
        self.client.mpl_query(self.mpl, opts)

        self.assertIn("nocache=true", responses.calls[0].request.url)

    @responses.activate
    def test_params_forwarded_in_body(self):
        responses.add(
            responses.POST, f"{EDGE_URL}/v1/query/_mpl", json=_MPL_RESPONSE
        )
        opts = MplOptions(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            params={"env": "prod"},
        )
        self.client.mpl_query(self.mpl, opts)

        body = ujson.loads(responses.calls[0].request.body)
        self.assertEqual(body["params"], {"env": "prod"})

    @responses.activate
    def test_query_options_forwarded_in_body(self):
        responses.add(
            responses.POST, f"{EDGE_URL}/v1/query/_mpl", json=_MPL_RESPONSE
        )
        opts = MplOptions(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            query_options={"quickRange": "last-1h"},
        )
        self.client.mpl_query(self.mpl, opts)

        body = ujson.loads(responses.calls[0].request.body)
        self.assertEqual(body["queryOptions"], {"quickRange": "last-1h"})

    @responses.activate
    def test_optional_mpl_fields_omitted_when_unset(self):
        responses.add(
            responses.POST, f"{EDGE_URL}/v1/query/_mpl", json=_MPL_RESPONSE
        )
        opts = MplOptions(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
        )
        self.client.mpl_query(self.mpl, opts)

        body = ujson.loads(responses.calls[0].request.body)
        self.assertNotIn("params", body)
        self.assertNotIn("queryOptions", body)

    def test_raises_when_edge_not_configured(self):
        client = _make_client(url=AXIOM_URL)
        with self.assertRaises(EdgeResolutionError) as ctx:
            client.mpl_query(self.mpl, self.opts)
        self.assertIn("edge_url or edge", str(ctx.exception))

    def test_personal_token_rejected(self):
        client = Client(
            token="xapt-personal-token",
            org_id="test-org",
            edge_url=EDGE_URL,
        )
        with self.assertRaises(PersonalTokenNotSupportedForEdgeError):
            client.mpl_query(self.mpl, self.opts)

    def test_missing_edge_checked_before_personal_token(self):
        client = Client(
            token="xapt-personal-token",
            org_id="test-org",
            url=AXIOM_URL,
        )
        with self.assertRaises(EdgeResolutionError):
            client.mpl_query(self.mpl, self.opts)

    @responses.activate
    def test_raises_on_malformed_mpl_response(self):
        responses.add(
            responses.POST,
            f"{EDGE_URL}/v1/query/_mpl",
            json={"series": []},
        )
        with self.assertRaises(Exception):
            self.client.mpl_query(self.mpl, self.opts)


class TestAsyncMplQuery(unittest.TestCase):
    """Unit tests for AsyncClient.mpl_query."""

    def setUp(self):
        self.mpl = (
            "`my-metrics`:`http.server.duration` " "| align to 5m using avg"
        )
        self.opts = MplOptions(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
        )

    def test_queries_edge_endpoint(self):
        with respx.mock:
            respx.post(f"{EDGE_URL}/v1/query/_mpl").mock(
                return_value=httpx.Response(
                    200,
                    json=_MPL_RESPONSE,
                    headers={"X-Axiom-History-Query-Id": "q-async-1"},
                )
            )

            async def run():
                async with AsyncClient(
                    token="xaat-test-token",
                    org_id="test-org",
                    edge_url=EDGE_URL,
                ) as client:
                    return await client.mpl_query(self.mpl, self.opts)

            result = asyncio.run(run())

        self.assertIsInstance(result, MplResult)
        self.assertEqual(len(result.series), 1)
        self.assertEqual(result.series[0].metric, "http.server.duration")
        self.assertEqual(result.savedQueryID, "q-async-1")

    def test_query_with_options_forwards_body_and_query_params(self):
        with respx.mock:
            route = respx.post(f"{EDGE_URL}/v1/query/_mpl").mock(
                return_value=httpx.Response(200, json=_MPL_RESPONSE)
            )

            async def run():
                async with AsyncClient(
                    token="xaat-test-token",
                    org_id="test-org",
                    edge_url=EDGE_URL,
                ) as client:
                    opts = MplOptions(
                        start_time=datetime(2024, 1, 1),
                        end_time=datetime(2024, 1, 2),
                        params={"env": "prod"},
                        query_options={"quickRange": "last-1h"},
                        nocache=True,
                    )
                    await client.mpl_query(self.mpl, opts)

            asyncio.run(run())

        self.assertEqual(route.call_count, 1)
        request = route.calls.last.request
        self.assertIn("format=metrics-v2", str(request.url))
        self.assertIn("nocache=true", str(request.url))
        body = request.read().decode("utf-8")
        self.assertIn('"params":{"env":"prod"}', body)
        self.assertIn('"queryOptions":{"quickRange":"last-1h"}', body)

    def test_raises_when_edge_not_configured(self):
        async def run():
            async with AsyncClient(
                token="xaat-test-token", org_id="test-org"
            ) as client:
                await client.mpl_query(self.mpl, self.opts)

        with self.assertRaises(EdgeResolutionError):
            asyncio.run(run())

    def test_personal_token_rejected(self):
        async def run():
            async with AsyncClient(
                token="xapt-personal-token",
                org_id="test-org",
                edge_url=EDGE_URL,
            ) as client:
                await client.mpl_query(self.mpl, self.opts)

        with self.assertRaises(PersonalTokenNotSupportedForEdgeError):
            asyncio.run(run())

    def test_missing_edge_checked_before_personal_token(self):
        async def run():
            async with AsyncClient(
                token="xapt-personal-token",
                org_id="test-org",
                url=AXIOM_URL,
            ) as client:
                await client.mpl_query(self.mpl, self.opts)

        with self.assertRaises(EdgeResolutionError):
            asyncio.run(run())


class TestMplIntegration(unittest.TestCase):
    """Integration test for mpl_query against a live Axiom environment.

    Requires AXIOM_METRICS_DATASET and AXIOM_EDGE_URL to be set.
    """

    @classmethod
    def setUpClass(cls):
        cls.dataset = os.getenv("AXIOM_METRICS_DATASET") or None
        cls.edge_url = os.getenv("AXIOM_EDGE_URL") or None
        if not cls.dataset or not cls.edge_url:
            raise unittest.SkipTest(
                "skipping MPL integration test; "
                "set AXIOM_METRICS_DATASET and AXIOM_EDGE_URL to run"
            )
        cls.client = Client(
            token=os.getenv("AXIOM_TOKEN"),
            org_id=os.getenv("AXIOM_ORG_ID"),
            url=os.getenv("AXIOM_URL"),
            edge_url=cls.edge_url,
        )

    def test_mpl_query_returns_result(self):
        end = datetime.now(timezone.utc)
        start = end - timedelta(hours=1)
        mpl = f"`{self.dataset}`:`*` | align to 5m using avg"
        result = self.client.mpl_query(
            mpl, MplOptions(start_time=start, end_time=end)
        )
        self.assertIsInstance(result, MplResult)
        self.assertIsInstance(result.series, list)

    def test_async_mpl_query_returns_result(self):
        async def run():
            async with AsyncClient(
                token=os.getenv("AXIOM_TOKEN"),
                org_id=os.getenv("AXIOM_ORG_ID"),
                url=os.getenv("AXIOM_URL"),
                edge_url=self.edge_url,
            ) as client:
                end = datetime.now(timezone.utc)
                start = end - timedelta(hours=1)
                mpl = f"`{self.dataset}`:`*` | align to 5m using avg"
                return await client.mpl_query(
                    mpl, MplOptions(start_time=start, end_time=end)
                )

        result = asyncio.run(run())
        self.assertIsInstance(result, MplResult)
