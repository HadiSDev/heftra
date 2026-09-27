"""What the model is asked to return for an agreement's header and its terms."""
from __future__ import annotations

from pydantic import BaseModel, field_validator

from ..documents.numbers import parse_amount


class ReadHeader(BaseModel):
    title: str | None = None
    reference: str | None = None
    supplier_name: str | None = None
    supplier_vat_number: str | None = None
    supplier_country_code: str | None = None
    supplier_website: str | None = None
    customer_name: str | None = None
    starts_on: str | None = None
    ends_on: str | None = None
    currency: str | None = None
    summary: str | None = None


class ReadTier(BaseModel):
    threshold: float | None = None
    rebate_percent: float | None = None

    @field_validator("threshold", "rebate_percent", mode="before")
    @classmethod
    def _amount(cls, value: object) -> float | None:
        return parse_amount(value)


class ReadTerm(BaseModel):
    kind: str = ""
    scope: str = ""
    conditions: str | None = None
    item: str | None = None
    unit: str | None = None
    unit_price: float | None = None
    discount_percent: float | None = None
    commitment_amount: float | None = None
    commitment_period: str | None = None
    tiers: list[ReadTier] = []
    currency: str | None = None
    quote: str = ""
    page: int | None = None
    confidence: float | None = None

    @field_validator("kind", "scope", "quote", mode="before")
    @classmethod
    def _required_text(cls, value: object) -> object:
        return "" if value is None else value

    @field_validator("tiers", mode="before")
    @classmethod
    def _tiers(cls, value: object) -> object:
        return [] if value is None else value

    @field_validator("unit_price", "discount_percent", "commitment_amount", "confidence",
                     mode="before")
    @classmethod
    def _amount(cls, value: object) -> float | None:
        return parse_amount(value)

    @field_validator("page", mode="before")
    @classmethod
    def _page(cls, value: object) -> int | None:
        amount = parse_amount(value)
        return int(amount) if amount is not None else None


class ReadTerms(BaseModel):
    terms: list[ReadTerm] = []
