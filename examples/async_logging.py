"""
Async logging example for axiom-py.

This example demonstrates how to use AsyncAxiomHandler to send
Python logs to Axiom asynchronously.
"""

import asyncio
import logging
from axiom_py import AsyncClient, AsyncAxiomHandler


async def main():
    """Main async function demonstrating async logging."""
    # Initialize the async client
    async with AsyncClient() as client:
        # Create and configure the async handler
        handler = AsyncAxiomHandler(
            client=client, dataset="logs", interval=1  # Flush every second
        )

        # Configure the root logger
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        # Log some messages
        logger.info("Application started")
        logger.debug("Debug message with details", extra={"user_id": 123})
        logger.warning("This is a warning")
        logger.error("An error occurred", extra={"error_code": "E001"})

        # Simulate some async work
        await asyncio.sleep(0.5)

        logger.info("Processing data...")
        for i in range(5):
            logger.info(f"Processing item {i}", extra={"item_id": i})
            await asyncio.sleep(0.1)

        logger.info("Application finished")

        # Important: Close the handler to flush remaining logs
        await handler.close()
        print("Logs sent to Axiom")


if __name__ == "__main__":
    asyncio.run(main())
