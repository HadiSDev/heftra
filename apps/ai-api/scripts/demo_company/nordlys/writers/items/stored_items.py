"""The company's items, stored by the app's own refresh, with the specifications a scan reads and
marked as searched, so the worker neither reads nor searches them again for a while."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlmodel import Session, select

from ai_api.items.stored import refresh_company_items
from ai_api.specs.refresh import apply_spec
from web_api.db.models import CompanyItem, ItemClass, SpecSource
from web_api.specs.pricing import price_item
from web_api.specs.specification import Specification

from ...catalog.lookup import products_by_name
from ...catalog.suppliers import SUPPLIERS
from ...ids import COMPANY_ID, demo_id

EUR_RATE = Decimal(1)
SEARCHED_BEFORE_SEEDING = timedelta(hours=1)

ItemKey = tuple[str, str]


def write_items(session: Session, today: date, now: datetime) -> dict[ItemKey, CompanyItem]:
    """Refresh the items from the lines, give each its product's specification and price, and
    return them by (supplier key, product key). Commits."""
    refresh_company_items(session, COMPANY_ID, today=today)
    products = products_by_name()
    suppliers = {demo_id("vendor", spec.key): spec.key for spec in SUPPLIERS}
    items: dict[ItemKey, CompanyItem] = {}
    stored = session.exec(select(CompanyItem).where(CompanyItem.company_id == COMPANY_ID)).all()
    for item in stored:
        product = products[item.item_name]
        apply_spec(session, item, Specification.model_validate(product.spec), SpecSource.AI)
        price_item(item, EUR_RATE)
        if item.item_class != ItemClass.SERVICE.value:
            item.searched_at = now - SEARCHED_BEFORE_SEEDING
        session.add(item)
        items[(suppliers[item.vendor_id], product.key)] = item
    session.commit()
    return items
