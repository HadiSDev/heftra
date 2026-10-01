"""Reading an agreement's header and terms, page by page, from a stub model."""
from __future__ import annotations

import json
import re

import pytest

from ai_api.agreements.definitions import Definition, checked_definitions
from ai_api.agreements.extract import AgreementUnreadable, read_agreement
from ai_api.agreements.models import ReadDefinition
from ai_api.agreements.pages import AgreementPage

PAGES = [
    AgreementPage(1, text="Framework agreement FA-2026-17 with Atea A/S"),
    AgreementPage(2, text="IT equipment shall be purchased from Atea when available from stock."),
    AgreementPage(3, text="Accessories carry a discount of 10 percent off list price."),
]

HEADER = {"title": "Framework agreement", "reference": "FA-2026-17",
          "supplier_name": "Atea A/S", "starts_on": "2026-01-01", "currency": "DKK"}


class StubModel:
    """Answers the header request, then one answer per page, recording what it was sent."""

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
        if isinstance(answer, (str, dict)):
            return answer if isinstance(answer, str) else json.dumps(answer)
        return json.dumps({"terms": answer})


def _texts(messages: list[dict]) -> str:
    return "\n".join(part.get("text", "") for part in messages[0]["content"])


def test_the_header_and_terms_are_read_page_by_page():
    model = StubModel([
        [],
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
    assert (read.pages, read.failed_pages, read.dropped_terms) == (3, 0, 0)
    for number, request in enumerate(model.requests[1:], start=1):
        assert f"--- Page {number} ---" in _texts(request)
        assert len(re.findall(r"--- Page \d+ ---", _texts(request))) == 1


def test_invented_terms_are_counted_and_dropped():
    model = StubModel([
        [],
        [{"kind": "agreed_price", "scope": "Laptops", "item": "MacBook Pro", "unit_price": 20000,
          "quote": "MacBook Pro at DKK 20,000 each.", "page": 2}],
        [],
    ])

    read = read_agreement(PAGES, complete=model)

    assert (read.terms, read.dropped_terms) == ([], 1)


def test_a_page_that_can_t_be_read_is_skipped():
    model = StubModel([[], RuntimeError("timed out"), [
        {"kind": "discount", "scope": "Accessories", "discount_percent": 10,
         "quote": "Accessories carry a discount of 10 percent off list price.", "page": 3}]])

    read = read_agreement(PAGES, complete=model)

    assert read.failed_pages == 1
    assert [term.kind for term in read.terms] == ["discount"]


def test_nothing_readable_fails():
    model = StubModel([RuntimeError("model down")] * 3)

    with pytest.raises(AgreementUnreadable):
        read_agreement(PAGES, complete=model)


def test_null_scopes_and_zeroed_fields_are_read_as_missing():
    commitment = "The Customer commits to purchasing at least DKK 100,000 per calendar year."
    price = "Lenovo ThinkPad T14 Gen 5 21ML003XMX piece 8,000.00"
    pages = [AgreementPage(1, text=f"{commitment}\nAnnex 1\n{price}")]
    model = StubModel([[
        {"kind": "volume_commitment", "scope": None, "item": None, "unit_price": 0,
         "discount_percent": 0, "commitment_amount": 100000, "commitment_period": "calendar year",
         "tiers": None, "quote": commitment, "page": 1},
        {"kind": "agreed_price", "scope": None, "item": "Lenovo ThinkPad T14 Gen 5",
         "unit": "piece", "unit_price": 8000, "discount_percent": 0, "commitment_amount": 0,
         "tiers": [], "quote": price, "page": 1},
    ]])

    read = read_agreement(pages, complete=model)

    price_term, commitment_term = sorted(read.terms, key=lambda term: term.kind)
    assert commitment_term.kind == "volume_commitment"
    assert commitment_term.scope == "All purchases from the supplier"
    assert commitment_term.commitment_period == "year"
    assert commitment_term.unit_price is None
    assert price_term.scope == "Lenovo ThinkPad T14 Gen 5"
    assert (price_term.discount_percent, price_term.commitment_amount) == (None, None)


def test_an_agreed_price_is_scoped_to_its_item():
    price = "Lenovo ThinkPad T14 Gen 5 21ML003XMX piece 8,000.00"
    pages = [AgreementPage(1, text=f"Annex 1 - Fixed unit prices in DKK.\n{price}")]
    model = StubModel([[
        {"kind": "agreed_price", "scope": "Fixed unit prices in DKK.",
         "item": "Lenovo ThinkPad T14 Gen 5", "unit": "piece", "unit_price": 8000,
         "quote": price, "page": 1},
    ]])

    read = read_agreement(pages, complete=model)

    assert [term.scope for term in read.terms] == ["Lenovo ThinkPad T14 Gen 5"]


def test_a_scope_carries_the_definitions_of_the_words_it_uses():
    definition = "keyboards, mice, docking stations and cables"
    discount = "Accessories carry a discount of 10 percent off list price."
    pages = [
        AgreementPage(1, text=f'"Accessories" means {definition}.'),
        AgreementPage(2, text=discount),
    ]
    model = StubModel([
        {"terms": [], "definitions": [
            {"term": "Accessories", "meaning": definition},
            {"term": "Monitors", "meaning": "screens of any size and make"},
        ]},
        {"terms": [{"kind": "discount", "scope": "Accessories", "discount_percent": 10,
                    "quote": discount, "page": 2}], "definitions": None},
    ])

    read = read_agreement(pages, complete=model)

    assert [term.scope for term in read.terms] == [
        f'Accessories. In this agreement, "Accessories" means {definition}.']


def test_a_definition_not_on_its_page_is_left_out():
    page = AgreementPage(1, text='"Accessories" means keyboards, mice and cables.')

    kept = checked_definitions([
        ReadDefinition(term="Accessories", meaning="keyboards, mice and cables"),
        ReadDefinition(term="Accessories", meaning="anything sold by the supplier"),
    ], page)

    assert kept == [Definition("Accessories", "keyboards, mice and cables")]


def test_the_reader_is_told_who_the_customer_is():
    model = StubModel([[], [], []])

    read_agreement(PAGES, complete=model, buyer="VectorLab ApS: builds apps for smartwatches")

    assert all("The customer is VectorLab ApS: builds apps for smartwatches" in _texts(request)
               for request in model.requests)
