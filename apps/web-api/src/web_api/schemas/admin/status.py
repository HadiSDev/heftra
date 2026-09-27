"""The factor sets, their price indices and each company's coverage, for system admins."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from .coverage import SectorCoverageRow


class AdminFactorSetRead(BaseModel):
    id: str
    source: str
    version: str
    classification: str
    currency: str
    price_year: int
    price_basis: str
    attribution: str
    sectors: int
    factors: int
    imported_at: datetime
    active: bool


class AdminPriceIndexRead(BaseModel):
    """A series some factor set's currency is deflated with, and how much of it is stored."""

    series: str
    label: str
    currency: str
    months: int
    latest_month: date | None = None
    base_year: int | None = None
    base_average: Decimal | None = None


class EmissionFactorsStatusRead(BaseModel):
    sets: list[AdminFactorSetRead] = []
    price_indices: list[AdminPriceIndexRead] = []
    coverage: list[SectorCoverageRow] = []
