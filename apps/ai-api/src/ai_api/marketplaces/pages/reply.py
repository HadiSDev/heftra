"""What the LLM reads of a product page."""
from __future__ import annotations

from pydantic import BaseModel, field_validator


class PageOffer(BaseModel):
    title: str = ""
    price: str = ""
    currency: str = ""
    vat_included: bool | None = None
    pack: str | None = None
    gtin: str | None = None
    part_number: str | None = None
    brand: str | None = None
    model: str | None = None
    availability: str | None = None
    shipping: str | None = None

    @field_validator("price", mode="before")
    @classmethod
    def _price(cls, value: object) -> str:
        return "" if value is None else str(value)

    @field_validator("pack", "gtin", "part_number", "brand", "model", "availability",
                     "shipping", mode="before")
    @classmethod
    def _blank(cls, value: object) -> object:
        return None if value in ("", "null", "none", "<string>") else value


class PageOffers(BaseModel):
    offers: list[PageOffer] = []
