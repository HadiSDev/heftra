"""Alternatives from the organization's own purchases: the same product, or a similar
specification, bought cheaper by any of its companies from any supplier."""
from __future__ import annotations

import logging
from decimal import Decimal

from sqlmodel import Session, col, select

from web_api.db.models import AlternativeSource, Company, CompanyItem, Vendor

from ... import config
from ...items.index import SimilarityUnavailable
from ...specs.index import SpecIndex
from ...specs.specification import read_spec
from .found import Found, ItemContext

logger = logging.getLogger("ai_api.alternatives")


def history_candidates(session: Session, context: ItemContext,
                       index: SpecIndex | None) -> list[Found]:
    """The organization's other items of the item's product or near its specification, with a
    price per pricing unit lower than the item's."""
    item = context.item
    ids = set(_similar(context, index))
    statement = (
        select(CompanyItem, Company.name, Company.base_currency)
        .join(Company, Company.id == CompanyItem.company_id)
        .where(Company.organization_id == context.organization_id, CompanyItem.id != item.id,
               CompanyItem.lines > 0, col(CompanyItem.unit_price).is_not(None))
    )
    if item.product_id is not None:
        statement = statement.where(col(CompanyItem.id).in_(ids)
                                    | (CompanyItem.product_id == item.product_id))
    else:
        statement = statement.where(col(CompanyItem.id).in_(ids))
    rows = session.exec(statement).all() if ids or item.product_id else []
    vendors = _vendor_names(session, {other.vendor_id for other, _, _ in rows if other.vendor_id})
    found: list[Found] = []
    for other, company_name, currency in rows:
        spec = read_spec(other.spec)
        price = _in_base(other, currency, context)
        if spec is None or price is None or price >= item.unit_price:
            continue
        found.append(Found(
            source=AlternativeSource.HISTORY, ref_key=f"item:{other.id}", name=spec.name,
            unit_price=price, spec=spec, product_id=other.product_id, vendor_id=other.vendor_id,
            origin={"supplier": vendors.get(other.vendor_id), "vendor_id": other.vendor_id,
                    "company": company_name, "company_id": other.company_id,
                    "item_id": other.id, "item_name": other.item_name,
                    "last_bought_on": other.last_bought_on.isoformat()
                    if other.last_bought_on else None}))
    return found


def _similar(context: ItemContext, index: SpecIndex | None) -> list[str]:
    if index is None:
        return []
    try:
        hits = index.search(context.spec, limit=config.ALTERNATIVES_SIMILAR,
                            threshold=config.ALTERNATIVES_SIMILARITY_MIN,
                            organization_id=context.organization_id)
    except SimilarityUnavailable as error:
        logger.warning("alternatives: the specification index is unavailable: %s", error)
        return []
    return [hit.item_id for hit in hits if hit.item_id != context.item.id]


def _in_base(other: CompanyItem, currency: str | None, context: ItemContext) -> Decimal | None:
    if currency == context.base_currency:
        return other.unit_price
    if other.unit_price_eur is None or not context.eur_rate:
        return None
    return other.unit_price_eur / context.eur_rate


def _vendor_names(session: Session, ids: set[str]) -> dict[str, str]:
    if not ids:
        return {}
    return dict(session.exec(select(Vendor.id, Vendor.name).where(col(Vendor.id).in_(ids))).all())
