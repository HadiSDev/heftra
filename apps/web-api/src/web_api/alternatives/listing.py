"""The items with open alternatives, best yearly saving first."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, nulls_last
from sqlmodel import Session, col, select

from ..db.models import (
    AlternativeMatch,
    AlternativeReviewStatus,
    AlternativeSource,
    CompanyItem,
    ItemAlternative,
    ItemClass,
)
from ..schemas.alternatives import AlternativeRead, AlternativesPage, ItemSummary
from ..specs.specification import read_spec
from .reads import alternative_reads, vendor_names


@dataclass(frozen=True)
class AlternativeFilters:
    source: AlternativeSource | None = None
    match: AlternativeMatch | None = None
    item_class: ItemClass | None = None


def list_items(session: Session, company_ids: list[str], filters: AlternativeFilters,
               page: int, page_size: int) -> AlternativesPage:
    """The companies' items with an open alternative passing the filters, each with its best
    one; the page totals their best savings when they share a currency."""
    conditions = _open(company_ids, filters)
    best = (select(ItemAlternative.item_id, func.max(ItemAlternative.saving_yearly).label("best"),
                   func.count().label("found"))
            .where(*conditions).group_by(ItemAlternative.item_id).subquery())
    statement = select(CompanyItem, best.c.found).join(best, best.c.item_id == CompanyItem.id)
    if filters.item_class is not None:
        statement = statement.where(CompanyItem.item_class == filters.item_class.value)

    listed = statement.with_only_columns(CompanyItem.base_currency, best.c.best).subquery()
    total, saving, currencies, currency = session.exec(
        select(func.count(), func.sum(listed.c.best),
               func.count(func.distinct(listed.c.base_currency)),
               func.max(listed.c.base_currency))
    ).one()

    rows = session.exec(statement.order_by(nulls_last(best.c.best.desc()), CompanyItem.id)
                        .offset((page - 1) * page_size).limit(page_size)).all()
    items = [item for item, _ in rows]
    best_of = _best_alternatives(session, [item.id for item in items], conditions)
    vendors = vendor_names(session, {item.vendor_id for item in items if item.vendor_id})
    return AlternativesPage(
        items=[_summary(item, found, best_of.get(item.id), vendors) for item, found in rows],
        page=page, page_size=page_size, total=total,
        total_saving=Decimal(saving) if saving is not None and currencies == 1 else None,
        currency=currency if currencies == 1 else None)


def _open(company_ids: list[str], filters: AlternativeFilters) -> list:
    conditions = [col(ItemAlternative.company_id).in_(company_ids),
                  ItemAlternative.review_status == AlternativeReviewStatus.OPEN.value]
    if filters.source is not None:
        conditions.append(ItemAlternative.source == filters.source.value)
    if filters.match is not None:
        conditions.append(ItemAlternative.match == filters.match.value)
    return conditions


def _best_alternatives(session: Session, item_ids: list[str],
                       conditions: list) -> dict[str, AlternativeRead]:
    """Each item's open alternative with the largest yearly saving."""
    if not item_ids:
        return {}
    found = session.exec(select(ItemAlternative).where(
        *conditions, col(ItemAlternative.item_id).in_(item_ids))).all()
    best: dict[str, ItemAlternative] = {}
    for alternative in found:
        current = best.get(alternative.item_id)
        if current is None or (alternative.saving_yearly or 0) > (current.saving_yearly or 0):
            best[alternative.item_id] = alternative
    reads = alternative_reads(session, best.values())
    return {read.item_id: read for read in reads}


def _summary(item: CompanyItem, found: int, best: AlternativeRead | None,
             vendors: dict[str, str]) -> ItemSummary:
    spec = read_spec(item.spec)
    return ItemSummary(
        id=item.id, company_id=item.company_id,
        name=spec.name if spec else (item.item_name or ""),
        supplier_name=vendors.get(item.vendor_id), item_class=item.item_class,
        pricing_unit=spec.pricing_unit.value if spec else None, unit_price=item.unit_price,
        quantity=item.quantity, currency=item.base_currency, alternatives=found, best=best)
