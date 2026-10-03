"""Keeping an item's open alternatives' savings in step with what the item now costs."""
from __future__ import annotations

from sqlmodel import Session, select

from web_api.db.models import AlternativeReviewStatus, CompanyItem, ItemAlternative

from .saving import saving


def reprice_alternatives(session: Session, item: CompanyItem) -> None:
    """Recompute the saving of each open alternative in the item's currency from the item's
    current price and quantity; one no longer cheaper enough goes. Left alone while the item
    has no price or currency."""
    if item.unit_price is None or item.base_currency is None:
        return
    open_alternatives = session.exec(select(ItemAlternative).where(
        ItemAlternative.item_id == item.id,
        ItemAlternative.review_status == AlternativeReviewStatus.OPEN.value,
        ItemAlternative.currency == item.base_currency)).all()
    for alternative in open_alternatives:
        found = saving(item.unit_price, alternative.unit_price, item.quantity)
        if found is None:
            session.delete(alternative)
            continue
        alternative.saving_percent = found.percent
        alternative.saving_yearly = found.yearly
        session.add(alternative)
