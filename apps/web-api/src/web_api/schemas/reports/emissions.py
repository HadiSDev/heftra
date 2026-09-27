"""The dashboard's emissions over a period."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from ..emissions.summary import EmissionsSpendRow, FactorSetRead
from .period import ReportPeriods


class MonthEmissions(BaseModel):
    month: date
    kg_co2e: Decimal


class SectorEmissions(BaseModel):
    code: str
    name: str
    kg_co2e: Decimal


class SpendEmissions(ReportPeriods):
    """The period's and its comparison's kg CO2e, twelve months of it, and where it came from."""

    factor_set: FactorSetRead | None = None
    kg_co2e: Decimal | None = None
    comparison_kg_co2e: Decimal | None = None
    months: list[MonthEmissions] = []
    spend: list[EmissionsSpendRow] = []
    top_sectors: list[SectorEmissions] = []
