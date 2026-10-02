"""Asking the LLM what code couldn't decide about an item's candidates, once per pair of
specifications."""
from __future__ import annotations

import logging
from collections.abc import Callable

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from web_api.db.models import SpecComparison
from web_api.specs.specification import Specification

from ...parsing import parse_model
from .prompt import compare_prompt
from .questions import Answers, CandidateAnswer, Question

logger = logging.getLogger("ai_api.alternatives")

Ask = Callable[[str], str]
MATCH_VERSION = 1
PAIR = "pair"
PROMPT_CANDIDATES = 8


class PairJudge:
    """Answers questions about candidates from stored comparisons first, then by asking, a few
    candidates to a prompt; counts what it asked."""

    def __init__(self, session: Session, ask: Ask) -> None:
        self._session = session
        self._ask = ask
        self.prompts = 0

    def answer(self, item: Specification,
               questions: list[Question]) -> dict[str, CandidateAnswer]:
        """The answer for each question that could be answered, by its key."""
        answers: dict[str, CandidateAnswer] = {}
        unasked: list[Question] = []
        for question in questions:
            stored = self._stored(item, question.candidate)
            if stored is None:
                unasked.append(question)
            else:
                answers[question.key] = stored
        for start in range(0, len(unasked), PROMPT_CANDIDATES):
            answers.update(self._ask_some(item, unasked[start:start + PROMPT_CANDIDATES]))
        return answers

    def _ask_some(self, item: Specification,
                  questions: list[Question]) -> dict[str, CandidateAnswer]:
        self.prompts += 1
        try:
            reply = parse_model(self._ask(compare_prompt(item, questions)), Answers)
        except Exception as error:  # noqa: BLE001
            logger.warning("alternatives: %d candidate(s) were not compared: %s",
                           len(questions), error)
            return {}
        by_number = {answer.n: answer for answer in reply.candidates}
        answered: dict[str, CandidateAnswer] = {}
        for number, question in enumerate(questions, start=1):
            answer = by_number.get(number)
            if answer is not None:
                answered[question.key] = answer
                self._store(item, question.candidate, answer)
        return answered

    def _stored(self, item: Specification, candidate: Specification) -> CandidateAnswer | None:
        found = self._session.exec(select(SpecComparison).where(
            SpecComparison.kind == PAIR, SpecComparison.left_hash == item.digest,
            SpecComparison.right_hash == candidate.digest,
            SpecComparison.version == MATCH_VERSION)).first()
        return CandidateAnswer.model_validate(found.result) if found is not None else None

    def _store(self, item: Specification, candidate: Specification,
               answer: CandidateAnswer) -> None:
        try:
            with self._session.begin_nested():
                self._session.add(SpecComparison(
                    kind=PAIR, left_hash=item.digest, right_hash=candidate.digest,
                    version=MATCH_VERSION, result=answer.model_dump(mode="json", exclude={"n"})))
        except IntegrityError:
            logger.info("alternatives: a comparison was stored meanwhile")
