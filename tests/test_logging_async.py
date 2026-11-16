"""Async logging lifecycle tests with the real client and local transport."""

import asyncio
import gzip
import json
import logging
import time

import httpx
import pytest
import respx

from axiom_py import AsyncAxiomHandler, AsyncClient


@pytest.fixture
def logging_client():
    client = AsyncClient(token="test-token", url="https://axiom.invalid")
    logger = logging.Logger("async-handler-test", logging.INFO)
    rows = []

    def accept(request):
        assert request.headers["Content-Type"] == "application/x-ndjson"
        assert request.headers["Content-Encoding"] == "gzip"
        payload = gzip.decompress(request.content)
        batch = [json.loads(line) for line in payload.splitlines()]
        rows.extend(batch)
        return httpx.Response(
            200,
            json={
                "ingested": len(batch),
                "failed": 0,
                "failures": [],
                "processedBytes": len(payload),
                "blocksCreated": 1,
                "walLength": 1,
            },
        )

    with respx.mock(assert_all_called=False, assert_all_mocked=True) as router:
        route = router.post(
            "https://axiom.invalid/v1/datasets/logs/ingest"
        ).mock(side_effect=accept)
        yield client, logger, rows, route


@pytest.mark.parametrize("outside_loop", [True, False])
def test_first_emit_starts_one_periodic_task(logging_client, outside_loop):
    client, logger, rows, route = logging_client
    handler = AsyncAxiomHandler(client, "logs") if outside_loop else None

    async def run():
        nonlocal handler
        if handler is None:
            handler = AsyncAxiomHandler(client, "logs")
        logger.addHandler(handler)
        received = asyncio.Event()
        accept = route.side_effect

        def record_delivery(request):
            response = accept(request)
            received.set()
            return response

        route.mock(side_effect=record_delivery)
        try:
            assert time.monotonic() - handler.last_flush < handler.interval
            logger.info("first")
            task = handler.flush_task
            assert task is not None
            logger.info("second")
            assert handler.flush_task is task
            assert not rows
            await asyncio.wait_for(received.wait(), 3 * handler.interval)
            assert [row["msg"] for row in rows] == ["first", "second"]
            assert not handler.buffer
            assert handler.flush_task is task
            assert not task.done()
        finally:
            logger.removeHandler(handler)
            await handler.close()
            await client.close()

    asyncio.run(run())
    assert handler.flush_task.done()


@pytest.mark.parametrize("trigger", ["threshold", "elapsed"])
def test_immediate_flush_keeps_periodic_task(logging_client, trigger):
    client, logger, rows, route = logging_client

    async def run():
        handler = AsyncAxiomHandler(client, "logs", interval=60)
        logger.addHandler(handler)
        task = handler.flush_task
        received = asyncio.Event()
        accept = route.side_effect

        def record_delivery(request):
            response = accept(request)
            received.set()
            return response

        route.mock(side_effect=record_delivery)
        try:
            count = 1000 if trigger == "threshold" else 1
            if trigger == "elapsed":
                handler.last_flush = time.monotonic() - handler.interval - 1
            for _ in range(count):
                logger.info(trigger)
            assert handler.flush_task is task
            await asyncio.wait_for(received.wait(), 3)
            assert [row["msg"] for row in rows] == [trigger] * count
            assert not handler.buffer
        finally:
            logger.removeHandler(handler)
            await handler.close()
            await client.close()

    asyncio.run(run())


def test_emit_without_running_loop_buffers_until_close(logging_client):
    client, logger, rows, _ = logging_client
    handler = AsyncAxiomHandler(client, "logs")
    logger.addHandler(handler)
    try:
        logger.info("buffered")
        assert handler._loop is None
        assert handler.flush_task is None
        assert len(handler.buffer) == 1
        assert not rows
    finally:
        logger.removeHandler(handler)

        async def close():
            await handler.close()
            await client.close()

        asyncio.run(close())
    assert [row["msg"] for row in rows] == ["buffered"]
