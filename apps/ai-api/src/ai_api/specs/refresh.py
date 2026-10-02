"""Giving items their specifications: those without one, or read by an older version."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from sqlmodel import Session, col, select

from web_api.db.models import CompanyItem, SpecSource, SpendCategory, Vendor

from .. import config
from ..items.pricing import price_item
from .products import link_product
from .prompt import ItemText
from .reader import SpecReader
from .signature import signature
from .specification import SPEC_VERSION, Specification


@dataclass
class SpecCounts:
    read: int = 0
    failed: int = 0


def spec_hash(item: CompanyItem) -> str:
    """What a specification was read from: the item's text, which its key digests, and the
    reader's version."""
    return f"{SPEC_VERSION}:{item.item_key}"


def due_for_spec(session: Session, company_id: str, *, item_ids: Iterable[str] | None = None,
                 limit: int | None = None) -> list[CompanyItem]:
    """Bought items without a specification, or with one an older reader read, that a person
    hasn't set and that haven't failed too often; most spend first."""
    statement = (
        select(CompanyItem)
        .where(CompanyItem.company_id == company_id, CompanyItem.lines > 0,
               col(CompanyItem.spec_source).is_distinct_from(SpecSource.HUMAN.value),
               CompanyItem.spec_failures < config.ALTERNATIVES_SPEC_MAX_FAILURES,
               col(CompanyItem.spec_text_hash).is_(None)
               | ~col(CompanyItem.spec_text_hash).startswith(f"{SPEC_VERSION}:"))
        .order_by(col(CompanyItem.spend).desc(), CompanyItem.id)
    )
    if item_ids is not None:
        statement = statement.where(col(CompanyItem.id).in_(list(item_ids)))
    if limit is not None:
        statement = statement.limit(limit)
    return list(session.exec(statement).all())


def specify_items(session: Session, items: list[CompanyItem], reader: SpecReader,
                  eur_rate: Decimal | None) -> SpecCounts:
    """Read the items' specifications, link them to their products and price them; an item
    that can't be read counts a failure, to be tried again later. Commits."""
    counts = SpecCounts()
    if not items:
        return counts
    texts = _texts(session, items)
    read = reader.read({item.id: texts[item.id] for item in items})
    for item in items:
        spec = read.get(item.id)
        if spec is None:
            item.spec_failures += 1
            counts.failed += 1
        else:
            apply_spec(session, item, spec, SpecSource.AI)
            counts.read += 1
        price_item(item, eur_rate)
        session.add(item)
    session.commit()
    return counts


def apply_spec(session: Session, item: CompanyItem, spec: Specification,
               source: SpecSource) -> None:
    """Store a specification on the item with its signature and product; the caller prices and
    commits."""
    product = link_product(session, spec)
    item.spec = spec.stored()
    item.spec_source = source.value
    item.spec_text_hash = spec_hash(item)
    item.spec_failures = 0
    item.spec_signature = signature(spec)
    item.product_id = product.id if product is not None else None


def _texts(session: Session, items: list[CompanyItem]) -> dict[str, ItemText]:
    category_ids = {item.category_id for item in items if item.category_id}
    vendor_ids = {item.vendor_id for item in items if item.vendor_id}
    categories = {category.id: category for category in session.exec(
        select(SpendCategory).where(col(SpendCategory.id).in_(category_ids)))} \
        if category_ids else {}
    vendors = dict(session.exec(select(Vendor.id, Vendor.name)
                                .where(col(Vendor.id).in_(vendor_ids))).all()) \
        if vendor_ids else {}
    return {item.id: ItemText(item_name=item.item_name, description=item.description,
                              unit=item.unit, category=_path(categories.get(item.category_id)),
                              supplier=vendors.get(item.vendor_id))
            for item in items}


def _path(category: SpendCategory | None) -> str | None:
    if category is None:
        return None
    levels = [category.level_1, category.level_2, category.level_3, category.level_4]
    return " / ".join(level for level in levels if level) or category.name
