"""Reusing a sector chosen before for the same question in the same classification."""
from __future__ import annotations

from sqlalchemy import delete
from sqlmodel import Session, select

from ..persistence import EmissionSectorCache
from .answer import SectorAnswer
from .line_context import LineContext


def cached_answer(session: Session, context: LineContext,
                  classification: str) -> SectorAnswer | None:
    row = session.exec(
        select(EmissionSectorCache).where(
            EmissionSectorCache.question_key == context.question_key,
            EmissionSectorCache.classification == classification,
        )
    ).first()
    if row is None:
        return None
    return SectorAnswer(row.sector_id, row.confidence or 0.0, row.rationale or "")


def remember_answer(session: Session, context: LineContext, classification: str,
                    answer: SectorAnswer) -> None:
    """Store the answer, replacing any earlier one to the same question."""
    session.exec(delete(EmissionSectorCache).where(
        EmissionSectorCache.question_key == context.question_key,
        EmissionSectorCache.classification == classification,
    ))
    session.add(EmissionSectorCache(
        question_key=context.question_key, classification=classification,
        sector_id=answer.sector_id, confidence=answer.confidence, rationale=answer.rationale,
        question_sample=context.sample,
    ))
