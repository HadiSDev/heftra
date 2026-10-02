"""Judging a term's candidate items, reusing earlier answers, asking the rest in batches."""
from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from sqlmodel import Session, col, select

from web_api.db.models import AgreementScopeJudgement, AgreementTerm

from ... import config
from ...items.item import Item
from ...parsing import parse_model
from ..keys import term_key
from .prompt import batch_prompt, judge_prompt
from .reply import BatchReply, JudgeReply

logger = logging.getLogger("ai_api.compliance")

Ask = Callable[[str], str]
LOOKUP_CHUNK = 500


class Judge:
    """Answers for one run, from the stored judgements first, counting what it asked."""

    def __init__(self, session: Session, ask: Ask, buyer: str = "", *,
                 batch: int | None = None, concurrency: int | None = None) -> None:
        self._session = session
        self._ask = ask
        self._buyer = buyer
        self._batch = max(1, batch or config.AGREEMENT_JUDGE_BATCH)
        self._concurrency = max(1, concurrency or config.AGREEMENT_JUDGE_CONCURRENCY)
        self.judged = 0
        self.cached = 0
        self.unjudged = 0

    def judge_items(self, term: AgreementTerm,
                    items: list[Item]) -> dict[str, AgreementScopeJudgement]:
        """The judgement of each item that could be judged, by item key."""
        key = term_key(term, self._buyer)
        judgements = self._stored(term.id, key, [item.key for item in items])
        self.cached += len(judgements)
        missing = [item for item in items if item.key not in judgements]
        replies = self._ask_all(term, missing)
        for item in missing:
            reply = replies.get(item.key)
            if reply is None:
                self.unjudged += 1
                continue
            judgement = _judgement(term.id, key, item.key, reply)
            self._session.add(judgement)
            judgements[item.key] = judgement
            self.judged += 1
        self._session.flush()
        return judgements

    def _stored(self, term_id: str, key: str,
                item_keys: list[str]) -> dict[str, AgreementScopeJudgement]:
        found: dict[str, AgreementScopeJudgement] = {}
        for start in range(0, len(item_keys), LOOKUP_CHUNK):
            chunk = item_keys[start:start + LOOKUP_CHUNK]
            for judgement in self._session.exec(
                select(AgreementScopeJudgement).where(
                    AgreementScopeJudgement.term_id == term_id,
                    AgreementScopeJudgement.term_key == key,
                    col(AgreementScopeJudgement.question_key).in_(chunk),
                )
            ).all():
                found[judgement.question_key] = judgement
        return found

    def _ask_all(self, term: AgreementTerm, items: list[Item]) -> dict[str, JudgeReply]:
        batches = [items[start:start + self._batch] for start in range(0, len(items), self._batch)]
        replies: dict[str, JudgeReply] = {}
        if not batches:
            return replies
        with ThreadPoolExecutor(max_workers=min(self._concurrency, len(batches))) as pool:
            for answered in pool.map(lambda batch: self._ask_batch(term, batch), batches):
                replies.update(answered)
        return replies

    def _ask_batch(self, term: AgreementTerm, items: list[Item]) -> dict[str, JudgeReply]:
        if len(items) == 1:
            return self._ask_each(term, items)
        try:
            reply = parse_model(self._ask(batch_prompt(term, items, self._buyer)), BatchReply)
        except Exception as error:  # noqa: BLE001
            logger.warning("compliance: a batch of %d item(s) against term %s was not judged, "
                           "asking one at a time: %s", len(items), term.id, error)
            return self._ask_each(term, items)
        by_number = {answer.n: answer for answer in reply.answers}
        answered = {item.key: by_number[number]
                    for number, item in enumerate(items, start=1) if number in by_number}
        unanswered = [item for item in items if item.key not in answered]
        return {**answered, **self._ask_each(term, unanswered)}

    def _ask_each(self, term: AgreementTerm, items: list[Item]) -> dict[str, JudgeReply]:
        answered: dict[str, JudgeReply] = {}
        for item in items:
            try:
                answered[item.key] = parse_model(
                    self._ask(judge_prompt(term, item, self._buyer)), JudgeReply)
            except Exception as error:  # noqa: BLE001
                logger.warning("compliance: item %s against term %s not judged: %s",
                               item.key[:12], term.id, error)
        return answered


def _judgement(term_id: str, key: str, item_key: str,
               reply: JudgeReply) -> AgreementScopeJudgement:
    return AgreementScopeJudgement(
        term_id=term_id, term_key=key, question_key=item_key,
        in_scope=reply.in_scope, same_item=reply.same_item,
        units_comparable=reply.units_comparable,
        confidence=Decimal(str(reply.confidence)).quantize(Decimal("0.001"))
        if reply.confidence is not None else None,
        reason=reply.reason.strip() or "No reason given.",
    )
