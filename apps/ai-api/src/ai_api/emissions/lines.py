"""Match a company's lines to emission sectors: cache, then the agent, then the fallback."""
from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Callable
from decimal import Decimal

from sqlalchemy import or_, update
from sqlmodel import Session, select

from web_api.db.models import EmissionSector, EmissionSectorSource, InvoiceLine
from web_api.emissions.factors import active_factor_set

from .answer import MatchFailed, SectorAnswer
from .cache import cached_answer, remember_answer
from .line_context import LineContext, line_contexts
from .matchers import Matchers, default_matchers
from .sector_index import SectorIndex

logger = logging.getLogger("ai_api.emissions")

NO_FACTOR_SET = "no active factor set"
COUNTS = ("agent", "fallback", "unmatched", "cached", "failed")

MatchersFor = Callable[[str, list[EmissionSector]], Matchers]


def match_company(session: Session, company_id: str, *, limit: int | None = None,
                  rematch: bool = False, matchers_for: MatchersFor | None = None) -> dict:
    """Match the company's eligible lines, and say how each was answered."""
    factor_set = active_factor_set(session)
    if factor_set is None:
        return {"skipped": NO_FACTOR_SET}
    classification = factor_set.classification
    sectors = list(session.exec(
        select(EmissionSector).where(EmissionSector.classification == classification)
    ).all())
    matchers = (matchers_for or _connected_matchers)(classification, sectors)

    if rematch:
        _forget_ai_sectors(session, company_id)
    lines = _eligible_lines(session, company_id, classification, limit)
    counts: Counter[str] = Counter({name: 0 for name in COUNTS})
    for context, line in zip(line_contexts(session, lines), lines):
        outcome = _match_line(session, context, line, classification, matchers,
                              use_cache=not rematch)
        counts[outcome] += 1
        session.commit()
    return dict(counts)


def _match_line(session: Session, context: LineContext, line: InvoiceLine, classification: str,
                matchers: Matchers, *, use_cache: bool) -> str:
    answer = cached_answer(session, context, classification) if use_cache else None
    outcome = "cached"
    if answer is None:
        try:
            answer, outcome = _ask(context, matchers)
        except MatchFailed as error:
            logger.warning("line %s: no sector: %s", line.id, error)
            return "failed"
        remember_answer(session, context, classification, answer)
    _apply(line, answer)
    session.add(line)
    if answer.sector_id is None and outcome != "cached":
        return "unmatched"
    return outcome


def _ask(context: LineContext, matchers: Matchers) -> tuple[SectorAnswer, str]:
    if matchers.agent is not None:
        try:
            return matchers.agent(context), "agent"
        except MatchFailed as error:
            logger.info("line %s: agent gave up, falling back: %s", context.line_id, error)
    return matchers.fallback(context), "fallback"


def _apply(line: InvoiceLine, answer: SectorAnswer) -> None:
    if answer.sector_id is None:
        line.emission_sector_id = None
        line.emission_sector_source = None
        line.emission_sector_confidence = None
        line.emission_sector_rationale = None
        return
    line.emission_sector_id = answer.sector_id
    line.emission_sector_source = EmissionSectorSource.AI
    line.emission_sector_confidence = Decimal(str(round(answer.confidence, 3)))
    line.emission_sector_rationale = answer.rationale or None


def _eligible_lines(session: Session, company_id: str, classification: str,
                    limit: int | None) -> list[InvoiceLine]:
    """Lines with no sector, and AI-matched lines whose sector is of another classification."""
    current = select(EmissionSector.id).where(EmissionSector.classification == classification)
    statement = (
        select(InvoiceLine)
        .where(
            InvoiceLine.company_id == company_id,
            or_(
                InvoiceLine.emission_sector_id.is_(None),  # type: ignore[union-attr]
                (InvoiceLine.emission_sector_source == EmissionSectorSource.AI)
                & InvoiceLine.emission_sector_id.not_in(current),  # type: ignore[union-attr]
            ),
        )
        .order_by(InvoiceLine.created_at, InvoiceLine.id)
    )
    if limit is not None:
        statement = statement.limit(limit)
    return list(session.exec(statement).all())


def _forget_ai_sectors(session: Session, company_id: str) -> None:
    session.exec(
        update(InvoiceLine)
        .where(InvoiceLine.company_id == company_id,
               InvoiceLine.emission_sector_source == EmissionSectorSource.AI)
        .values(emission_sector_id=None, emission_sector_source=None,
                emission_sector_confidence=None, emission_sector_rationale=None)
    )
    session.commit()


def _connected_matchers(classification: str, sectors: list[EmissionSector]) -> Matchers:
    index = SectorIndex.connect()
    index.ensure(classification, sectors)
    return default_matchers(index, classification, sectors)
