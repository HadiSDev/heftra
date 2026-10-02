"""Keeping a company's items stored, with what they bought in the last 12 months."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import case, func, update
from sqlmodel import Session, col, select

from web_api.db.models import Company, CompanyItem, Invoice, InvoiceLine
from web_api.fx.service import FxService
from web_api.items.window import WINDOW_DAYS
from web_api.specs.pricing import PriceNote, price_item

from .. import config
from .refresh import refresh_item_keys


def refresh_company_items(session: Session, company_id: str, *, today: date | None = None,
                          fx: FxService | None = None, page_size: int | None = None,
                          item_keys: list[str] | None = None) -> int:
    """Store each item the company bought in the last 12 months, or only those of `item_keys`:
    its text, supplier, category, spend, lines, last purchase and quantities, priced by its
    specification, which is kept. Items not bought in that time keep their row with nothing
    bought. Commits every page; returns how many items were stored."""
    refresh_item_keys(session, company_id, None)
    today = today or date.today()
    started = datetime.now(timezone.utc)
    eur_rate = company_eur_rate(session, company_id, today, fx or FxService(session))
    size = page_size or config.AGREEMENT_PAGE_SIZE
    stored = 0
    after = ""
    while True:
        rows = _grouped(session, company_id, today - timedelta(days=WINDOW_DAYS), after, size,
                        item_keys)
        if not rows:
            break
        existing = {item.item_key: item for item in session.exec(
            select(CompanyItem).where(CompanyItem.company_id == company_id,
                                      col(CompanyItem.item_key).in_([row[0] for row in rows]))
        ).all()}
        for row in rows:
            item = existing.get(row[0]) or CompanyItem(company_id=company_id, item_key=row[0])
            _fill(item, row, started)
            price_item(item, eur_rate)
            session.add(item)
        session.commit()
        stored += len(rows)
        after = rows[-1][0]
    _clear_unbought(session, company_id, started, item_keys)
    return stored


def company_eur_rate(session: Session, company_id: str, on: date,
                     fx: FxService) -> Decimal | None:
    """What one unit of the company's base currency is in EUR on a day."""
    company = session.get(Company, company_id)
    if company is None or not company.base_currency:
        return None
    if company.base_currency == "EUR":
        return Decimal(1)
    found = fx.get_rate(company.base_currency, "EUR", on)
    return Decimal(found[0]) if found else None


def _grouped(session: Session, company_id: str, since: date, after: str, size: int,
             item_keys: list[str] | None) -> list:
    stated = col(InvoiceLine.quantity) > 0
    statement = (
        select(InvoiceLine.item_key, func.min(InvoiceLine.item_name),
               func.min(InvoiceLine.description), func.min(InvoiceLine.unit),
               func.min(InvoiceLine.spend_category_id), func.min(Invoice.vendor_id),
               func.max(InvoiceLine.base_currency), func.count(),
               func.sum(InvoiceLine.base_amount), func.max(Invoice.invoice_date),
               func.sum(case((stated, InvoiceLine.quantity))),
               func.sum(case((stated, InvoiceLine.base_amount))),
               func.avg(case((stated, InvoiceLine.quantity))))
        .join(Invoice, Invoice.id == InvoiceLine.invoice_id)
        .where(InvoiceLine.company_id == company_id, col(InvoiceLine.item_key).is_not(None),
               col(InvoiceLine.item_key) > after, col(InvoiceLine.base_amount) > 0,
               Invoice.invoice_date >= since)
        .group_by(InvoiceLine.item_key)
        .order_by(InvoiceLine.item_key)
        .limit(size)
    )
    if item_keys is not None:
        statement = statement.where(col(InvoiceLine.item_key).in_(item_keys))
    return list(session.exec(statement).all())


def _fill(item: CompanyItem, row, refreshed: datetime) -> None:
    (_, name, description, unit, category_id, vendor_id, currency, lines, spend, last_on,
     line_quantity, priced_spend, order_quantity) = row
    item.item_name = name
    item.description = description
    item.unit = unit
    item.category_id = category_id
    item.vendor_id = vendor_id
    item.base_currency = currency
    item.lines = lines
    item.spend = Decimal(spend or 0)
    item.last_bought_on = last_on
    item.line_quantity = _decimal(line_quantity)
    item.priced_spend = _decimal(priced_spend)
    item.order_quantity = _decimal(order_quantity)
    item.refreshed_at = refreshed


def _decimal(value) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None


def _clear_unbought(session: Session, company_id: str, started: datetime,
                    item_keys: list[str] | None) -> None:
    statement = (
        update(CompanyItem)
        .where(CompanyItem.company_id == company_id,
               (col(CompanyItem.refreshed_at).is_(None))
               | (col(CompanyItem.refreshed_at) < started))
        .values(spend=Decimal(0), lines=0, line_quantity=None, priced_spend=None,
                order_quantity=None, quantity=None, unit_price=None, unit_price_eur=None,
                price_note=PriceNote.NOT_BOUGHT.value, refreshed_at=started)
    )
    if item_keys is not None:
        statement = statement.where(col(CompanyItem.item_key).in_(item_keys))
    session.exec(statement)
    session.commit()
