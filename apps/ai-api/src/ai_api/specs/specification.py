"""An item's specification, as stored on it."""
from __future__ import annotations

import hashlib
import json

from pydantic import BaseModel, Field, ValidationError, field_validator

from web_api.db.models import ItemClass, PricingUnit

from .attribute import Attribute

SPEC_VERSION = 1


class Specification(BaseModel):
    """What an item is: its class and type, its identifiers, its key attributes, and the unit it
    is priced in, with how many of them one unit of the line holds."""

    item_class: ItemClass
    product_type: str
    name: str
    brand: str | None = None
    model: str | None = None
    part_number: str | None = None
    gtin: str | None = None
    attributes: list[Attribute] = Field(default_factory=list)
    pricing_unit: PricingUnit
    units_per_line_unit: float | None = None
    confidence: float = 0.0

    @field_validator("brand", "model", "part_number", "gtin", mode="before")
    @classmethod
    def _blank(cls, value: object) -> object:
        return None if value in ("", "null", "none", "n/a") else value

    @field_validator("units_per_line_unit", mode="before")
    @classmethod
    def _positive(cls, value: object) -> object:
        if value in (None, ""):
            return None
        return value if float(value) > 0 else None

    def attribute(self, name: str) -> Attribute | None:
        return next((attribute for attribute in self.attributes if attribute.name == name), None)

    def stored(self) -> dict:
        return self.model_dump(mode="json")

    @property
    def digest(self) -> str:
        """A hash of what the specification says, for caching comparisons of it."""
        payload = self.model_dump(mode="json", exclude={"confidence"})
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    @property
    def text(self) -> str:
        """The specification as one line of text, for similarity search."""
        attributes = ", ".join(f"{attribute.name.replace('_', ' ')} {attribute.value}"
                               for attribute in self.attributes)
        parts = [self.product_type, self.name, attributes, f"per {self.pricing_unit.value}"]
        return " — ".join(part for part in parts if part)


def read_spec(stored: dict | None) -> Specification | None:
    """A stored specification, or None when there is none or it no longer reads."""
    if not stored:
        return None
    try:
        return Specification.model_validate(stored)
    except ValidationError:
        return None
