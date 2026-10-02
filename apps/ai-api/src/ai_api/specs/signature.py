"""A specification's signature: the same for items that are the same thing by their attributes,
so organizations' prices for it can be pooled."""
from __future__ import annotations

import hashlib
import json

from .attribute import Attribute, AttributeKind
from .specification import Specification


def signature(spec: Specification) -> str:
    """A hash of the class, pricing unit, product type and key attributes, normalised."""
    payload = [spec.item_class.value, spec.pricing_unit.value, _words(spec.product_type),
               sorted(_attribute(attribute) for attribute in spec.attributes)]
    return hashlib.sha256(json.dumps(payload).encode()).hexdigest()


def _attribute(attribute: Attribute) -> str:
    if attribute.kind == AttributeKind.NUMERIC and attribute.number is not None:
        value = f"{attribute.number:g} {_words(attribute.unit)}"
    elif attribute.kind == AttributeKind.TIERED:
        value = " ".join(_words(part) for part in (attribute.family, attribute.tier,
                                                   attribute.generation))
    else:
        value = _words(attribute.value)
    return f"{attribute.name}={value.strip()}"


def _words(text: str | None) -> str:
    return " ".join((text or "").lower().split())
