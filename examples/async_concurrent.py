"""
Concurrent operations example for axiom-py async client.

This example demonstrates how to use asyncio.gather() to perform
multiple operations concurrently for better performance.
"""

import asyncio
import time
from axiom_py import AsyncClient


async def ingest_to_dataset(client: AsyncClient, dataset: str, count: int):
    """Ingest events to a specific dataset."""
    events = [{"index": i, "dataset": dataset} for i in range(count)]
    result = await client.ingest_events(dataset, events)
    print(f"Ingested {result.ingested} events to {dataset}")
    return result


async def query_dataset(client: AsyncClient, dataset: str):
    """Query a specific dataset."""
    result = await client.query(f"['{dataset}'] | limit 10")
    print(f"Queried {dataset}: found {len(result.matches)} matches")
    return result


async def main():
    """Main async function demonstrating concurrent operations."""
    async with AsyncClient() as client:
        print("=== Concurrent Ingestion Example ===")
        start_time = time.time()

        # Ingest to multiple datasets concurrently
        datasets = ["dataset1", "dataset2", "dataset3"]
        await asyncio.gather(
            *[
                ingest_to_dataset(client, dataset, 100)
                for dataset in datasets
            ]
        )

        elapsed = time.time() - start_time
        print(f"Completed concurrent ingestion in {elapsed:.2f} seconds\n")

        print("=== Concurrent Query Example ===")
        start_time = time.time()

        # Query multiple datasets concurrently
        await asyncio.gather(
            *[query_dataset(client, dataset) for dataset in datasets]
        )

        elapsed = time.time() - start_time
        print(f"Completed concurrent queries in {elapsed:.2f} seconds\n")

        print("=== Mixed Operations Example ===")
        start_time = time.time()

        # Mix ingestion and queries concurrently
        await asyncio.gather(
            ingest_to_dataset(client, "dataset1", 50),
            query_dataset(client, "dataset2"),
            ingest_to_dataset(client, "dataset3", 50),
            query_dataset(client, "dataset1"),
        )

        elapsed = time.time() - start_time
        print(
            f"Completed mixed concurrent operations in {elapsed:.2f} seconds"
        )


if __name__ == "__main__":
    asyncio.run(main())
