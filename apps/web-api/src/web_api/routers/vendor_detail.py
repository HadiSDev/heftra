"""A supplier's detail page: who it is, what the organization spent with it, and on what."""
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, nulls_last
from sqlmodel import Session, select

from web_api.db.models import Company, ErpEntry, Invoice, InvoiceLine, SpendCategory, Vendor
from web_api.vendor_spend import NET_SPEND, spend_by_vendor
from web_api.vendor_website import known_website
from ..auth.deps import TenantScope, get_session, resolve_company_ids, tenant_scope
from ..schemas import VendorCategorySpendRead, VendorDetailRead, VendorInvoiceRead

router = APIRouter(prefix="/api/v1", tags=["vendors"])

RECENT_INVOICE_LIMIT = 10
_ZERO = Decimal("0")
_CENT = Decimal("0.01")

CategoryKey = tuple[str | None, str | None, str | None]


@router.get("/vendors/{vendor_id}/detail", response_model=VendorDetailRead)
def vendor_detail(
    vendor_id: str,
    company_id: str | None = Query(default=None),
    scope: TenantScope = Depends(tenant_scope),
    session: Session = Depends(get_session),
) -> VendorDetailRead:
    """The supplier with its figures over the caller's invoices; 404 when the caller has none from it."""
    company_ids = resolve_company_ids(scope, company_id)
    vendor = session.get(Vendor, vendor_id)
    if vendor is None or not company_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    invoice_count, first_date, last_date = session.exec(
        select(func.count(Invoice.id), func.min(Invoice.invoice_date), func.max(Invoice.invoice_date))
        .where(Invoice.vendor_id == vendor_id, Invoice.company_id.in_(company_ids))
    ).one()
    if not invoice_count:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    return VendorDetailRead(
        id=vendor.id,
        name=vendor.name,
        country_code=vendor.country_code,
        vat_number=vendor.vat_number,
        description=vendor.description,
        description_source=vendor.description_source,
        website=known_website(session, vendor),
        document_country_code=_most_printed(
            session, Invoice.document_supplier_country_code, company_ids, vendor_id
        ),
        document_vat_number=_most_printed(
            session, Invoice.document_supplier_vat_number, company_ids, vendor_id
        ),
        invoice_count=invoice_count,
        first_invoice_date=first_date,
        last_invoice_date=last_date,
        spend=spend_by_vendor(session, company_ids, [vendor_id]).get(vendor_id, []),
        categories=_category_spend(session, company_ids, vendor_id),
        recent_invoices=_recent_invoices(session, company_ids, vendor_id),
    )


def _most_printed(session: Session, column, company_ids: list[str], vendor_id: str) -> str | None:
    """The value the supplier's invoices to the caller most often print in `column`."""
    return session.exec(
        select(column)
        .where(Invoice.vendor_id == vendor_id, Invoice.company_id.in_(company_ids), column.is_not(None))
        .group_by(column)
        .order_by(func.count().desc(), column)
        .limit(1)
    ).first()


def _category_spend(
    session: Session, company_ids: list[str], vendor_id: str
) -> list[VendorCategorySpendRead]:
    """The supplier's spend by category and base currency, largest first.

    Each invoice's net spend is split across its lines by their share of its lines' value, so the
    categories add up to the supplier's spend however the document printed its lines.
    """
    rows = session.exec(
        select(
            InvoiceLine.invoice_id, InvoiceLine.spend_category_id, SpendCategory.name,
            Company.base_currency, InvoiceLine.base_amount, NET_SPEND,
        )
        .join(Invoice, Invoice.id == InvoiceLine.invoice_id)
        .join(Company, Company.id == Invoice.company_id)
        .outerjoin(SpendCategory, SpendCategory.id == InvoiceLine.spend_category_id)
        .where(Invoice.vendor_id == vendor_id, Invoice.company_id.in_(company_ids))
    ).all()

    line_totals: dict[str, Decimal] = {}
    for invoice_id, _, _, _, line_amount, _ in rows:
        line_totals[invoice_id] = line_totals.get(invoice_id, _ZERO) + (line_amount or _ZERO)

    amounts: dict[CategoryKey, Decimal] = {}
    line_counts: dict[CategoryKey, int] = {}
    for invoice_id, category_id, category_name, currency, line_amount, net in rows:
        key = (category_id, category_name, currency)
        line_counts[key] = line_counts.get(key, 0) + 1
        amounts[key] = amounts.get(key, _ZERO) + _share_of_net(net, line_amount, line_totals[invoice_id])

    categories = [
        VendorCategorySpendRead(
            category_id=category_id,
            category_name=category_name,
            currency=currency,
            amount=amounts[(category_id, category_name, currency)].quantize(_CENT),
            line_count=line_count,
        )
        for (category_id, category_name, currency), line_count in line_counts.items()
    ]
    return sorted(
        categories,
        key=lambda c: (-c.amount, c.category_name is None, c.category_name or ""),
    )


def _share_of_net(net, line_amount: Decimal | None, line_total: Decimal) -> Decimal:
    """The part of an invoice's net spend one line accounts for; none when it cannot be told."""
    if net is None or line_amount is None or line_total <= 0:
        return _ZERO
    return Decimal(str(net)) * line_amount / line_total


def _recent_invoices(
    session: Session, company_ids: list[str], vendor_id: str
) -> list[VendorInvoiceRead]:
    """The supplier's latest invoices to the caller's companies, newest first."""
    rows = session.exec(
        select(Invoice, Company.name)
        .join(Company, Company.id == Invoice.company_id)
        .where(Invoice.vendor_id == vendor_id, Invoice.company_id.in_(company_ids))
        .order_by(nulls_last(Invoice.invoice_date.desc()), Invoice.created_at.desc(), Invoice.id)
        .limit(RECENT_INVOICE_LIMIT)
    ).all()
    vouchers = _voucher_numbers(session, [invoice.id for invoice, _ in rows])
    return [
        VendorInvoiceRead(
            id=invoice.id,
            invoice_number=invoice.invoice_number or invoice.document_invoice_number,
            voucher_number=vouchers.get(invoice.id),
            invoice_date=invoice.invoice_date,
            company_name=company_name,
            currency=invoice.currency,
            total=invoice.total,
            status=invoice.status,
        )
        for invoice, company_name in rows
    ]


def _voucher_numbers(session: Session, invoice_ids: list[str]) -> dict[str, str]:
    """`{invoice_id: the ERP voucher number it was posted on}`, for invoices posted on one."""
    if not invoice_ids:
        return {}
    rows = session.exec(
        select(ErpEntry.source_invoice_id, func.min(ErpEntry.voucher_number))
        .where(ErpEntry.source_invoice_id.in_(invoice_ids), ErpEntry.voucher_number.is_not(None))
        .group_by(ErpEntry.source_invoice_id)
    ).all()
    return {invoice_id: voucher_number for invoice_id, voucher_number in rows}
