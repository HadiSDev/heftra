"""Runs that judge items once, redo only what changed, survive a crash, and keep totals right."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from agreement_books import Books, Judge, embed, item_index
from ai_api import config
from ai_api.compliance import agreement_run
from ai_api.compliance.run import analyse_company
from ai_api.compliance.scope import RunScope, run_scope
from ai_api.items.index import ItemIndex
from web_api.db.models import (
    Agreement,
    AgreementFinding,
    AgreementScopeJudgement,
    AgreementTermKind,
    AgreementTermSpend,
    Invoice,
    InvoiceLine,
)

LONG_AGO = datetime(2020, 1, 1, tzinfo=timezone.utc)


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def books(session) -> Books:
    return Books(session)


@pytest.fixture
def analyse(session, books):
    """Runs analysis for the company, with one item index kept across the test's runs, as
    Qdrant keeps it between runs."""
    shared = item_index()

    def run(judge, *, index=None):
        return analyse_company(session, books.company.id, ask=judge, embed_fn=embed,
                               index=index or shared)

    return run


def _age_everything(session) -> None:
    for row in [*session.exec(select(InvoiceLine)).all(), *session.exec(select(Invoice)).all()]:
        row.changed_at = LONG_AGO
        session.add(row)
    session.commit()


def _findings(session) -> list[AgreementFinding]:
    return list(session.exec(select(AgreementFinding)).all())


def test_many_identical_lines_are_one_question(session, books, analyse):
    agreement = books.agreement()
    books.term(agreement, AgreementTermKind.PREFERRED_SUPPLIER, "Laptops")
    for _ in range(300):
        books.line(books.proshop, "Dell Latitude laptop", unit_price="9000")
    judge = Judge(("laptop",))

    summary = analyse(judge)

    assert judge.questions == 1
    assert (summary["candidates"], summary["lines"]) == (1, 300)
    assert len(_findings(session)) == 300


def test_a_run_after_a_sync_reads_only_the_new_lines(session, books, analyse):
    agreement = books.agreement()
    books.term(agreement, AgreementTermKind.PREFERRED_SUPPLIER, "Laptops")
    for _ in range(5):
        books.line(books.proshop, "Dell laptop", unit_price="9000")
    analyse(Judge(("laptop",)))
    _age_everything(session)
    books.line(books.proshop, "HP laptop", unit_price="7000")

    summary = analyse(Judge(("laptop",)))

    assert summary["runs"] == {agreement.id: "incremental"}
    assert (summary["lines"], summary["judged"]) == (1, 1)
    assert len(_findings(session)) == 6


def test_a_recategorized_line_is_checked_again(session, books, analyse):
    agreement = books.agreement()
    books.term(agreement, AgreementTermKind.PREFERRED_SUPPLIER, "Laptops")
    tree = books.tree("Office Equipment", "Hardware")
    line = books.line(books.proshop, "Dell laptop", unit_price="9000",
                      category=tree["Office Equipment"])
    books.line(books.proshop, "HP laptop", unit_price="7000", category=tree["Office Equipment"])
    analyse(Judge(("laptop",)))
    _age_everything(session)

    moved = session.get(InvoiceLine, line.id)
    moved.spend_category_id = tree["Hardware"].id
    session.add(moved)
    session.commit()
    summary = analyse(Judge(("laptop",)))

    assert summary["lines"] == 1


def test_an_edited_term_redoes_all_its_lines(session, books, analyse):
    agreement = books.agreement()
    term = books.term(agreement, AgreementTermKind.PREFERRED_SUPPLIER, "Laptops")
    for _ in range(4):
        books.line(books.proshop, "Dell laptop", unit_price="9000")
    analyse(Judge(("laptop",)))
    _age_everything(session)

    term.scope = "Laptops and notebooks"
    term.updated_at = datetime.now(timezone.utc)
    session.add(term)
    session.commit()
    summary = analyse(Judge(("laptop",)))

    assert (summary["lines"], summary["judged"]) == (4, 1)


def test_a_run_that_stops_part_way_is_redone_without_duplicates(session, books, monkeypatch,
                                                                analyse):
    agreement = books.agreement()
    books.term(agreement, AgreementTermKind.PREFERRED_SUPPLIER, "Laptops")
    for _ in range(3):
        books.line(books.proshop, "Dell laptop", unit_price="9000")
    monkeypatch.setattr(config, "AGREEMENT_PAGE_SIZE", 1)
    written = []
    real_write = agreement_run.write_page

    def crash_on_second_page(*args, **kwargs):
        if written:
            raise RuntimeError("worker stopped")
        written.append(1)
        return real_write(*args, **kwargs)

    monkeypatch.setattr(agreement_run, "write_page", crash_on_second_page)
    with pytest.raises(RuntimeError):
        analyse(Judge(("laptop",)))
    session.rollback()
    assert session.get(Agreement, agreement.id).analysed_from is None
    assert len(_findings(session)) == 1

    monkeypatch.setattr(agreement_run, "write_page", real_write)
    summary = analyse(Judge(("laptop",)))

    assert summary["runs"] == {agreement.id: "full"}
    assert len(_findings(session)) == 3


def test_totals_follow_a_judgement_that_flips(session, books, analyse):
    agreement = books.agreement()
    books.term(agreement, AgreementTermKind.VOLUME_COMMITMENT, "Laptops",
               commitment_amount=Decimal("100000"), commitment_period="year")
    books.line(books.atea, "Dell laptop", unit_price="9000")
    books.line(books.atea, "HP laptop", unit_price="7000")
    analyse(Judge(("laptop",)))

    flipped = session.exec(select(AgreementScopeJudgement)).all()[0]
    flipped.in_scope = False
    session.add(flipped)
    agreement.full_analysis = True
    session.add(agreement)
    session.commit()
    analyse(Judge(("laptop",)))

    (total,) = session.exec(select(AgreementTermSpend)).all()
    assert (total.month, total.from_supplier, total.lines) == (date(2026, 3, 1), True, 1)


def test_candidates_come_from_categories_when_the_index_is_down(session, books, analyse):
    class Broken:
        def get_collections(self):
            raise ConnectionError("qdrant down")

    tree = books.tree("Office Equipment")
    agreement = books.agreement()
    books.term(agreement, AgreementTermKind.PREFERRED_SUPPLIER, "Laptops",
               scope_category_ids=[tree["Office Equipment"].id])
    books.line(books.proshop, "Dell laptop", unit_price="9000", category=tree["Office Equipment"])

    summary = analyse(Judge(("laptop",)), index=ItemIndex(Broken(), embed))

    assert summary["similarity"] is False
    assert len(_findings(session)) == 1


def test_similarity_finds_items_outside_the_term_s_categories(session, books, analyse):
    tree = books.tree("Office Equipment", "Other")
    agreement = books.agreement()
    books.term(agreement, AgreementTermKind.PREFERRED_SUPPLIER, "Laptops",
               scope_category_ids=[tree["Office Equipment"].id])
    misfiled = books.line(books.proshop, "Dell laptop", unit_price="9000",
                          category=tree["Other"])

    analyse(Judge(("laptop",)))

    assert [finding.invoice_line_id for finding in _findings(session)] == [misfiled.id]


def test_a_term_with_too_many_candidates_is_capped_most_spend_first(session, books, monkeypatch,
                                                                    analyse):
    monkeypatch.setattr(config, "AGREEMENT_CANDIDATES_MAX", 1)
    agreement = books.agreement()
    books.term(agreement, AgreementTermKind.PREFERRED_SUPPLIER, "Laptops")
    big = books.line(books.proshop, "Dell laptop", unit_price="9000")
    books.line(books.proshop, "HP laptop", unit_price="7000")

    summary = analyse(Judge(("laptop",)))

    assert summary["capped_terms"] == 1
    assert [finding.invoice_line_id for finding in _findings(session)] == [big.id]


def test_a_first_run_or_a_requested_one_is_full(session, books):
    agreement = books.agreement()
    assert run_scope(agreement).full
    agreement.analysed_from = datetime.now(timezone.utc)
    assert not run_scope(agreement).full
    agreement.full_analysis = True
    assert run_scope(agreement).full


def test_a_term_confirmed_after_the_watermark_is_redone_in_full(session, books):
    agreement = books.agreement()
    term = books.term(agreement, AgreementTermKind.PREFERRED_SUPPLIER, "Laptops")
    since = datetime(2020, 1, 1, tzinfo=timezone.utc)

    later = datetime(2100, 1, 1, tzinfo=timezone.utc)
    assert RunScope(since, since).since_for(term) is None
    assert RunScope(later, later).since_for(term) == later
