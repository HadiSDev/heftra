"""A read term becomes a draft only when its quote is on the page and its fields are complete."""
from __future__ import annotations

from decimal import Decimal

from ai_api.agreements.models import ReadTerm
from ai_api.agreements.pages import AgreementPage
from ai_api.agreements.terms import draft_term, merge_terms
from ai_api.documents.images import DocumentImage

PAGES = [
    AgreementPage(3, text="3. Purchasing\nIT equipment shall be purchased from Atea\nwhen "
                          "available from stock."),
    AgreementPage(7, text="Lenovo ThinkPad T14 Gen 5: DKK 8000.00 per unit."),
]


def test_a_quoted_term_is_drafted_with_its_page():
    term = draft_term(ReadTerm(
        kind="preferred_supplier", scope="IT equipment", conditions="when available from stock",
        quote="IT equipment shall be purchased from Atea when available from stock.", page=3,
        confidence=0.9,
    ), PAGES)

    assert term is not None
    assert term.quotes == [{"text": "IT equipment shall be purchased from Atea when available "
                                    "from stock.", "page": 3}]
    assert term.confidence == Decimal("0.900")


def test_an_invented_quote_is_dropped():
    assert draft_term(ReadTerm(kind="preferred_supplier", scope="Printers",
                               quote="Printers shall be leased from Atea only.", page=3),
                      PAGES) is None


def test_a_quote_on_another_page_takes_that_page():
    term = draft_term(ReadTerm(kind="agreed_price", scope="Laptops",
                               item="Lenovo ThinkPad T14 Gen 5", unit="unit", unit_price="8.000,00",
                               currency="dkk",
                               quote="Lenovo ThinkPad T14 Gen 5: DKK 8.000,00 per unit", page=3),
                      PAGES)

    assert term.quotes[0]["page"] == 7
    assert (term.unit_price, term.currency) == (Decimal("8000.0"), "DKK")


def test_a_price_without_its_price_is_dropped():
    assert draft_term(ReadTerm(kind="agreed_price", scope="Laptops",
                               item="Lenovo ThinkPad T14 Gen 5",
                               quote="Lenovo ThinkPad T14 Gen 5: DKK 8000.00 per unit", page=7),
                      PAGES) is None


def test_an_unknown_kind_is_dropped():
    assert draft_term(ReadTerm(kind="liability", scope="Everything",
                               quote="IT equipment shall be purchased from Atea", page=3),
                      PAGES) is None


def test_a_pictured_page_can_t_be_checked_so_its_quote_is_kept():
    pictured = [AgreementPage(2, image=DocumentImage("image/png", b"png"))]

    term = draft_term(ReadTerm(kind="discount", scope="Accessories", discount_percent=10,
                               quote="Accessories carry a discount of 10 percent.", page=2),
                      pictured)

    assert term is not None and term.quotes[0]["page"] == 2


def test_the_same_term_from_two_parts_is_merged():
    first = draft_term(ReadTerm(kind="preferred_supplier", scope="IT equipment",
                                quote="IT equipment shall be purchased from Atea", page=3,
                                confidence=0.6), PAGES)
    second = draft_term(ReadTerm(kind="preferred_supplier", scope="it equipment",
                                 quote="when available from stock.", page=3,
                                 confidence=0.9), PAGES)

    (merged,) = merge_terms([first, second])

    assert len(merged.quotes) == 2
    assert merged.confidence == Decimal("0.900")
