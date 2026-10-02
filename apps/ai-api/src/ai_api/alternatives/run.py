"""The two alternatives runs: one item on request, and a company's scan of its largest spend."""
from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone

from sqlmodel import Session, col, select

from web_api.db.models import Company, CompanyItem, SpecSource
from web_api.fx.service import FxService
from web_api.specs.pricing import price_item
from web_api.specs.specification import read_spec

from .. import config
from ..items.index import SimilarityUnavailable
from ..items.stored import company_eur_rate, refresh_company_items
from ..marketplaces.registry import enabled_connectors
from ..marketplaces.source import OfferSource
from ..specs.index import SpecEntry, SpecIndex
from ..specs.reader import SpecReader
from ..specs.refresh import apply_spec, due_for_spec, specify_items
from .matching.judge import Ask
from .search import SearchTools, search_item

logger = logging.getLogger("ai_api.alternatives")

Embed = Callable[[list[str]], list[list[float]]]


class ItemNotFound(LookupError):
    """The run names an item the company doesn't have."""


def find_alternatives(session: Session, company_id: str, item_id: str, *, ask: Ask,
                      embed_fn: Embed, fx: FxService | None = None,
                      index: SpecIndex | None = None,
                      connectors: list[OfferSource] | None = None,
                      today: date | None = None) -> dict:
    """Refresh one item's figures and search its alternatives, reading its specification first
    when it has none."""
    item = session.get(CompanyItem, item_id)
    if item is None or item.company_id != company_id:
        raise ItemNotFound(f"no item {item_id} for company {company_id}")
    tools = _tools(session, ask, embed_fn, fx, index, connectors, today)
    refresh_company_items(session, company_id, today=tools.today, fx=tools.fx,
                          item_keys=[item.item_key])
    session.refresh(item)
    summary = _prepare(session, company_id, [item], tools)
    summary.update(search_item(session, item, tools))
    return _summary(summary, tools)


def scan_alternatives(session: Session, company_id: str, *, ask: Ask, embed_fn: Embed,
                      fx: FxService | None = None, index: SpecIndex | None = None,
                      connectors: list[OfferSource] | None = None,
                      today: date | None = None) -> dict:
    """Refresh the company's items, read the specifications of up to `ALTERNATIVES_SCAN_SPECS`
    of them, and search the ones due, largest spend first, up to `ALTERNATIVES_SCAN_ITEMS`."""
    tools = _tools(session, ask, embed_fn, fx, index, connectors, today)
    refreshed = refresh_company_items(session, company_id, today=tools.today, fx=tools.fx)
    due = due_for_search(session, company_id, now=datetime.now(timezone.utc),
                         limit=config.ALTERNATIVES_SCAN_ITEMS)
    specified = due_for_spec(session, company_id, limit=config.ALTERNATIVES_SCAN_SPECS)
    summary = _prepare(session, company_id, [*due, *specified], tools)
    summary["items"] = refreshed
    for item in due:
        summary.update(search_item(session, item, tools))
    summary["searched"] = len(due)
    return _summary(summary, tools)


def due_for_search(session: Session, company_id: str, *, now: datetime,
                   limit: int) -> list[CompanyItem]:
    """Bought items not searched in `ALTERNATIVES_RESCAN_DAYS`, most spend first."""
    stale = now - timedelta(days=config.ALTERNATIVES_RESCAN_DAYS)
    return list(session.exec(
        select(CompanyItem)
        .where(CompanyItem.company_id == company_id, CompanyItem.lines > 0,
               col(CompanyItem.searched_at).is_(None) | (col(CompanyItem.searched_at) < stale))
        .order_by(col(CompanyItem.spend).desc(), CompanyItem.id)
        .limit(limit)
    ).all())


def _tools(session: Session, ask: Ask, embed_fn: Embed, fx: FxService | None,
           index: SpecIndex | None, connectors: list[OfferSource] | None,
           today: date | None) -> SearchTools:
    return SearchTools(ask=ask, reader=SpecReader(ask),
                       index=index if index is not None else SpecIndex.connect(embed_fn),
                       connectors=connectors if connectors is not None
                       else enabled_connectors(ask),
                       fx=fx or FxService(session), today=today or date.today())


def _prepare(session: Session, company_id: str, items: list[CompanyItem],
             tools: SearchTools) -> Counter:
    """Read the items' missing specifications, complete the ones a person set, and index
    them."""
    counts: Counter = Counter()
    company = session.get(Company, company_id)
    eur_rate = company_eur_rate(session, company_id, tools.today, tools.fx)
    items = list({item.id: item for item in items}.values())
    unread = due_for_spec(session, company_id, item_ids=[item.id for item in items])
    read = specify_items(session, unread, tools.reader, eur_rate)
    counts["specs_read"] += read.read
    counts["specs_failed"] += read.failed
    for item in items:
        if item.spec_source == SpecSource.HUMAN.value and item.spec_signature is None \
                and (spec := read_spec(item.spec)) is not None:
            apply_spec(session, item, spec, SpecSource.HUMAN)
            price_item(item, eur_rate)
            session.add(item)
    session.commit()
    entries = [SpecEntry(item.id, company_id, company.organization_id, item.product_id, spec)
               for item in items if (spec := read_spec(item.spec)) is not None]
    if tools.index is not None:
        try:
            counts["specs_indexed"] += tools.index.ensure(entries)
        except SimilarityUnavailable as error:
            logger.warning("alternatives: the specification index is unavailable: %s", error)
            tools.index = None
    return counts


def _summary(counts: Counter, tools: SearchTools) -> dict:
    summary = dict(counts)
    summary["similarity"] = tools.index is not None
    if tools.health.failed:
        summary["connectors_failed"] = dict(tools.health.failed)
    return summary
