"""A term as the reader drafts it, checked against the page it quotes."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from web_api.db.models import AgreementTermKind

from ..documents.numbers import normalize_numbers
from .models import ReadTerm
from .pages import AgreementPage

MIN_QUOTE_CHARS = 12
_SPACES = re.compile(r"\s+")
_EDGES = " \t\n\"'“”‘’«».,;:"
_KINDS = {kind.value for kind in AgreementTermKind}
_PERIODS = {"month", "quarter", "year", "agreement"}


@dataclass
class DraftTerm:
    """A term ready to be stored as a draft, with every quote it was read from."""

    kind: str
    scope: str
    conditions: str | None = None
    item: str | None = None
    unit: str | None = None
    unit_price: Decimal | None = None
    discount_percent: Decimal | None = None
    commitment_amount: Decimal | None = None
    commitment_period: str | None = None
    tiers: list[dict] = field(default_factory=list)
    currency: str | None = None
    quotes: list[dict] = field(default_factory=list)
    confidence: Decimal | None = None


def comparable(text: str) -> str:
    """Text reduced so a copied quote matches its page: numbers, spacing and case evened out."""
    return _SPACES.sub(" ", normalize_numbers(text)).strip(_EDGES).casefold()


def quoted_page(quote: str, stated: int | None, pages: list[AgreementPage]) -> int | None:
    """The page `quote` is found on, preferring the stated one; None when it is on none."""
    wanted = comparable(quote)
    if len(wanted) < MIN_QUOTE_CHARS:
        return None
    by_number = {page.number: page for page in pages}
    stated_page = by_number.get(stated) if stated is not None else None
    if stated_page is not None and stated_page.text is None and stated_page.image is not None:
        return stated_page.number
    ordered = ([stated_page] if stated_page else []) + [p for p in pages if p is not stated_page]
    for page in ordered:
        if page.text and wanted in comparable(page.text):
            return page.number
    return None


def draft_term(read: ReadTerm, pages: list[AgreementPage]) -> DraftTerm | None:
    """The term as a draft, or None when its kind, fields or quote don't hold up."""
    kind = read.kind.strip().lower()
    scope = read.scope.strip() or (read.item or "").strip()
    if kind not in _KINDS or not scope:
        return None
    page = quoted_page(read.quote, read.page, pages)
    if page is None:
        return None
    term = DraftTerm(
        kind=kind,
        scope=scope,
        conditions=_text(read.conditions),
        item=_text(read.item),
        unit=_text(read.unit),
        unit_price=_decimal(read.unit_price),
        discount_percent=_decimal(read.discount_percent),
        commitment_amount=_decimal(read.commitment_amount),
        commitment_period=_period(read.commitment_period),
        tiers=[{"threshold": str(tier.threshold), "rebate_percent": str(tier.rebate_percent)}
               for tier in read.tiers
               if tier.threshold is not None and tier.rebate_percent is not None],
        currency=_currency(read.currency),
        quotes=[{"text": read.quote.strip(), "page": page}],
        confidence=_confidence(read.confidence),
    )
    return term if _complete(term) else None


def merge_terms(terms: list[DraftTerm]) -> list[DraftTerm]:
    """One term per kind and subject, keeping every quote and the highest confidence."""
    merged: dict[tuple[str, str], DraftTerm] = {}
    for term in terms:
        key = (term.kind, comparable(term.item or term.scope))
        existing = merged.get(key)
        if existing is None:
            merged[key] = term
            continue
        for quote in term.quotes:
            if quote not in existing.quotes:
                existing.quotes.append(quote)
        if term.confidence is not None and (existing.confidence is None
                                            or term.confidence > existing.confidence):
            existing.confidence = term.confidence
    return list(merged.values())


def _complete(term: DraftTerm) -> bool:
    if term.kind == AgreementTermKind.AGREED_PRICE.value:
        return term.item is not None and term.unit_price is not None
    if term.kind == AgreementTermKind.DISCOUNT.value:
        return term.discount_percent is not None and 0 < term.discount_percent <= 100
    if term.kind == AgreementTermKind.VOLUME_COMMITMENT.value:
        return term.commitment_amount is not None and term.commitment_amount > 0
    return True


def _text(value: str | None) -> str | None:
    cleaned = (value or "").strip()
    return cleaned or None


def _decimal(value: float | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def _confidence(value: float | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(min(max(value, 0.0), 1.0))).quantize(Decimal("0.001"))


def _currency(value: str | None) -> str | None:
    code = (value or "").strip().upper()
    return code if len(code) == 3 and code.isalpha() else None


def _period(value: str | None) -> str | None:
    period = (value or "").strip().lower()
    return period if period in _PERIODS else None
