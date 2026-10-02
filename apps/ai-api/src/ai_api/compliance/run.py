"""Checking every active agreement of a company against its spend lines."""
from __future__ import annotations

import logging
from collections.abc import Callable

from sqlmodel import Session, select

from web_api.company_context import business_context
from web_api.db.models import Agreement, AgreementStatus, Company
from web_api.fx.service import FxService

from ..agreements.scope_categories import Suggest, category_suggester
from ..items.index import Embed, ItemIndex
from .agreement_run import RunCounts, RunTools, analyse_agreement
from .candidates import Similarity
from .judge.judge import Ask, Judge

logger = logging.getLogger("ai_api.compliance")


def analyse_company(session: Session, company_id: str, *, ask: Ask, embed_fn: Embed,
                    fx: FxService | None = None, index: ItemIndex | None = None) -> dict:
    """Recalculate every active agreement, incrementally where it can; returns the run's counts.

    The item index is connected to unless one is given.
    """
    agreements = session.exec(
        select(Agreement).where(Agreement.company_id == company_id,
                                Agreement.status == AgreementStatus.ACTIVE.value)
    ).all()
    counts = RunCounts()
    if not agreements:
        return _summary(0, counts, None, available=True)
    company = session.get(Company, company_id)
    buyer = business_context(company)
    judge = Judge(session, ask, buyer)
    similarity = Similarity(index if index is not None else ItemIndex.connect(embed_fn))
    tools = RunTools(judge=judge, similarity=similarity,
                     suggest=_lazy_suggester(session, company_id, embed_fn),
                     fx=fx or FxService(session), buyer=buyer,
                     base_currency=company.base_currency)
    for agreement in agreements:
        analyse_agreement(session, agreement, tools, counts)
    if not similarity.available:
        logger.warning("compliance: the item index was unavailable; candidates came from "
                       "categories only")
    return _summary(len(agreements), counts, judge, available=similarity.available)


def _lazy_suggester(session: Session, company_id: str, embed_fn: Embed) -> Callable[[], Suggest]:
    built: list[Suggest] = []

    def suggester() -> Suggest:
        if not built:
            built.append(category_suggester(session, company_id, embed_fn=embed_fn))
        return built[0]

    return suggester


def _summary(agreements: int, counts: RunCounts, judge: Judge | None, *,
             available: bool) -> dict:
    return {
        "agreements": agreements,
        "runs": counts.runs,
        "terms": counts.terms,
        "candidates": counts.candidates,
        "judged": judge.judged if judge else 0,
        "cached": judge.cached if judge else 0,
        "unjudged": judge.unjudged if judge else 0,
        "capped_terms": counts.capped_terms,
        "lines": counts.lines,
        "pages": counts.pages,
        "findings": dict(counts.findings),
        "similarity": available,
    }
