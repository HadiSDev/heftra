"""A company's items, grouped from its keyed lines in the database, most spend first."""
from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, or_
from sqlmodel import Session, col, select

from web_api.db.models import Invoice, InvoiceLine, Vendor

from .item import Item

KEY_CHUNK = 500


def company_items(session: Session, company_id: str, *, start: date | None = None,
                  end: date | None = None, category_ids: Iterable[str] | None = None,
                  keys: Iterable[str] | None = None, limit: int | None = None) -> list[Item]:
    """The items with positive lines in the dates, optionally only in categories or by key."""
    if keys is None:
        return _query(session, company_id, start, end, category_ids, None, limit)
    wanted = list(keys)
    found: list[Item] = []
    for begin in range(0, len(wanted), KEY_CHUNK):
        found += _query(session, company_id, start, end, category_ids,
                        wanted[begin:begin + KEY_CHUNK], None)
    found.sort(key=lambda item: item.spend, reverse=True)
    return found[:limit] if limit is not None else found


def changed_item_keys(session: Session, company_id: str, since: datetime, *,
                      start: date | None = None, end: date | None = None) -> set[str]:
    """The items of lines that changed, or whose invoice changed, after `since`."""
    statement = (
        select(InvoiceLine.item_key).distinct()
        .join(Invoice, Invoice.id == InvoiceLine.invoice_id)
        .where(InvoiceLine.company_id == company_id, col(InvoiceLine.item_key).is_not(None),
               or_(col(InvoiceLine.changed_at) > since, col(Invoice.changed_at) > since))
    )
    if start is not None:
        statement = statement.where(Invoice.invoice_date >= start)
    if end is not None:
        statement = statement.where(Invoice.invoice_date <= end)
    return set(session.exec(statement).all())


def _query(session: Session, company_id: str, start: date | None, end: date | None,
           category_ids: Iterable[str] | None, keys: list[str] | None,
           limit: int | None) -> list[Item]:
    spend = func.sum(InvoiceLine.base_amount)
    statement = (
        select(InvoiceLine.item_key, func.min(InvoiceLine.item_name),
               func.min(InvoiceLine.description), func.min(InvoiceLine.unit),
               func.min(InvoiceLine.spend_category_id), func.min(InvoiceLine.level_1),
               func.min(InvoiceLine.level_2), func.min(InvoiceLine.level_3),
               func.min(InvoiceLine.level_4), func.min(Invoice.vendor_id), func.min(Vendor.name),
               func.count(), spend, func.avg(InvoiceLine.unit_price),
               func.min(Invoice.invoice_date), func.max(Invoice.invoice_date))
        .join(Invoice, Invoice.id == InvoiceLine.invoice_id)
        .outerjoin(Vendor, Vendor.id == Invoice.vendor_id)
        .where(InvoiceLine.company_id == company_id, col(InvoiceLine.item_key).is_not(None),
               col(InvoiceLine.base_amount) > 0)
        .group_by(InvoiceLine.item_key)
        .order_by(spend.desc(), InvoiceLine.item_key)
    )
    if start is not None:
        statement = statement.where(Invoice.invoice_date >= start)
    if end is not None:
        statement = statement.where(Invoice.invoice_date <= end)
    if category_ids is not None:
        statement = statement.where(col(InvoiceLine.spend_category_id).in_(list(category_ids)))
    if keys is not None:
        statement = statement.where(col(InvoiceLine.item_key).in_(keys))
    if limit is not None:
        statement = statement.limit(limit)
    return [_item(row) for row in session.exec(statement).all()]


def _item(row) -> Item:
    (key, name, description, unit, category_id, level_1, level_2, level_3, level_4, vendor_id,
     vendor_name, lines, spend, unit_price, first_on, last_on) = row
    return Item(
        key=key, item_name=name, description=description, unit=unit, category_id=category_id,
        category_path=tuple(level for level in (level_1, level_2, level_3, level_4) if level),
        vendor_id=vendor_id, vendor_name=vendor_name, lines=lines,
        spend=Decimal(spend or 0),
        unit_price=Decimal(str(unit_price)).quantize(Decimal("0.01"))
        if unit_price is not None else None,
        first_on=first_on, last_on=last_on,
    )
