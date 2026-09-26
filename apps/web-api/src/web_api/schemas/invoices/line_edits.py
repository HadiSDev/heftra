"""Corrections to invoice lines, and lines added by hand."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class InvoiceLineUpdate(BaseModel):
    """A human's correction of what a line says was bought."""

    model_config = ConfigDict(extra="forbid")

    item_name: str | None = None
    description: str | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    unit_price: Decimal | None = None
    amount: Decimal | None = None


class InvoiceLinePatch(InvoiceLineUpdate):
    """A correction to a line, which may also choose or clear its emission sector."""

    emission_sector_id: str | None = None


class InvoiceLineCreate(InvoiceLineUpdate):
    """A line a reviewer added by hand, typically splitting a stand-in."""

    sequence: int | None = None
