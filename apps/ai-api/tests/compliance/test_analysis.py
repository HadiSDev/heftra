"""Checking spend lines against an agreement's confirmed terms, rule by rule."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from agreement_books import Books, Judge, embed
from ai_api.compliance.run import analyse_company
from web_api.db.models import (
    AgreementFinding,
    AgreementTermKind,
    AgreementTermStatus,
    FindingReviewStatus,
    Invoice,
)


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def books(session) -> Books:
    return Books(session)


def _analyse(session, books, judge):
    return analyse_company(session, books.company.id, ask=judge, embed_fn=embed)


def _findings(session) -> dict[tuple[str, str], AgreementFinding]:
    rows = session.exec(select(AgreementFinding)).all()
    return {(row.kind, row.invoice_line_id): row for row in rows}


def test_a_laptop_from_a_webshop_is_an_off_contract_rule_break(session, books):
    agreement = books.agreement()
    books.term(agreement, AgreementTermKind.PREFERRED_SUPPLIER, "IT equipment such as laptops",
               conditions="when available from stock")
    webshop = books.line(books.proshop, "Dell Latitude 5450 laptop", unit_price="9200")
    ours = books.line(books.atea, "Lenovo ThinkPad T14 laptop", unit_price="8000")
    books.line(books.proshop, "Coffee beans", unit_price="120")

    summary = _analyse(session, books, Judge(("laptop",)))

    found = _findings(session)
    off = found[("off_contract", webshop.id)]
    assert (off.severity, off.amount, off.from_supplier) == ("rule_break", Decimal("9200.00"),
                                                            False)
    assert "when available from stock" in off.reason and "Proshop A/S" in off.reason
    assert found[("compliant", ours.id)].from_supplier is True
    assert summary["findings"] == {"off_contract": 1, "compliant": 1}


def test_an_overcharged_laptop(session, books):
    agreement = books.agreement()
    books.term(agreement, AgreementTermKind.AGREED_PRICE, "Laptops",
               item="ThinkPad T14", unit="unit", unit_price=Decimal("8000"))
    line = books.line(books.atea, "Lenovo ThinkPad T14 Gen 5 laptop", quantity="3",
                      unit_price="8400")

    _analyse(session, books, Judge(("thinkpad",), item="ThinkPad T14"))

    overcharge = _findings(session)[("overcharge", line.id)]
    assert overcharge.amount == Decimal("1200.00")
    assert (overcharge.expected, overcharge.actual) == (Decimal("8000"), Decimal("8400.0000"))


def test_a_box_against_a_unit_price_is_unverifiable(session, books):
    agreement = books.agreement()
    books.term(agreement, AgreementTermKind.AGREED_PRICE, "Laptops",
               item="ThinkPad T14", unit="unit", unit_price=Decimal("8000"))
    line = books.line(books.atea, "ThinkPad T14 laptop, box of 10", unit="box",
                      unit_price="84000")

    _analyse(session, books, Judge(("thinkpad",), item="ThinkPad T14", per_box=True))

    assert list(_findings(session)) == [("price_unverifiable", line.id)]


def test_the_same_item_dearer_elsewhere_is_a_potential_saving(session, books):
    agreement = books.agreement()
    books.term(agreement, AgreementTermKind.AGREED_PRICE, "Laptops",
               item="ThinkPad T14", unit="unit", unit_price=Decimal("8000"))
    line = books.line(books.proshop, "ThinkPad T14 laptop", quantity="2", unit_price="9000")

    _analyse(session, books, Judge(("thinkpad",), item="ThinkPad T14"))

    saving = _findings(session)[("potential_saving", line.id)]
    assert (saving.severity, saving.amount) == ("info", Decimal("2000.00"))


def test_a_missing_discount_and_one_that_is_given(session, books):
    agreement = books.agreement()
    books.term(agreement, AgreementTermKind.DISCOUNT, "Accessories such as docks and cables",
               discount_percent=Decimal("10"))
    missing = books.line(books.atea, "USB-C dock", unit_price="1000")
    given = books.line(books.atea, "USB-C cable", quantity="10", unit_price="100", amount="900")
    elsewhere = books.line(books.proshop, "Thunderbolt dock", unit_price="2000")

    _analyse(session, books, Judge(("dock", "cable")))

    found = _findings(session)
    assert found[("missed_discount", missing.id)].amount == Decimal("100.00")
    assert ("compliant", given.id) in found
    assert found[("potential_saving", elsewhere.id)].amount == Decimal("200.00")


def test_a_discount_line_on_the_invoice_counts(session, books):
    agreement = books.agreement()
    books.term(agreement, AgreementTermKind.DISCOUNT, "Docks", discount_percent=Decimal("10"))
    dock = books.line(books.atea, "USB-C dock", unit_price="1000")
    books.line(books.atea, "Framework discount", unit_price="-100", amount="-100",
               invoice=session.get(Invoice, dock.invoice_id))

    _analyse(session, books, Judge(("dock",)))

    assert ("compliant", dock.id) in _findings(session)


def test_commitment_spend_is_recorded_as_compliant(session, books):
    agreement = books.agreement()
    books.term(agreement, AgreementTermKind.VOLUME_COMMITMENT, "Laptops",
               commitment_amount=Decimal("500000"), commitment_period="year")
    ours = books.line(books.atea, "ThinkPad laptop", unit_price="8000")
    books.line(books.proshop, "Dell laptop", unit_price="9000")

    _analyse(session, books, Judge(("laptop",)))

    found = _findings(session)
    assert list(found) == [("compliant", ours.id)]
    assert found[("compliant", ours.id)].line_amount == Decimal("8000")


def test_lines_before_the_agreement_are_not_checked(session, books):
    agreement = books.agreement(starts_on=date(2026, 6, 1))
    books.term(agreement, AgreementTermKind.PREFERRED_SUPPLIER, "Laptops")
    books.line(books.proshop, "Dell laptop", unit_price="9000", on=date(2026, 3, 1))

    _analyse(session, books, Judge(("laptop",)))

    assert _findings(session) == {}


def test_a_second_run_only_asks_about_new_lines(session, books):
    agreement = books.agreement()
    books.term(agreement, AgreementTermKind.PREFERRED_SUPPLIER, "Laptops")
    books.line(books.proshop, "Dell laptop", unit_price="9000")
    judge = Judge(("laptop",))
    _analyse(session, books, judge)
    books.line(books.proshop, "HP laptop", unit_price="7000")

    summary = _analyse(session, books, judge)

    assert (summary["judged"], summary["cached"]) == (1, 1)


def test_an_accepted_exception_survives_a_rerun(session, books):
    agreement = books.agreement()
    books.term(agreement, AgreementTermKind.PREFERRED_SUPPLIER, "Laptops")
    line = books.line(books.proshop, "Dell laptop", unit_price="9000")
    _analyse(session, books, Judge(("laptop",)))
    finding = _findings(session)[("off_contract", line.id)]
    finding.review_status = FindingReviewStatus.EXCEPTION.value
    finding.review_note = "Atea out of stock"
    session.add(finding)
    session.commit()

    _analyse(session, books, Judge(("laptop",)))

    kept = _findings(session)[("off_contract", line.id)]
    assert (kept.review_status, kept.review_note) == ("exception", "Atea out of stock")


def test_a_line_ruled_out_of_scope_is_not_raised_again(session, books):
    agreement = books.agreement()
    books.term(agreement, AgreementTermKind.PREFERRED_SUPPLIER, "Laptops")
    line = books.line(books.proshop, "Laptop sleeve", unit_price="200")
    _analyse(session, books, Judge(("laptop",)))
    finding = _findings(session)[("off_contract", line.id)]
    finding.review_status = FindingReviewStatus.NOT_IN_SCOPE.value
    session.add(finding)
    session.commit()
    judge = Judge(("laptop",))

    _analyse(session, books, judge)

    assert judge.questions == 0
    assert _findings(session)[("off_contract", line.id)].review_status == "not_in_scope"


def test_a_rejected_term_loses_its_findings(session, books):
    agreement = books.agreement()
    term = books.term(agreement, AgreementTermKind.PREFERRED_SUPPLIER, "Laptops")
    books.line(books.proshop, "Dell laptop", unit_price="9000")
    _analyse(session, books, Judge(("laptop",)))
    term.status = AgreementTermStatus.REJECTED.value
    session.add(term)
    session.commit()

    _analyse(session, books, Judge(("laptop",)))

    assert _findings(session) == {}


def test_an_unparseable_answer_is_counted_not_guessed(session, books):
    agreement = books.agreement()
    books.term(agreement, AgreementTermKind.PREFERRED_SUPPLIER, "Laptops")
    books.line(books.proshop, "Dell laptop", unit_price="9000")

    def broken(prompt):
        raise RuntimeError("timed out")

    summary = _analyse(session, books, broken)

    assert summary["unjudged"] == 1
    assert _findings(session) == {}


def test_without_an_active_agreement_nothing_happens(session, books):
    summary = _analyse(session, books, Judge(("laptop",)))

    assert summary["agreements"] == 0
