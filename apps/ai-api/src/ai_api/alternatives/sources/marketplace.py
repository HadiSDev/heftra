"""Alternatives from marketplace connectors: offers read into specifications, priced at the
item's usual order quantity."""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from decimal import Decimal
from urllib.parse import urlparse

from sqlmodel import Session

from web_api.db.models import AlternativeSource, MarketplaceOffer

from ... import config
from ...marketplaces.cache import cached_offers
from ...marketplaces.market import Market
from ...marketplaces.queries import search_queries
from ...marketplaces.source import ConnectorFailed, OfferSource
from ...specs.prompt import ItemText
from ...specs.reader import SpecReader
from ...specs.specification import read_spec
from ..saving import Convert, StatedPrice, unit_price
from .found import Found, ItemContext

logger = logging.getLogger("ai_api.alternatives")


@dataclass
class ConnectorHealth:
    """The connectors that failed in a run, skipped for the rest of it."""

    failed: dict[str, str] = field(default_factory=dict)

    def usable(self, source: OfferSource) -> bool:
        return source.name not in self.failed

    def fail(self, source: OfferSource, error: str) -> None:
        logger.warning("alternatives: connector %s failed and is skipped: %s", source.name, error)
        self.failed[source.name] = error


def marketplace_candidates(session: Session, context: ItemContext, market: Market | None,
                           connectors: list[OfferSource], reader: SpecReader,
                           health: ConnectorHealth, convert: Convert) -> list[Found]:
    """The offers the connectors find for the item in its market that are cheaper per pricing
    unit; none without a market."""
    if market is None:
        return []
    offers = _offers(session, context, market, connectors, health)
    _read_specs(session, [offer for offer in offers if offer.spec is None], reader)
    found: list[Found] = []
    for offer in offers:
        candidate = _found(context, market, offer, convert)
        if candidate is not None:
            found.append(candidate)
    return found


def _offers(session: Session, context: ItemContext, market: Market,
            connectors: list[OfferSource], health: ConnectorHealth) -> list[MarketplaceOffer]:
    queries = search_queries(context.spec, config.ALTERNATIVES_QUERIES_PER_ITEM)
    offers: dict[str, MarketplaceOffer] = {}
    for source in connectors:
        for query in queries:
            if not health.usable(source):
                break
            try:
                for offer in cached_offers(session, source, query, market):
                    offers[offer.id] = offer
            except ConnectorFailed as error:
                session.rollback()
                health.fail(source, str(error))
    return list(offers.values())


def _read_specs(session: Session, offers: list[MarketplaceOffer], reader: SpecReader) -> None:
    """Read each offer as a specification, keeping an empty one when it can't be read so it
    isn't asked again. Commits."""
    if not offers:
        return
    read = reader.read({offer.id: ItemText(item_name=offer.title, description=offer.description,
                                           unit=offer.pack_unit or "piece", category=None,
                                           supplier=offer.seller)
                        for offer in offers})
    for offer in offers:
        spec = read.get(offer.id)
        offer.spec = spec.stored() if spec is not None else {}
        if spec is not None and spec.units_per_line_unit is not None:
            offer.pack_quantity = Decimal(str(spec.units_per_line_unit))
        session.add(offer)
    session.commit()


def _found(context: ItemContext, market: Market, offer: MarketplaceOffer,
           convert: Convert) -> Found | None:
    spec = read_spec(offer.spec)
    if spec is None or spec.units_per_line_unit is None:
        return None
    stated = StatedPrice(price=_price_at(offer, context.item.order_quantity),
                         currency=offer.currency, vat_included=offer.vat_included,
                         seller_country=offer.seller_country or market.country,
                         units=Decimal(str(spec.units_per_line_unit)),
                         seen_on=offer.seen_at.date())
    price = unit_price(stated, convert)
    if price is None or price >= context.item.unit_price:
        return None
    return Found(
        source=AlternativeSource.MARKETPLACE, ref_key=f"offer:{offer.connector}:{offer.url}",
        name=offer.title, unit_price=price, spec=spec, seller_host=urlparse(offer.url).hostname,
        origin={"connector": offer.connector, "seller": offer.seller, "url": offer.url,
                "title": offer.title, "seen_at": offer.seen_at.isoformat(),
                "availability": offer.availability, "shipping": offer.shipping})


def _price_at(offer: MarketplaceOffer, order_quantity: Decimal | None) -> Decimal:
    """The price of one sale unit when buying the item's usual quantity."""
    wanted = math.ceil(order_quantity) if order_quantity else 1
    breaks = sorted((int(entry["quantity"]), Decimal(entry["price"]))
                    for entry in offer.price_breaks)
    applicable = [price for quantity, price in breaks if quantity <= wanted]
    return applicable[-1] if applicable else offer.price
