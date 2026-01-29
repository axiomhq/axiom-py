"""
Basic async example for axiom-py.

This example demonstrates basic usage of the async Axiom client for
ingesting events and querying data.
"""

import asyncio
import os
from axiom_py import AsyncClient


async def main():
    """Main async function demonstrating basic usage."""
    # Initialize client with token from environment
    # You can also pass token explicitly: AsyncClient(token="your-token")
    async with AsyncClient() as client:
        dataset_name = os.getenv("AXIOM_DATASET", "my-dataset")

        # Ingest some sample events
        print("Ingesting events...")
        events = [
            {"user": "alice", "action": "login", "status": "success"},
            {"user": "bob", "action": "purchase", "amount": 99.99},
            {"user": "charlie", "action": "logout", "status": "success"},
        ]

        result = await client.ingest_events(dataset_name, events)
        print(
            f"Ingested {result.ingested} events ({result.processed_bytes} bytes)"
        )

        # Query the data
        print("\nQuerying data...")
        query_result = await client.query(
            f"['{dataset_name}'] | where action == 'login' | limit 10"
        )
        print(f"Found {len(query_result.matches)} matches")

        # Print the matches
        for match in query_result.matches:
            print(f"  - {match}")


if __name__ == "__main__":
    asyncio.run(main())
