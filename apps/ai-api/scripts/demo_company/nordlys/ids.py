"""Fixed ids for every row the demo writes, so a re-run replaces its rows instead of adding more."""
from __future__ import annotations

from uuid import UUID, uuid5

NAMESPACE = UUID("6b1f3c1e-0d55-4c55-9a43-2f0c4e5d7a10")


def demo_id(kind: str, key: str) -> str:
    """The id of the demo's `kind` row named `key`; the same on every run."""
    return str(uuid5(NAMESPACE, f"nordlys-byg:{kind}:{key}"))


COMPANY_ID = demo_id("company", "nordlys-byg")
TREE_ID = demo_id("spend-tree", "nordlys-byg")
INTEGRATION_ID = demo_id("erp-integration", "mock")
