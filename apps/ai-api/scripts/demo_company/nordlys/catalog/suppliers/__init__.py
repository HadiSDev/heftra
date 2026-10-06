"""Every supplier of the demo company, by key."""
from __future__ import annotations

from ..shapes import SupplierSpec
from . import materials, overheads, site_operations

SUPPLIERS: tuple[SupplierSpec, ...] = (
    *materials.SUPPLIERS, *site_operations.SUPPLIERS, *overheads.SUPPLIERS,
)


def by_key() -> dict[str, SupplierSpec]:
    return {spec.key: spec for spec in SUPPLIERS}
