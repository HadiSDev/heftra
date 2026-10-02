"""What to ask marketplaces about an item: its identifiers first, then what it is."""
from __future__ import annotations

from web_api.specs.attribute import Attribute, AttributeKind
from web_api.specs.specification import Specification


TELLING_ATTRIBUTES = 2


def search_queries(spec: Specification, limit: int) -> list[str]:
    """The item's part number (with its brand) or EAN, then its brand, name and model with its
    most telling attributes; at most `limit`."""
    queries: list[str] = []
    if spec.part_number:
        queries.append(" ".join(part for part in (spec.brand, spec.part_number) if part))
    elif spec.gtin:
        queries.append(spec.gtin)
    telling = [_stated(attribute) for attribute in spec.attributes
               if attribute.kind != AttributeKind.NUMERIC or attribute.number is not None]
    described = " ".join([*_not_in(spec.name, spec.brand), spec.name,
                          *_not_in(spec.name, spec.model), *telling[:TELLING_ATTRIBUTES]])
    queries.append(" ".join(described.split()))
    return list(dict.fromkeys(queries))[:max(1, limit)]


def _stated(attribute: Attribute) -> str:
    if attribute.kind == AttributeKind.NUMERIC and attribute.number is not None:
        return f"{attribute.number:g} {attribute.unit or ''}".strip()
    return attribute.value


def _not_in(name: str, part: str | None) -> list[str]:
    if not part or part.lower() in name.lower():
        return []
    return [part]
