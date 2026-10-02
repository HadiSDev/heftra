"""Keeping each line's `item_key` current, a page at a time."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import case, or_, update
from sqlmodel import Session, col, select

from web_api.db.models import Invoice, InvoiceLine
from web_api.items.keys import item_key

from .. import config


def refresh_item_keys(session: Session, company_id: str, since: datetime | None, *,
                      page_size: int | None = None) -> int:
    """Key the lines without a key, and those whose line or invoice changed after `since`.

    Commits every page; returns how many lines got a new key.
    """
    size = page_size or config.AGREEMENT_PAGE_SIZE
    stale = [col(InvoiceLine.item_key).is_(None)]
    if since is not None:
        stale += [col(InvoiceLine.changed_at) > since, col(Invoice.changed_at) > since]
    rekeyed = 0
    after = ""
    while True:
        rows = session.exec(
            select(InvoiceLine.id, InvoiceLine.item_key, InvoiceLine.item_name,
                   InvoiceLine.description, InvoiceLine.unit, InvoiceLine.spend_category_id,
                   Invoice.vendor_id)
            .join(Invoice, Invoice.id == InvoiceLine.invoice_id)
            .where(InvoiceLine.company_id == company_id, or_(*stale),
                   col(InvoiceLine.id) > after)
            .order_by(col(InvoiceLine.id))
            .limit(size)
        ).all()
        if not rows:
            return rekeyed
        changes: dict[str, str] = {}
        for line_id, current, name, description, unit, category_id, vendor_id in rows:
            key = item_key(name, description, unit, category_id, vendor_id)
            if key != current:
                changes[line_id] = key
        if changes:
            session.exec(
                update(InvoiceLine)
                .where(col(InvoiceLine.id).in_(list(changes)))
                .values(item_key=case(changes, value=InvoiceLine.id))
            )
            session.commit()
        rekeyed += len(changes)
        after = rows[-1][0]
