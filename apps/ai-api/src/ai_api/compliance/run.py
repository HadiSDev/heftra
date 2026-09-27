"""Checking every active agreement of a company against its spend lines."""
from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Callable
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlmodel import Session, select

from web_api.db.models import (
    Agreement,
    AgreementFinding,
    AgreementStatus,
    AgreementTerm,
    AgreementTermStatus,
    Company,
    FindingReviewStatus,
    Vendor,
)
from web_api.fx.service import FxService
from web_api.vat import international_vat

from .candidates import EmbedFn, LineVectors, candidates, descendants
from .drafts import FindingDraft
from .identity import from_supplier, supplier_vat
from .judge.judge import Ask, Judge
from .lines import AnalysedLine, invoice_discount_rates, load_lines
from .rules import TermContext, evaluate
from .savings import fold_savings
from .store import delete_undecided_findings, store_findings

logger = logging.getLogger("ai_api.compliance")


def analyse_company(session: Session, company_id: str, *, ask: Ask, embed_fn: EmbedFn,
                    fx: FxService | None = None,
                    today: Callable[[], date] = date.today) -> dict:
    """Recalculate the findings of every active agreement; returns the run's counts."""
    agreements = session.exec(
        select(Agreement).where(Agreement.company_id == company_id,
                                Agreement.status == AgreementStatus.ACTIVE.value)
    ).all()
    summary: dict = {"agreements": len(agreements), "terms": 0, "candidates": 0}
    if not agreements:
        return {**summary, "judged": 0, "cached": 0, "unjudged": 0, "findings": {}}

    fx = fx or FxService(session)
    judge = Judge(session, ask)
    base_currency = session.get(Company, company_id).base_currency
    found: Counter[str] = Counter()
    for agreement in agreements:
        terms = session.exec(
            select(AgreementTerm).where(
                AgreementTerm.agreement_id == agreement.id,
                AgreementTerm.status == AgreementTermStatus.CONFIRMED.value,
            )
        ).all()
        delete_undecided_findings(session, [agreement.id], [term.id for term in terms])
        drafts, considered = _analyse(session, agreement, terms, judge, fx, embed_fn)
        drafts = fold_savings(drafts, base_currency)
        store_findings(session, agreement, [term.id for term in terms], drafts, base_currency)
        agreement.analysed_at = datetime.now(timezone.utc)
        session.add(agreement)
        summary["terms"] += len(terms)
        summary["candidates"] += considered
        found.update(draft.kind.value for draft in drafts)
    session.commit()
    return {**summary, "judged": judge.judged, "cached": judge.cached,
            "unjudged": judge.unjudged, "findings": dict(found)}


def _analyse(session: Session, agreement: Agreement, terms: list[AgreementTerm], judge: Judge,
             fx: FxService, embed_fn: EmbedFn) -> tuple[list[FindingDraft], int]:
    if not terms or agreement.starts_on is None:
        return [], 0
    lines = load_lines(session, agreement.company_id, agreement.starts_on, agreement.ends_on)
    if not lines:
        return [], 0
    vendor = session.get(Vendor, agreement.vendor_id) if agreement.vendor_id else None
    vat = supplier_vat(agreement, international_vat(vendor.vat_number, vendor.country_code)
                       if vendor else None)
    supplier_name = vendor.name if vendor else (agreement.supplier_name or "the supplier")
    ruled_out = _ruled_out(session, agreement.id)
    vectors = LineVectors(lines, embed_fn)
    discounts = invoice_discount_rates(session, {line.invoice_id for line in lines})
    convert = _converter(fx)
    drafts: list[FindingDraft] = []
    considered = 0
    for term in terms:
        context = TermContext(term, supplier_name, term.currency or agreement.currency)
        pool = [line for line in lines if (term.id, line.line_id) not in ruled_out]
        for line in candidates(term, pool, vectors, descendants(session, term.scope_category_ids)):
            considered += 1
            judgement = judge.judge(term, line)
            if judgement is None or not judgement.in_scope:
                continue
            drafts.extend(evaluate(
                context, line, judgement, from_supplier(line, agreement.vendor_id, vat),
                convert=convert, invoice_discount=discounts.get(line.invoice_id),
            ))
    return drafts, considered


def _ruled_out(session: Session, agreement_id: str) -> set[tuple[str, str]]:
    """(term, line) pairs a person ruled not in scope."""
    return set(session.exec(
        select(AgreementFinding.term_id, AgreementFinding.invoice_line_id).where(
            AgreementFinding.agreement_id == agreement_id,
            AgreementFinding.review_status == FindingReviewStatus.NOT_IN_SCOPE.value,
        )
    ).all())


def _converter(fx: FxService):
    def convert(price: Decimal, source: str | None, target: str | None,
                on: date | None) -> Decimal | None:
        if not target or not source or source == target:
            return price
        found = fx.get_rate(source, target, on)
        return price * found[0] if found else None
    return convert
