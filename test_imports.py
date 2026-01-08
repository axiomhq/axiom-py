"""Quick test to verify async imports work correctly."""

# Test sync imports (should already work)
from axiom_py import Client, Dataset, Annotation

# Test async imports (new)
from axiom_py import (
    AsyncClient,
    AsyncDatasetsClient,
    AsyncAnnotationsClient,
    AsyncTokensClient,
    AsyncUsersClient,
    AsyncAxiomHandler,
    AsyncAxiomProcessor,
)

# Test internal modules
from axiom_py._http_client import get_common_headers, async_retry
from axiom_py._error_handling import check_response_error

print("✓ All imports successful!")
print(f"✓ AsyncClient available: {AsyncClient}")
print(f"✓ AsyncDatasetsClient available: {AsyncDatasetsClient}")
print(f"✓ AsyncAnnotationsClient available: {AsyncAnnotationsClient}")
print(f"✓ AsyncTokensClient available: {AsyncTokensClient}")
print(f"✓ AsyncUsersClient available: {AsyncUsersClient}")
print(f"✓ AsyncAxiomHandler available: {AsyncAxiomHandler}")
print(f"✓ AsyncAxiomProcessor available: {AsyncAxiomProcessor}")
print("\nAll async classes are properly exported!")
