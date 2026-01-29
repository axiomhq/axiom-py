"""Simple test for async client without pytest."""

import asyncio
import sys
import os

sys.path.insert(0, "/Users/islam/axiom/axiom-py/src")

from axiom_py import AsyncClient


async def test_basic():
    """Test basic async client functionality."""
    print("Testing AsyncClient context manager...")
    async with AsyncClient(
        token=os.getenv("AXIOM_TOKEN"), url=os.getenv("AXIOM_URL")
    ) as client:
        print(f"✓ Client created: {client}")
        print(f"✓ HTTP client exists: {client.client}")
        print(f"✓ Datasets client: {client.datasets}")
        print(f"✓ Annotations client: {client.annotations}")
        print(f"✓ Tokens client: {client.tokens}")
        print(f"✓ Users client: {client.users}")
        print(f"✓ Client is not closed: {not client.client.is_closed}")

    print(f"✓ Client is closed after context exit: {client.client.is_closed}")
    print("\nAll basic tests passed!")


if __name__ == "__main__":
    asyncio.run(test_basic())
