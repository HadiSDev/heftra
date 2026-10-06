"""Stored specifications, as the specification reader would give them."""
from __future__ import annotations

SPEC_CONFIDENCE = 0.92


def numeric(name: str, value: str, number: float, unit: str, direction: str = "more") -> dict:
    return {"name": name, "kind": "numeric", "value": value, "number": number, "unit": unit,
            "direction": direction}


def described(name: str, value: str) -> dict:
    return {"name": name, "kind": "other", "value": value}


def goods(product_type: str, name: str, pricing_unit: str, *attributes: dict,
          item_class: str = "material", units_per_line_unit: float | None = None) -> dict:
    """A material, part or finished good priced per `pricing_unit`."""
    return {"item_class": item_class, "product_type": product_type, "name": name,
            "pricing_unit": pricing_unit, "units_per_line_unit": units_per_line_unit,
            "attributes": list(attributes), "confidence": SPEC_CONFIDENCE}


def service(product_type: str, name: str) -> dict:
    """A service, fee or subscription: no alternatives are searched for it."""
    return {"item_class": "service", "product_type": product_type, "name": name,
            "pricing_unit": "piece", "units_per_line_unit": 1, "attributes": [],
            "confidence": SPEC_CONFIDENCE}
