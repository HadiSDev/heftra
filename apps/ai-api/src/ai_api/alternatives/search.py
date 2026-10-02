"""Searching one item's alternatives across every enabled source."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlmodel import Session

from web_api.db.models import AlternativeSource, Company, CompanyItem
from web_api.fx.service import FxService
from web_api.specs.specification import read_spec

from .. import config
from ..items.stored import company_eur_rate
from ..marketplaces.market import market_for
from ..marketplaces.source import OfferSource
from ..specs.index import SpecIndex
from ..specs.reader import SpecReader
from .agreements import agreement_notes, item_bindings
from .matching.judge import Ask, PairJudge
from .matching.matcher import Candidate, match_candidates
from .saving import Convert, saving
from .sources.benchmark import benchmark_candidates
from .sources.found import Found, ItemContext
from .sources.history import history_candidates
from .sources.marketplace import ConnectorHealth, marketplace_candidates
from .store import AlternativeStore


@dataclass
class SearchTools:
    """What every item's search in a run shares."""

    ask: Ask
    reader: SpecReader
    index: SpecIndex | None
    connectors: list[OfferSource]
    fx: FxService
    today: date
    health: ConnectorHealth = field(default_factory=ConnectorHealth)


def search_item(session: Session, item: CompanyItem, tools: SearchTools) -> Counter:
    """Find the item's alternatives, replace its open ones from the sources searched and keep
    reviewed ones; returns what was found and kept per source. Commits."""
    counts: Counter = Counter()
    spec = read_spec(item.spec)
    company = session.get(Company, item.company_id)
    now = datetime.now(timezone.utc)
    item.searched_at = now
    if spec is None or item.unit_price is None or company is None:
        counts["unpriced"] += 1
        session.add(item)
        session.commit()
        return counts
    context = ItemContext(item=item, spec=spec, organization_id=company.organization_id,
                          base_currency=company.base_currency,
                          eur_rate=company_eur_rate(session, company.id, tools.today, tools.fx))
    found = history_candidates(session, context, tools.index) \
        + benchmark_candidates(session, context)
    sources = {AlternativeSource.HISTORY.value, AlternativeSource.BENCHMARK.value}
    if spec.confidence >= config.ALTERNATIVES_SPEC_MIN_CONFIDENCE:
        found += marketplace_candidates(session, context, market_for(company.country_code),
                                        tools.connectors, tools.reader, tools.health,
                                        _converter(tools.fx, company.base_currency))
        sources.add(AlternativeSource.MARKETPLACE.value)
    store = AlternativeStore(session, item, company.base_currency)
    candidates = [entry for entry in found if not store.reviewed(entry)]
    matches = match_candidates(spec, item.product_id,
                               [Candidate(entry.ref_key, entry.spec, entry.product_id)
                                for entry in candidates if entry.match is None],
                               PairJudge(session, tools.ask))
    bindings = item_bindings(session, company, item, tools.today)
    for entry in candidates:
        counts[f"{entry.source.value}_candidates"] += 1
        result = matches.get(entry.ref_key)
        match = entry.match or (result.match if result is not None else None)
        found_saving = saving(item.unit_price, entry.unit_price, item.quantity)
        if match is None or found_saving is None:
            continue
        store.put(entry, match, result.comparison if result is not None else [], found_saving,
                  agreement_notes(entry, bindings), now)
        counts[f"{entry.source.value}_alternatives"] += 1
    store.drop_unfound(sources)
    session.add(item)
    session.commit()
    return counts


def _converter(fx: FxService, base_currency: str) -> Convert:
    def convert(amount: Decimal, currency: str, on: date) -> Decimal | None:
        if currency == base_currency:
            return amount
        found = fx.get_rate(currency, base_currency, on)
        return amount * Decimal(found[0]) if found else None
    return convert
