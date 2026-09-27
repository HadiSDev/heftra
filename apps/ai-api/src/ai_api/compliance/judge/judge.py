"""Judging term and line pairs, reusing earlier answers to the same question."""
from __future__ import annotations

import logging
from collections.abc import Callable
from decimal import Decimal

from sqlmodel import Session, select

from web_api.db.models import AgreementScopeJudgement, AgreementTerm

from ...parsing import parse_model
from ..keys import term_key
from ..lines import AnalysedLine
from .prompt import judge_prompt
from .reply import JudgeReply

logger = logging.getLogger("ai_api.compliance")

Ask = Callable[[str], str]


class Judge:
    """Answers for one run, from the stored judgements first, counting what it asked."""

    def __init__(self, session: Session, ask: Ask) -> None:
        self._session = session
        self._ask = ask
        self.judged = 0
        self.cached = 0
        self.unjudged = 0

    def judge(self, term: AgreementTerm, line: AnalysedLine) -> AgreementScopeJudgement | None:
        key = term_key(term)
        stored = self._session.exec(
            select(AgreementScopeJudgement).where(
                AgreementScopeJudgement.term_id == term.id,
                AgreementScopeJudgement.term_key == key,
                AgreementScopeJudgement.question_key == line.question_key,
            )
        ).first()
        if stored is not None:
            self.cached += 1
            return stored
        try:
            reply = parse_model(self._ask(judge_prompt(term, line)), JudgeReply)
        except Exception as error:  # noqa: BLE001
            self.unjudged += 1
            logger.warning("compliance: line %s against term %s not judged: %s",
                           line.line_id, term.id, error)
            return None
        self.judged += 1
        judgement = AgreementScopeJudgement(
            term_id=term.id, term_key=key, question_key=line.question_key,
            in_scope=reply.in_scope, same_item=reply.same_item,
            units_comparable=reply.units_comparable,
            confidence=Decimal(str(reply.confidence)).quantize(Decimal("0.001"))
            if reply.confidence is not None else None,
            reason=reply.reason.strip() or "No reason given.",
        )
        self._session.add(judgement)
        self._session.flush()
        return judgement
