"""Connectors' answers kept for a while and shared, since they are public."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, delete, select

from web_api.db.models import MarketplaceOffer, MarketplaceQuery

from .. import config
from .market import Market
from .offer import Offer
from .source import ConnectorFailed, OfferSource

logger = logging.getLogger("ai_api.marketplaces")

OK = "ok"
FAILED = "failed"


def cached_offers(session: Session, source: OfferSource, query: str,
                  market: Market) -> list[MarketplaceOffer]:
    """The connector's offers for the query, from an answer younger than the TTL or asked now
    and stored; raises `ConnectorFailed` when asking fails, which isn't kept. Commits."""
    now = datetime.now(timezone.utc)
    row = session.exec(select(MarketplaceQuery).where(
        MarketplaceQuery.connector == source.name, MarketplaceQuery.market == market.key,
        MarketplaceQuery.query == query)).first()
    if row is not None and row.status == OK and _aware(row.expires_at) > now:
        return list(session.exec(select(MarketplaceOffer)
                                 .where(MarketplaceOffer.query_id == row.id)).all())
    offers = _ask(source, query, market)
    row = row or MarketplaceQuery(connector=source.name, market=market.key, query=query,
                                  status=OK, expires_at=now)
    row.status = OK
    row.error = None
    row.fetched_at = now
    row.expires_at = now + timedelta(days=config.ALTERNATIVES_OFFER_TTL_DAYS)
    session.add(row)
    session.flush()
    session.exec(delete(MarketplaceOffer).where(MarketplaceOffer.query_id == row.id))
    stored = [_stored(row.id, source.name, offer, now) for offer in offers]
    session.add_all(stored)
    session.commit()
    return stored


def _ask(source: OfferSource, query: str, market: Market) -> list[Offer]:
    """The connector's answer; any error it raises is its failure."""
    try:
        return source.search(query, market)
    except ConnectorFailed:
        raise
    except Exception as error:  # noqa: BLE001
        raise ConnectorFailed(f"{source.name}: {error}") from error


def _stored(query_id: str, connector: str, offer: Offer, seen: datetime) -> MarketplaceOffer:
    return MarketplaceOffer(
        query_id=query_id, connector=connector, seller=offer.seller, url=offer.url,
        title=offer.title, price=offer.price, currency=offer.currency.upper(),
        vat_included=offer.vat_included, seller_country=offer.seller_country,
        pack_unit=offer.pack, availability=offer.availability, shipping=offer.shipping,
        description=offer.description,
        identifiers={"gtin": offer.gtin, "part_number": offer.part_number,
                     "brand": offer.brand, "model": offer.model},
        price_breaks=[{"quantity": entry.quantity, "price": str(entry.price)}
                      for entry in offer.price_breaks],
        seen_at=seen)


def _aware(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)
