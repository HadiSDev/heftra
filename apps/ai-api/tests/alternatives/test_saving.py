"""Prices per pricing unit without VAT, and the saving they give."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from ai_api.alternatives.saving import StatedPrice, saving, unit_price


def same_currency(amount, currency, on):
    return amount


def test_a_danish_webshop_price_with_vat_per_roll():
    stated = StatedPrice(Decimal("100"), "DKK", True, "DK", Decimal("8"), date(2026, 6, 1))

    price = unit_price(stated, same_currency)

    assert price == Decimal("10")
    assert saving(Decimal("11"), price, Decimal("400")).percent == Decimal("9.09")


def test_a_price_whose_vat_rate_is_unknown_is_not_used():
    stated = StatedPrice(Decimal("100"), "USD", True, None, Decimal("1"), date(2026, 6, 1))
    assert unit_price(stated, same_currency) is None


def test_a_foreign_price_is_converted():
    stated = StatedPrice(Decimal("50"), "EUR", False, "DE", Decimal("1"), date(2026, 6, 1))
    assert unit_price(stated, lambda amount, currency, on: amount * Decimal("7.46")) == \
        Decimal("373")


def test_too_small_a_saving_is_not_an_alternative():
    assert saving(Decimal("100"), Decimal("99"), Decimal("10")) is None


def test_the_yearly_saving_on_cable():
    found = saving(Decimal("3.00"), Decimal("2.40"), Decimal("1220"))
    assert (found.percent, found.yearly) == (Decimal("20.00"), Decimal("732.00"))
