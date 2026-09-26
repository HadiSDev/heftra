"""The estimated emissions of the vouchers Spend Lines lists."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class FactorSetRead(BaseModel):
    """The factor set every figure comes from, and how it must be credited."""

    model_config = ConfigDict(from_attributes=True)

    source: str
    version: str
    currency: str
    price_year: int
    price_basis: str
    attribution: str


class EmissionsSpendRow(BaseModel):
    """How much of one base currency's posted spend the estimate covers."""

    currency: str
    posted_spend: Decimal = Decimal("0")
    estimated_spend: Decimal = Decimal("0")


class EmissionsSummaryRead(BaseModel):
    factor_set: FactorSetRead | None = None
    kg_co2e: Decimal | None = None
    spend: list[EmissionsSpendRow] = []
    vouchers_by_status: dict[str, int] = {}
