"""Rates fetched while reading are kept, and a page's stored rates load in one query."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import event
from sqlmodel import Session, select

from web_api.db.models import FxRate
from web_api.fx import FxService

FRIDAY = date(2026, 3, 6)
SATURDAY = date(2026, 3, 7)
MONDAY = date(2026, 3, 9)
RATES = {"EUR": Decimal("1"), "DKK": Decimal("7.4600"), "USD": Decimal("1.0850")}


class StubProvider:
    def __init__(self, published: date = FRIDAY):
        self.published = published
        self.calls: list[date] = []

    def fetch(self, rate_date: date):
        self.calls.append(rate_date)
        return self.published, dict(RATES)


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def _stored(engine) -> set[tuple[str, date]]:
    with Session(engine) as s:
        return {(row.quote_currency, row.rate_date) for row in s.exec(select(FxRate))}


def test_a_read_keeps_what_it_fetched_without_committing_the_request(session, engine):
    provider = StubProvider()

    rate = FxService.for_reads(session, provider).get_rate("DKK", "USD", SATURDAY)
    session.rollback()

    assert rate is not None
    assert ("USD", SATURDAY) in _stored(engine)
    assert ("USD", FRIDAY) in _stored(engine)


def test_the_next_read_uses_the_stored_rates(session, engine):
    first = StubProvider()
    FxService.for_reads(session, first).get_rate("DKK", "USD", SATURDAY)
    second = StubProvider()

    with Session(engine) as later:
        FxService.for_reads(later, second).get_rate("DKK", "USD", SATURDAY)

    assert first.calls == [SATURDAY]
    assert second.calls == []


def test_a_write_path_leaves_fetched_rates_to_its_own_commit(session, engine):
    FxService(session, StubProvider()).get_rate("DKK", "USD", SATURDAY)
    session.rollback()

    assert _stored(engine) == set()


def test_prefetch_loads_every_date_in_one_query(session, engine):
    for day in (FRIDAY, MONDAY):
        for currency, rate in RATES.items():
            session.add(FxRate(quote_currency=currency, rate_date=day, published_date=day,
                               rate=rate, source="test"))
    session.commit()
    provider = StubProvider()
    service = FxService.for_reads(session, provider)
    statements: list[str] = []

    def count(conn, cursor, statement, params, context, executemany):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", count)
    try:
        service.prefetch([FRIDAY, MONDAY])
        friday = service.get_rate("DKK", "USD", FRIDAY)
        monday = service.get_rate("DKK", "USD", MONDAY)
    finally:
        event.remove(engine, "before_cursor_execute", count)

    assert len(statements) == 1
    assert friday is not None and monday is not None
    assert provider.calls == []
