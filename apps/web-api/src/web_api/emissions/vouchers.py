"""Estimate a batch of vouchers, loading what they need in a few queries."""
from __future__ import annotations

from collections.abc import Hashable, Mapping
from datetime import date
from decimal import Decimal
from typing import NamedTuple, TypeVar

from sqlmodel import Session, select

from ..db.models import Company, Invoice, InvoiceLine, Vendor
from ..fx.service import FxService
from ..vouchers.amounts import group_invoice_id, voucher_amount
from ..vouchers.dates import spent_on
from ..vouchers.rows import EntryRow
from .estimator import Estimator, RateFor
from .factors import FactorLookup, active_factor_set
from .inputs import LineInput, VoucherInput
from .results import VoucherEmissions

Key = TypeVar("Key", bound=Hashable)


class _InvoiceOrigin(NamedTuple):
    vendor_country: str | None
    printed_country: str | None


def estimate_vouchers(session: Session, groups: Mapping[Key, list[EntryRow]],
                      fx: FxService) -> dict[Key, VoucherEmissions]:
    """Each group's emissions, keyed as `groups` is. A group's postings belong to one company."""
    factor_set = active_factor_set(session)
    if factor_set is None:
        nothing = Estimator.without_factors()
        return {key: nothing for key, rows in groups.items() if rows}

    invoice_ids = {key: group_invoice_id(rows) for key, rows in groups.items()}
    wanted = {invoice_id for invoice_id in invoice_ids.values() if invoice_id}
    lines = _lines(session, wanted)
    origins = _origins(session, wanted)
    countries = _company_countries(session, {rows[0].entry.company_id for rows in groups.values()
                                             if rows})

    sector_ids = {line.sector_id for group in lines.values() for line in group if line.sector_id}
    estimator = Estimator(FactorLookup.load(session, factor_set, sector_ids),
                          _rate_for(fx, factor_set.currency))

    results: dict[Key, VoucherEmissions] = {}
    for key, rows in groups.items():
        if not rows:
            continue
        invoice_id = invoice_ids[key]
        origin = origins.get(invoice_id) if invoice_id else None
        amount, _, _, currency, unconverted = voucher_amount(rows, "base")
        results[key] = estimator.estimate(VoucherInput(
            amount=amount,
            currency=currency,
            unconverted=unconverted > 0,
            spent_on=spent_on(rows),
            supplier_country=_supplier_country(origin),
            company_country=countries.get(rows[0].entry.company_id),
            lines=lines.get(invoice_id, []) if invoice_id else [],
        ))
    return results


def _rate_for(fx: FxService, target: str) -> RateFor:
    def rate(currency: str, on: date) -> Decimal | None:
        found = fx.get_rate(currency, target, on)
        return found[0] if found is not None else None
    return rate


def _supplier_country(origin: _InvoiceOrigin | None) -> str | None:
    if origin is None:
        return None
    return origin.vendor_country or origin.printed_country


def _lines(session: Session, invoice_ids: set[str]) -> dict[str, list[LineInput]]:
    if not invoice_ids:
        return {}
    rows = session.exec(
        select(InvoiceLine.invoice_id, InvoiceLine.id, InvoiceLine.base_amount,
               InvoiceLine.emission_sector_id)
        .where(InvoiceLine.invoice_id.in_(invoice_ids))  # type: ignore[attr-defined]
        .order_by(InvoiceLine.invoice_id, InvoiceLine.sequence, InvoiceLine.id)
    ).all()
    by_invoice: dict[str, list[LineInput]] = {}
    for invoice_id, line_id, base_amount, sector_id in rows:
        by_invoice.setdefault(invoice_id, []).append(LineInput(line_id, base_amount, sector_id))
    return by_invoice


def _origins(session: Session, invoice_ids: set[str]) -> dict[str, _InvoiceOrigin]:
    if not invoice_ids:
        return {}
    rows = session.exec(
        select(Invoice.id, Vendor.country_code, Invoice.document_supplier_country_code)
        .outerjoin(Vendor, Vendor.id == Invoice.vendor_id)
        .where(Invoice.id.in_(invoice_ids))  # type: ignore[attr-defined]
    ).all()
    return {invoice_id: _InvoiceOrigin(vendor, printed) for invoice_id, vendor, printed in rows}


def _company_countries(session: Session, company_ids: set[str]) -> dict[str, str | None]:
    if not company_ids:
        return {}
    return dict(session.exec(
        select(Company.id, Company.country_code)
        .where(Company.id.in_(company_ids))  # type: ignore[attr-defined]
    ).all())
