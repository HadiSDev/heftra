"""What an in-scope line means for a term, by the same rules and wording as the analysis."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from ai_api import config

from ...catalog.agreements import AGREED_PRICE, DISCOUNT, PREFERRED_SUPPLIER
from ...catalog.shapes import TermSpec
from ...settings import MONEY
from .scope import ScopedLine

HUNDRED = Decimal(100)
PRICE_PLACES = Decimal("0.0001")
PERCENT_PLACES = Decimal("0.1")

OFF_CONTRACT = "off_contract"
OVERCHARGE = "overcharge"
MISSED_DISCOUNT = "missed_discount"
POTENTIAL_SAVING = "potential_saving"
COMPLIANT = "compliant"


@dataclass(frozen=True)
class Verdict:
    kind: str
    amount: Decimal
    reason: str
    expected: Decimal | None = None
    actual: Decimal | None = None


def judge(term: TermSpec, scoped: ScopedLine, supplier_name: str) -> Verdict | None:
    """The finding the line gives against the term, or None when it gives none."""
    if term.kind == PREFERRED_SUPPLIER:
        return _preferred(term, scoped, supplier_name)
    if term.kind == AGREED_PRICE:
        return _agreed_price(term, scoped)
    if term.kind == DISCOUNT:
        return _discount(term, scoped, supplier_name)
    return None


def _preferred(term: TermSpec, scoped: ScopedLine, supplier_name: str) -> Verdict | None:
    if scoped.from_supplier:
        return None
    product = scoped.line.product
    return Verdict(OFF_CONTRACT, scoped.line.amount,
                   f"{term.scope} should be bought from {supplier_name}, but was bought from "
                   f"{scoped.invoice.supplier.name}. The line is {product.name.lower()}, which "
                   f"is {term.scope.lower()}.")


def _agreed_price(term: TermSpec, scoped: ScopedLine) -> Verdict | None:
    line = scoped.line
    agreed = term.unit_price
    actual = (line.amount / line.quantity).quantize(PRICE_PLACES, ROUND_HALF_UP)
    price_text = f"{_money(actual)} against the agreed {_money(agreed)} EUR"
    tolerance = agreed * Decimal(str(config.AGREEMENT_PRICE_TOLERANCE_PCT)) / HUNDRED
    if scoped.from_supplier:
        if actual > agreed + tolerance:
            excess = line.amount * (actual - agreed) / actual
            return Verdict(OVERCHARGE, excess.quantize(MONEY, ROUND_HALF_UP),
                           f"Invoiced at {price_text}.", agreed, actual)
        return Verdict(COMPLIANT, Decimal(0), f"Invoiced at {price_text}.", agreed, actual)
    if actual > agreed:
        excess = line.amount * (actual - agreed) / actual
        return Verdict(POTENTIAL_SAVING, excess.quantize(MONEY, ROUND_HALF_UP),
                       f"Bought from {scoped.invoice.supplier.name} at {price_text}.", agreed,
                       actual)
    return None


def _discount(term: TermSpec, scoped: ScopedLine, supplier_name: str) -> Verdict:
    line = scoped.line
    agreed = term.discount_percent
    saving = (line.amount * agreed / HUNDRED).quantize(MONEY, ROUND_HALF_UP)
    if not scoped.from_supplier:
        return Verdict(POTENTIAL_SAVING, saving,
                       f"{supplier_name} gives {_percent(agreed)} on {term.scope}; this was "
                       f"bought from {scoped.invoice.supplier.name}.", agreed)
    found = Decimal(0)
    if line.discount:
        found = (line.discount / (line.amount + line.discount) * HUNDRED).quantize(PERCENT_PLACES)
    tolerance = Decimal(str(config.AGREEMENT_DISCOUNT_TOLERANCE_PCT))
    if found >= agreed - tolerance:
        return Verdict(COMPLIANT, Decimal(0),
                       f"A {_percent(found)} discount is on the invoice.", agreed, found)
    return Verdict(MISSED_DISCOUNT, saving,
                   f"The agreed {_percent(agreed)} discount isn't on the invoice "
                   f"({_percent(found)} found).", agreed, found)


def _money(value: Decimal) -> str:
    return f"{value.quantize(MONEY):,}"


def _percent(value: Decimal) -> str:
    return f"{value.normalize():f}%"
