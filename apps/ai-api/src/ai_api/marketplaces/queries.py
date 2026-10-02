"""What to ask marketplaces about an item: its identifiers first, then what it is."""
from __future__ import annotations

from ..specs.attribute import AttributeKind
from ..specs.specification import Specification

TELLING_ATTRIBUTES = 2


def search_queries(spec: Specification, limit: int) -> list[str]:
    """The item's part number (with its brand) or EAN, then its name with its most telling
    attributes; at most `limit`."""
    queries: list[str] = []
    if spec.part_number:
        queries.append(" ".join(part for part in (spec.brand, spec.part_number) if part))
    elif spec.gtin:
        queries.append(spec.gtin)
    telling = [attribute.value for attribute in spec.attributes
               if attribute.kind != AttributeKind.NUMERIC or attribute.number is not None]
    described = " ".join([spec.brand or "", spec.model or spec.name,
                          *telling[:TELLING_ATTRIBUTES]])
    queries.append(" ".join(described.split()))
    return list(dict.fromkeys(queries))[:max(1, limit)]
