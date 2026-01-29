"""
Async dataset management example for axiom-py.

This example demonstrates how to use the async client to manage
datasets: create, list, update, and delete.
"""

import asyncio
from datetime import timedelta
from axiom_py import AsyncClient


async def main():
    """Main async function demonstrating dataset management."""
    async with AsyncClient() as client:
        dataset_name = "example-dataset-async"

        # Create a new dataset
        print(f"Creating dataset: {dataset_name}")
        dataset = await client.datasets.create(
            dataset_name, "Example dataset for async operations"
        )
        print(f"Created: {dataset.name} - {dataset.description}")

        # List all datasets
        print("\nListing all datasets:")
        datasets = await client.datasets.get_list()
        for ds in datasets:
            print(f"  - {ds.name}: {ds.description}")

        # Get specific dataset
        print(f"\nGetting dataset: {dataset_name}")
        dataset = await client.datasets.get(dataset_name)
        print(f"Found: {dataset.name}")

        # Update dataset description
        print(f"\nUpdating dataset: {dataset_name}")
        dataset = await client.datasets.update(
            dataset_name, "Updated description for async example"
        )
        print(f"Updated: {dataset.name} - {dataset.description}")

        # Ingest some sample data
        print(f"\nIngesting data to {dataset_name}")
        events = [{"message": f"Event {i}", "value": i} for i in range(10)]
        result = await client.ingest_events(dataset_name, events)
        print(f"Ingested {result.ingested} events")

        # Trim dataset (remove data older than 7 days)
        print(f"\nTrimming dataset: {dataset_name}")
        await client.datasets.trim(dataset_name, timedelta(days=7))
        print("Trim operation completed")

        # Delete the dataset
        print(f"\nDeleting dataset: {dataset_name}")
        await client.datasets.delete(dataset_name)
        print("Dataset deleted")


if __name__ == "__main__":
    asyncio.run(main())
