"""Async logging contains the AsyncAxiomHandler for async logging."""

import asyncio
import time
from logging import Handler, NOTSET, getLogger, WARNING
from typing import Optional

from .client_async import AsyncClient


class AsyncAxiomHandler(Handler):
    """An async logging handler that sends logs to Axiom."""

    client: AsyncClient
    dataset: str
    buffer: list
    interval: int
    last_flush: float
    flush_task: Optional[asyncio.Task]
    _loop: Optional[asyncio.AbstractEventLoop]

    def __init__(
        self, client: AsyncClient, dataset: str, level=NOTSET, interval=1
    ):
        """
        Initialize the async Axiom handler.

        Args:
            client: AsyncClient instance
            dataset: Dataset name to send logs to
            level: Logging level (default: NOTSET)
            interval: Flush interval in seconds (default: 1)

        Example:
            ```python
            async with AsyncClient(token="...") as client:
                handler = AsyncAxiomHandler(client, "logs")
                logger = logging.getLogger()
                logger.addHandler(handler)

                logger.info("This will be sent to Axiom")

                await handler.close()
            ```
        """
        super().__init__()
        # Set urllib3 logging level to warning
        # This prevents requests library from flooding logs with debug messages
        getLogger("urllib3").setLevel(WARNING)
        getLogger("httpx").setLevel(WARNING)

        self.client = client
        self.dataset = dataset
        self.buffer = []
        self.interval = interval
        self.last_flush = time.monotonic()
        self.flush_task = None
        self._loop = None

        # Start periodic flush task
        try:
            self._loop = asyncio.get_running_loop()
            self._start_periodic_flush()
        except RuntimeError:
            # No event loop running yet, will start when emit is first called
            pass

    def _start_periodic_flush(self):
        """Start background task for periodic flushing."""
        if self.flush_task and not self.flush_task.done():
            self.flush_task.cancel()

        if self._loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                # No event loop running
                return

        self.flush_task = self._loop.create_task(self._periodic_flush())

    async def _periodic_flush(self):
        """Periodically flush buffer to Axiom."""
        try:
            while True:
                await asyncio.sleep(self.interval)
                await self.flush()
        except asyncio.CancelledError:
            # Task was cancelled, perform final flush
            await self.flush()
            raise

    def emit(self, record):
        """
        Emit sends a log to Axiom.

        This method is synchronous (required by logging.Handler), but it schedules
        async flush operations when needed.
        """
        self.buffer.append(record.__dict__)

        # Check if we need to flush
        should_flush = (
            len(self.buffer) >= 1000
            or time.monotonic() - self.last_flush > self.interval
        )

        if should_flush:
            # Ensure event loop is available
            if self._loop is None:
                try:
                    self._loop = asyncio.get_running_loop()
                except RuntimeError:
                    # No event loop running, can't flush
                    return

            # Ensure periodic flush task is running
            if self.flush_task is None or self.flush_task.done():
                self._start_periodic_flush()

            # Schedule immediate flush
            self._loop.create_task(self.flush())

    async def flush(self):
        """
        Asynchronously flush all logs in the buffer to Axiom.

        This should be called explicitly when you're done logging to ensure
        all buffered logs are sent.
        """
        self.last_flush = time.monotonic()

        if len(self.buffer) == 0:
            return

        # Swap buffers to avoid blocking new logs
        local_buffer, self.buffer = self.buffer, []

        try:
            await self.client.ingest_events(self.dataset, local_buffer)
        except Exception as e:
            # If ingestion fails, log the error but don't raise to avoid
            # breaking the logging system
            print(f"AsyncAxiomHandler: Failed to flush logs: {e}")
            # Put logs back in buffer to retry later
            self.buffer.extend(local_buffer)

    async def close(self):
        """
        Close the handler and perform final flush.

        This should be called when you're done with the handler to ensure
        all buffered logs are sent and background tasks are cleaned up.

        Example:
            ```python
            async with AsyncClient(token="...") as client:
                handler = AsyncAxiomHandler(client, "logs")
                # ... use handler ...
                await handler.close()
            ```
        """
        # Cancel periodic flush task
        if self.flush_task and not self.flush_task.done():
            self.flush_task.cancel()
            try:
                await self.flush_task
            except asyncio.CancelledError:
                pass

        # Final flush
        await self.flush()
