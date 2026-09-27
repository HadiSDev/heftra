"""Reading an agreement's header and terms, part by part, from a stub model."""
from __future__ import annotations

import json

import pytest

from ai_api import config
from ai_api.agreements.extract import AgreementUnreadable, read_agreement
from ai_api.agreements.pages import AgreementPage

PAGES = [
    AgreementPage(1, text="Framework agreement FA-2026-17 with Atea A/S"),
    AgreementPage(2, text="IT equipment shall be purchased from Atea when available from stock."),
    AgreementPage(3, text="Accessories carry a discount of 10 percent off list price."),
]

HEADER = {"title": "Framework agreement", "reference": "FA-2026-17",
          "supplier_name": "Atea A/S", "starts_on": "2026-01-01", "currency": "DKK"}


class StubModel:
    """Answers the header request, then one answer per part, recording what it was sent."""

    def __init__(self, parts: list) -> None:
        self.parts = list(parts)
        self.requests: list[list[dict]] = []

    def __call__(self, messages: list[dict]) -> str:
        self.requests.append(messages)
        if len(self.requests) == 1:
            return json.dumps(HEADER)
        answer = self.parts.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer if isinstance(answer, str) else json.dumps({"terms": answer})


@pytest.fixture(autouse=True)
def two_pages_a_part(monkeypatch):
    monkeypatch.setattr(config, "AGREEMENT_CHUNK_PAGES", 2)


def _texts(messages: list[dict]) -> str:
    return "\n".join(part.get("text", "") for part in messages[0]["content"])


def test_the_header_and_terms_are_read_part_by_part():
    model = StubModel([
        [{"kind": "preferred_supplier", "scope": "IT equipment",
          "conditions": "when available from stock",
          "quote": "IT equipment shall be purchased from Atea when available from stock.",
          "page": 2}],
        [{"kind": "discount", "scope": "Accessories", "discount_percent": 10,
          "quote": "Accessories carry a discount of 10 percent off list price.", "page": 3}],
    ])

    read = read_agreement(PAGES, complete=model)

    assert read.header.reference == "FA-2026-17"
    assert [term.kind for term in read.terms] == ["preferred_supplier", "discount"]
    assert (read.chunks, read.failed_chunks, read.dropped_terms) == (2, 0, 0)
    assert "--- Page 1 ---" in _texts(model.requests[1])
    assert "--- Page 3 ---" in _texts(model.requests[2])


def test_invented_terms_are_counted_and_dropped():
    model = StubModel([
        [{"kind": "agreed_price", "scope": "Laptops", "item": "MacBook Pro", "unit_price": 20000,
          "quote": "MacBook Pro at DKK 20,000 each.", "page": 2}],
        [],
    ])

    read = read_agreement(PAGES, complete=model)

    assert (read.terms, read.dropped_terms) == ([], 1)


def test_a_part_that_can_t_be_read_is_skipped():
    model = StubModel([RuntimeError("timed out"), [
        {"kind": "discount", "scope": "Accessories", "discount_percent": 10,
         "quote": "Accessories carry a discount of 10 percent off list price.", "page": 3}]])

    read = read_agreement(PAGES, complete=model)

    assert read.failed_chunks == 1
    assert [term.kind for term in read.terms] == ["discount"]


def test_nothing_readable_fails():
    model = StubModel([RuntimeError("model down"), RuntimeError("model down")])

    with pytest.raises(AgreementUnreadable):
        read_agreement(PAGES, complete=model)
