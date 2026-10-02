"""A candidate's price per the item's pricing unit, and what switching to it would save."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from .. import config
from .vat import without_vat

Convert = Callable[[Decimal, str, date], Decimal | None]
PRICE_PLACES = Decimal("0.000001")
MONEY = Decimal("0.01")


@dataclass(frozen=True)
class StatedPrice:
    """A price as a seller states it: for one sale unit holding `units` pricing units."""

    price: Decimal
    currency: str
    vat_included: bool
    seller_country: str | None
    units: Decimal
    seen_on: date


@dataclass(frozen=True)
class Saving:
    percent: Decimal
    yearly: Decimal | None


def unit_price(stated: StatedPrice, convert: Convert) -> Decimal | None:
    """The price per pricing unit, without VAT, in base currency; `convert` takes an amount in
    a currency on a day to base currency. None when it can't be told."""
    if stated.units <= 0:
        return None
    net = without_vat(stated.price, stated.vat_included, stated.seller_country)
    if net is None:
        return None
    converted = convert(net / stated.units, stated.currency, stated.seen_on)
    return converted.quantize(PRICE_PLACES, ROUND_HALF_UP) if converted is not None else None


def saving(item_price: Decimal, alternative_price: Decimal,
           yearly_quantity: Decimal | None) -> Saving | None:
    """What the alternative saves, in percent and over a year of the item's quantity; None when
    it saves less than `ALTERNATIVES_MIN_SAVING_PERCENT`."""
    if item_price <= 0:
        return None
    percent = (item_price - alternative_price) / item_price * 100
    if percent < Decimal(str(config.ALTERNATIVES_MIN_SAVING_PERCENT)):
        return None
    yearly = ((item_price - alternative_price) * yearly_quantity).quantize(MONEY, ROUND_HALF_UP) \
        if yearly_quantity is not None else None
    return Saving(percent.quantize(MONEY, ROUND_HALF_UP), yearly)
