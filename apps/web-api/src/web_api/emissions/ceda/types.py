"""What the Open CEDA workbook holds, once read."""
from __future__ import annotations

from decimal import Decimal
from typing import NamedTuple


class WorkbookError(ValueError):
    """The workbook is not laid out as an Open CEDA release is."""


class WorkbookSector(NamedTuple):
    code: str
    name: str
    description: str | None


class CedaWorkbook(NamedTuple):
    """An Open CEDA release's factors, in the price type and currency it states."""

    version: str
    currency: str
    price_year: int
    price_type: str
    sectors: list[WorkbookSector]
    country_factors: dict[tuple[str, str], Decimal]
    region_factors: dict[tuple[str, str], Decimal]
    purchaser_ratios: dict[str, Decimal]
    country_regions: dict[str, str]
    skipped_countries: list[str]
