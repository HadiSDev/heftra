"""Writing a service product in one call."""
from __future__ import annotations

from ..shapes import ProductSpec
from ..specs import service


def service_product(key: str, name: str, description: str, unit: str | None, leaf: str,
                    sector: str, kind: str) -> ProductSpec:
    """A service, whose specification only names the kind of service it is."""
    return ProductSpec(key, name, description, unit, leaf, sector, service(kind, name))
