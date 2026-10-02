"""Judging items in batches, reusing stored answers and re-asking what a batch missed."""
from __future__ import annotations

import json
import re
import threading
from decimal import Decimal

import pytest
from sqlmodel import Session

from agreement_books import Books
from ai_api.compliance.judge.judge import Judge
from ai_api.items.item import Item
from web_api.db.models import AgreementTermKind

_PURCHASE = re.compile(r"^Purchase (\d+):\nItem: (.*)$", re.M)


def _item(name: str) -> Item:
    return Item(key=f"key-{name}", item_name=name, description=None, unit="piece",
                category_id=None, category_path=(), vendor_id=None, vendor_name="Proshop",
                lines=1, spend=Decimal(100), unit_price=Decimal(100), first_on=None,
                last_on=None)


def _answer(name: str) -> dict:
    return {"in_scope": "laptop" in name.lower(), "same_item": None,
            "units_comparable": True, "confidence": 0.9, "reason": f"About {name}."}


class Model:
    """Answers batches by number and single prompts by item, recording what it was asked."""

    def __init__(self, *, broken_batches: bool = False, skip: str | None = None) -> None:
        self.broken_batches = broken_batches
        self.skip = skip
        self.batches = 0
        self.singles = 0
        self._lock = threading.Lock()

    def __call__(self, prompt: str) -> str:
        numbered = _PURCHASE.findall(prompt)
        with self._lock:
            if numbered:
                self.batches += 1
            else:
                self.singles += 1
        if numbered:
            if self.broken_batches:
                return "I could not decide."
            return json.dumps({"answers": [{"n": int(n), **_answer(name)}
                                           for n, name in numbered if name != self.skip]})
        name = prompt.split("Purchase:\nItem: ", 1)[1].splitlines()[0]
        return json.dumps(_answer(name))


@pytest.fixture
def term(engine):
    with Session(engine) as s:
        books = Books(s)
        term = books.term(books.agreement(), AgreementTermKind.PREFERRED_SUPPLIER, "Laptops")
        yield s, term


def test_items_are_asked_in_batches(term):
    session, term = term
    model = Model()
    items = [_item(f"Laptop {n}") for n in range(5)] + [_item("Coffee")]

    judgements = Judge(session, model, batch=4, concurrency=2).judge_items(term, items)

    assert model.batches == 2 and model.singles == 0
    assert sum(j.in_scope for j in judgements.values()) == 5


def test_a_stored_answer_is_not_asked_again(term):
    session, term = term
    first, second = Model(), Model()
    Judge(session, first, batch=4).judge_items(term, [_item("Laptop A")])

    judge = Judge(session, second, batch=4)
    judge.judge_items(term, [_item("Laptop A"), _item("Laptop B")])

    assert (judge.cached, judge.judged, second.singles + second.batches) == (1, 1, 1)


def test_a_batch_that_cannot_be_read_is_asked_one_by_one(term):
    session, term = term
    model = Model(broken_batches=True)

    judge = Judge(session, model, batch=3)
    judgements = judge.judge_items(term, [_item("Laptop A"), _item("Laptop B"), _item("Mouse")])

    assert (model.batches, model.singles, len(judgements)) == (1, 3, 3)


def test_an_item_a_batch_left_out_is_asked_on_its_own(term):
    session, term = term
    model = Model(skip="Laptop B")

    judgements = Judge(session, model, batch=3).judge_items(
        term, [_item("Laptop A"), _item("Laptop B"), _item("Mouse")])

    assert (model.batches, model.singles) == (1, 1)
    assert judgements["key-Laptop B"].in_scope is True


def test_concurrent_batches_lose_no_answers(term):
    session, term = term
    items = [_item(f"Laptop {n}") for n in range(40)]

    judge = Judge(session, Model(), batch=3, concurrency=6)
    judgements = judge.judge_items(term, items)

    assert (len(judgements), judge.judged, judge.unjudged) == (40, 40, 0)
