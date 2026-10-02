"""One agreement's run: its terms' candidate items judged, their lines checked page by page."""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlmodel import Session, select

from web_api.db.models import (
    Agreement,
    AgreementScopeJudgement,
    AgreementTerm,
    AgreementTermStatus,
    Vendor,
)
from web_api.fx.service import FxService
from web_api.vat import international_vat

from ..agreements.scope_categories import Suggest
from ..items.grouping import changed_item_keys, company_items
from ..items.refresh import refresh_item_keys
from .candidates import Similarity, Window, descendants, term_candidates
from .findings import (
    delete_undecided_findings,
    prune_out_of_scope,
    prune_outside_validity,
    write_page,
)
from .identity import from_supplier, supplier_vat, supplier_vendor_ids
from .judge.judge import Judge
from .keys import term_key
from .pages import TermLines, in_scope_pages
from .rules import TermContext
from .scope import RunScope, run_scope, watermark
from .totals import drop_totals, recompute_totals, touched_months


@dataclass
class RunCounts:
    terms: int = 0
    candidates: int = 0
    capped_terms: int = 0
    lines: int = 0
    pages: int = 0
    findings: Counter = field(default_factory=Counter)
    runs: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RunTools:
    """What every agreement of the company's run shares."""

    judge: Judge
    similarity: Similarity
    suggest: Callable[[], Suggest]
    fx: FxService
    buyer: str
    base_currency: str | None


def analyse_agreement(session: Session, agreement: Agreement, tools: RunTools,
                      counts: RunCounts) -> None:
    """Recalculate the agreement's findings and totals, all of them or what changed since its
    watermark, and move the watermark once every candidate item was judged."""
    started = datetime.now(timezone.utc)
    scope = run_scope(agreement)
    counts.runs[agreement.id] = "full" if scope.full else "incremental"
    terms = _confirmed_terms(session, agreement)
    _drop_unconfirmed(session, agreement, {term.id for term in terms})
    unjudged = 0
    if terms and agreement.starts_on is not None:
        unjudged = _analyse_terms(session, agreement, terms, scope, tools, counts)
    if unjudged == 0:
        agreement.analysed_from = started
        agreement.full_analysis = False
    agreement.analysed_at = datetime.now(timezone.utc)
    session.add(agreement)
    session.commit()


def _analyse_terms(session: Session, agreement: Agreement, terms: list[AgreementTerm],
                   scope: RunScope, tools: RunTools, counts: RunCounts) -> int:
    """Check every term; returns how many candidate items the judge could not answer for."""
    company_id = agreement.company_id
    refresh_item_keys(session, company_id, watermark(agreement))
    if scope.full:
        prune_outside_validity(session, agreement)
    keys = {term.id: term_key(term, tools.buyer) for term in terms}
    since = {term.id: scope.since_for(term) if _judged_before(session, term.id, keys[term.id])
             else None for term in terms}
    changed = None if scope.full else frozenset(changed_item_keys(
        session, company_id, scope.since, start=agreement.starts_on, end=agreement.ends_on))
    every_item = any(moment is None for moment in since.values())
    tools.similarity.ensure(company_id, company_items(
        session, company_id, start=agreement.starts_on, end=agreement.ends_on,
        keys=None if every_item else changed))
    vendor = session.get(Vendor, agreement.vendor_id) if agreement.vendor_id else None
    vat = supplier_vat(agreement, international_vat(vendor.vat_number, vendor.country_code)
                       if vendor else None)
    supplier_ids = supplier_vendor_ids(session, agreement, vat)
    supplier_name = vendor.name if vendor else (agreement.supplier_name or "the supplier")
    convert = _converter(tools.fx)
    unjudged = 0
    for term in terms:
        key = keys[term.id]
        window = Window(company_id, agreement.starts_on, agreement.ends_on,
                        keys=None if since[term.id] is None else changed)
        categories = descendants(session, _scope_categories(session, term, tools.suggest))
        candidates = term_candidates(session, term, window, categories, tools.similarity)
        judgements = tools.judge.judge_items(term, candidates.items)
        session.commit()
        unanswered = {item.key for item in candidates.items if item.key not in judgements}
        unjudged += len(unanswered)
        counts.terms += 1
        counts.candidates += len(candidates.items)
        counts.capped_terms += int(candidates.capped)
        wanted = TermLines(company_id, term.id, key, agreement.starts_on, agreement.ends_on,
                           since[term.id])
        context = TermContext(term, supplier_name, term.currency or agreement.currency)
        for page in in_scope_pages(session, wanted):
            counts.findings.update(write_page(
                session, agreement, context, page,
                from_supplier=lambda line: from_supplier(line, agreement.vendor_id, vat),
                convert=convert, base_currency=tools.base_currency))
            counts.lines += len(page)
            counts.pages += 1
        prune_out_of_scope(session, term.id, key, keep=unanswered)
        recompute_totals(session, wanted, supplier_ids, touched_months(session, wanted))
    return unjudged


def _confirmed_terms(session: Session, agreement: Agreement) -> list[AgreementTerm]:
    return list(session.exec(
        select(AgreementTerm).where(
            AgreementTerm.agreement_id == agreement.id,
            AgreementTerm.status == AgreementTermStatus.CONFIRMED.value,
        )
    ).all())


def _drop_unconfirmed(session: Session, agreement: Agreement, confirmed: set[str]) -> None:
    delete_undecided_findings(session, [agreement.id], list(confirmed))
    others = session.exec(
        select(AgreementTerm.id).where(AgreementTerm.agreement_id == agreement.id)
    ).all()
    drop_totals(session, [term_id for term_id in others if term_id not in confirmed])
    session.commit()


def _scope_categories(session: Session, term: AgreementTerm,
                      suggest: Callable[[], Suggest]) -> list[str]:
    """The term's spend categories; a term without any is given the suggested ones, saved for a
    person to see and correct."""
    if not term.scope_category_ids:
        term.scope_category_ids = suggest()(term.item or term.scope)
        session.add(term)
    return list(term.scope_category_ids)


def _judged_before(session: Session, term_id: str, key: str) -> bool:
    """Whether the term has any judgement under its current key; a new buyer description or
    judge version leaves it with none, and then all its lines are redone."""
    return session.exec(
        select(AgreementScopeJudgement.id).where(
            AgreementScopeJudgement.term_id == term_id,
            AgreementScopeJudgement.term_key == key,
        ).limit(1)
    ).first() is not None


def _converter(fx: FxService):
    def convert(price: Decimal, source: str | None, target: str | None,
                on: date | None) -> Decimal | None:
        if not target or not source or source == target:
            return price
        found = fx.get_rate(source, target, on)
        return price * found[0] if found else None
    return convert
