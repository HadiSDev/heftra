"""Alternatives from what other organizations pay: the median of their prices for the item's
product or specification, from enough organizations that none can be told apart."""
from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from sqlmodel import Session, col, select

from web_api.db.models import (
    AlternativeMatch,
    AlternativeSource,
    Company,
    CompanyItem,
    Organization,
)

from ... import config
from .found import Found, ItemContext

PRICE_PLACES = Decimal("0.000001")


@dataclass(frozen=True)
class Benchmark:
    """Prices in EUR per pricing unit, one per organization."""

    organizations: int
    median: Decimal
    lowest_quartile: Decimal


def benchmark_candidates(session: Session, context: ItemContext) -> list[Found]:
    """The benchmark of the item's product, else of its specification, when the organization
    takes part, it comes from enough other organizations and its median is lower."""
    organization = session.get(Organization, context.organization_id)
    if organization is None or not organization.price_benchmark_enabled or not context.eur_rate:
        return []
    item = context.item
    groups = []
    if item.product_id is not None:
        groups.append(("product", CompanyItem.product_id == item.product_id, item.product_id,
                       AlternativeMatch.EXACT))
    if item.spec_signature is not None:
        groups.append(("specification", CompanyItem.spec_signature == item.spec_signature,
                       item.spec_signature, AlternativeMatch.EQUIVALENT))
    for by, condition, value, match in groups:
        found = benchmark(session, condition, context.organization_id)
        if found is None:
            continue
        median = _to_base(found.median, context.eur_rate)
        if median >= item.unit_price:
            return []
        return [Found(
            source=AlternativeSource.BENCHMARK, ref_key=f"benchmark:{by}:{value}",
            name=context.spec.name, unit_price=median, match=match,
            origin={"by": by, "organizations": found.organizations,
                    "median": str(median),
                    "lowest_quartile": str(_to_base(found.lowest_quartile, context.eur_rate))})]
    return []


def benchmark(session: Session, condition, viewer_organization_id: str) -> Benchmark | None:
    """The prices organizations other than the viewer's, taking part, paid for the items
    meeting `condition`; None from fewer than `BENCHMARK_MIN_ORGANIZATIONS`."""
    rows = session.exec(
        select(Organization.id, CompanyItem.unit_price_eur, CompanyItem.quantity)
        .join(Company, Company.id == CompanyItem.company_id)
        .join(Organization, Organization.id == Company.organization_id)
        .where(condition, Organization.id != viewer_organization_id,
               Organization.price_benchmark_enabled == True,  # noqa: E712
               CompanyItem.lines > 0, col(CompanyItem.unit_price_eur).is_not(None),
               col(CompanyItem.quantity) > 0)
    ).all()
    spend: dict[str, Decimal] = defaultdict(Decimal)
    quantity: dict[str, Decimal] = defaultdict(Decimal)
    for organization_id, price, bought in rows:
        spend[organization_id] += price * bought
        quantity[organization_id] += bought
    prices = sorted(spend[organization_id] / quantity[organization_id] for organization_id in spend)
    if len(prices) < config.BENCHMARK_MIN_ORGANIZATIONS:
        return None
    return Benchmark(organizations=len(prices), median=Decimal(statistics.median(prices)),
                     lowest_quartile=Decimal(statistics.quantiles(prices, n=4,
                                                                  method="inclusive")[0]))


def _to_base(eur: Decimal, eur_rate: Decimal) -> Decimal:
    return (eur / eur_rate).quantize(PRICE_PLACES, ROUND_HALF_UP)
