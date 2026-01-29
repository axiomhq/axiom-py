"""Async structlog contains the AsyncAxiomProcessor for structlog."""

from typing import List
import time

from .client_async import AsyncClient


class AsyncAxiomProcessor:
    """An async processor for sending structlogs to Axiom."""

    client: AsyncClient
    dataset: str
    buffer: List[object]
    interval: int
    last_run: float

    def __init__(self, client: AsyncClient, dataset: str, interval=1):
        """
        Initialize the async Axiom processor.

        Args:
            client: AsyncClient instance
            dataset: Dataset name to send logs to
            interval: Flush interval in seconds (default: 1)

        Example:
            ```python
            import structlog
            from axiom_py import AsyncClient, AsyncAxiomProcessor

            async def main():
                async with AsyncClient(token="...") as client:
                    processor = AsyncAxiomProcessor(client, "logs")

                    structlog.configure(
                        processors=[
                            structlog.processors.add_log_level,
                            processor,
                            structlog.processors.JSONRenderer(),
                        ],
                    )

                    logger = structlog.get_logger()
                    await logger.ainfo("test message")

                    # Flush remaining logs
                    await processor.flush()
            ```
        """
        self.client = client
        self.dataset = dataset
        self.buffer = []
        self.last_run = time.monotonic()
        self.interval = interval

    async def flush(self):
        """
        Asynchronously flush all logs in the buffer to Axiom.

        This should be called explicitly when you're done logging to ensure
        all buffered logs are sent.
        """
        self.last_run = time.monotonic()

        if len(self.buffer) == 0:
            return

        # Swap buffers
        local_buffer, self.buffer = self.buffer, []

        try:
            await self.client.ingest_events(self.dataset, local_buffer)
        except Exception as e:
            # If ingestion fails, log the error but don't raise
            print(f"AsyncAxiomProcessor: Failed to flush logs: {e}")
            # Put logs back in buffer to retry later
            self.buffer.extend(local_buffer)

    async def __call__(
        self, logger: object, method_name: str, event_dict: object
    ):
        """
        Process a log event from structlog.

        This method can be used as an async processor in structlog's
        configuration.

        Args:
            logger: The logger instance
            method_name: The name of the logging method called
            event_dict: The event dictionary to process

        Returns:
            The event dictionary (unchanged)
        """
        self.buffer.append(event_dict.copy())

        # Check if we should flush
        should_flush = (
            len(self.buffer) >= 1000
            or time.monotonic() - self.last_run > self.interval
        )

        if should_flush:
            await self.flush()

        return event_dict
