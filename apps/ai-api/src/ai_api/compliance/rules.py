"""What a judged in-scope line means for each kind of term, worked out in code."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from web_api.db.models import AgreementScopeJudgement, AgreementTerm, AgreementTermKind, FindingKind

from .. import config
from .drafts import FindingDraft
from .lines import AnalysedLine

MONEY = Decimal("0.01")
HUNDRED = Decimal(100)

ConvertPrice = Callable[[Decimal, str | None, str | None, date | None], Decimal | None]


@dataclass(frozen=True)
class TermContext:
    """A confirmed term with what its findings need to say."""

    term: AgreementTerm
    supplier_name: str
    currency: str | None


def evaluate(context: TermContext, line: AnalysedLine, judgement: AgreementScopeJudgement,
             from_supplier: bool, *, convert: ConvertPrice,
             invoice_discount: Decimal | None) -> list[FindingDraft]:
    """The findings one in-scope line gives against one term."""
    kind = context.term.kind
    if kind == AgreementTermKind.PREFERRED_SUPPLIER.value:
        return [_preferred(context, line, judgement, from_supplier)]
    if kind == AgreementTermKind.AGREED_PRICE.value:
        return _agreed_price(context, line, judgement, from_supplier, convert)
    if kind == AgreementTermKind.DISCOUNT.value:
        return [_discount(context, line, judgement, from_supplier, invoice_discount)]
    if kind == AgreementTermKind.VOLUME_COMMITMENT.value and from_supplier:
        return [_draft(context, line, judgement, FindingKind.COMPLIANT, Decimal(0), True,
                       "Counts towards the commitment.")]
    return []


def _preferred(context: TermContext, line: AnalysedLine, judgement: AgreementScopeJudgement,
               from_supplier: bool) -> FindingDraft:
    if from_supplier:
        return _draft(context, line, judgement, FindingKind.COMPLIANT, Decimal(0), True,
                      f"Bought from {context.supplier_name}.")
    condition = f" ({context.term.conditions})" if context.term.conditions else ""
    reason = (f"{context.term.scope} should be bought from {context.supplier_name}{condition}, "
              f"but was bought from {line.vendor_name or 'another supplier'}. {judgement.reason}")
    return _draft(context, line, judgement, FindingKind.OFF_CONTRACT, line.base_amount, False,
                  reason)


def _agreed_price(context: TermContext, line: AnalysedLine, judgement: AgreementScopeJudgement,
                  from_supplier: bool, convert: ConvertPrice) -> list[FindingDraft]:
    term = context.term
    if not judgement.same_item or term.unit_price is None:
        return []
    actual = None
    paid = _paid_unit_price(line)
    if judgement.units_comparable is not False and paid is not None:
        actual = convert(paid, line.currency, context.currency, line.spent_on)
    if actual is None or actual <= 0:
        if not from_supplier:
            return []
        return [_draft(context, line, judgement, FindingKind.PRICE_UNVERIFIABLE, Decimal(0), True,
                       f"The line's price can't be compared with the agreed price per "
                       f"{term.unit or 'unit'}.", expected=term.unit_price)]
    agreed = term.unit_price
    excess_share = (actual - agreed) / actual
    tolerance = agreed * Decimal(str(config.AGREEMENT_PRICE_TOLERANCE_PCT)) / HUNDRED
    price_text = f"{_price(actual)} against the agreed {_price(agreed)} {context.currency or ''}"
    if from_supplier:
        if actual > agreed + tolerance:
            return [_draft(context, line, judgement, FindingKind.OVERCHARGE,
                           line.base_amount * excess_share, True,
                           f"Invoiced at {price_text.rstrip()}.", expected=agreed, actual=actual)]
        return [_draft(context, line, judgement, FindingKind.COMPLIANT, Decimal(0), True,
                       f"Invoiced at {price_text.rstrip()}.", expected=agreed, actual=actual)]
    if actual > agreed:
        return [_draft(context, line, judgement, FindingKind.POTENTIAL_SAVING,
                       line.base_amount * excess_share, False,
                       f"Bought from {line.vendor_name or 'another supplier'} at "
                       f"{price_text.rstrip()}.", expected=agreed, actual=actual)]
    return []


def _paid_unit_price(line: AnalysedLine) -> Decimal | None:
    """What one unit cost after the line's discounts, falling back to its listed unit price."""
    if line.amount is not None and line.quantity:
        return line.amount / line.quantity
    return line.unit_price


def _discount(context: TermContext, line: AnalysedLine, judgement: AgreementScopeJudgement,
              from_supplier: bool, invoice_discount: Decimal | None) -> FindingDraft:
    agreed = context.term.discount_percent or Decimal(0)
    saving = line.base_amount * agreed / HUNDRED
    if not from_supplier:
        return _draft(context, line, judgement, FindingKind.POTENTIAL_SAVING, saving, False,
                      f"{context.supplier_name} gives {_percent(agreed)} on "
                      f"{context.term.scope}; this was bought from "
                      f"{line.vendor_name or 'another supplier'}.", expected=agreed)
    found = max(_line_discount(line), invoice_discount or Decimal(0)) * HUNDRED
    tolerance = Decimal(str(config.AGREEMENT_DISCOUNT_TOLERANCE_PCT))
    if found >= agreed - tolerance:
        return _draft(context, line, judgement, FindingKind.COMPLIANT, Decimal(0), True,
                      f"A {_percent(found)} discount is on the invoice.", expected=agreed,
                      actual=found)
    return _draft(context, line, judgement, FindingKind.MISSED_DISCOUNT, saving, True,
                  f"The agreed {_percent(agreed)} discount isn't on the invoice "
                  f"({_percent(found)} found).", expected=agreed, actual=found)


def _line_discount(line: AnalysedLine) -> Decimal:
    """The share taken off the line, by its discount or by its price against its amount."""
    if line.amount is None or line.amount <= 0:
        return Decimal(0)
    if line.discount is not None and line.discount > 0:
        return line.discount / (line.amount + line.discount)
    if line.quantity and line.unit_price:
        listed = line.quantity * line.unit_price
        if listed > line.amount:
            return (listed - line.amount) / listed
    return Decimal(0)


def _draft(context: TermContext, line: AnalysedLine, judgement: AgreementScopeJudgement,
           kind: FindingKind, amount: Decimal, from_supplier: bool, reason: str, *,
           expected: Decimal | None = None, actual: Decimal | None = None) -> FindingDraft:
    return FindingDraft(
        term_id=context.term.id, line=line, kind=kind, amount=amount.quantize(MONEY),
        reason=reason.strip(), from_supplier=from_supplier, confidence=judgement.confidence,
        expected=expected, actual=actual.quantize(Decimal("0.0001")) if actual is not None
        else None,
    )


def _price(value: Decimal) -> str:
    return f"{value.quantize(MONEY):,}"


def _percent(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.1')).normalize():f}%"
