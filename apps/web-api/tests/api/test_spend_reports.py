"""The spend reports over HTTP: tenant scope, period validation and currency separation."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from spend_books import Books
from web_api_testkit import auth

Q3 = {"from": "2026-07-01", "to": "2026-09-30"}
REPORTS = ("spend-overview", "spend-trend", "spend-breakdown", "spend-insights")


@pytest.fixture
def books(engine, seed):
    with Session(engine) as s:
        ours = Books(s, name="Acme Ledger", organization_id=seed["org_a"])
        theirs = Books(s, name="Beta Ledger", organization_id=seed["org_b"])
        ours.purchase(date(2026, 8, 3), "100.00", vendor=ours.supplier("Ours ApS"))
        theirs.purchase(date(2026, 8, 3), "900.00", vendor=theirs.supplier("Theirs ApS"))
        return {**seed, "ours": ours.company.id, "theirs": theirs.company.id}


def _get(client, report: str, token: str = "tokA", **params):
    return client.get(f"/api/v1/reports/{report}", params={**Q3, **params}, headers=auth(token))


@pytest.mark.parametrize("report", REPORTS)
def test_each_report_answers_for_the_period(client, books, report):
    res = _get(client, report)

    assert res.status_code == 200, res.text
    body = res.json()
    assert body["period"] == {"start": "2026-07-01", "end": "2026-09-30"}
    assert body["comparison"] == {"start": "2026-04-01", "end": "2026-06-30"}


def test_only_the_callers_spend_is_reported(client, books):
    rows = _get(client, "spend-overview").json()["rows"]

    assert [(row["currency"], Decimal(row["spend"])) for row in rows] == [("DKK", Decimal("100.00"))]


def test_the_suppliers_are_the_callers_own(client, books):
    (row,) = _get(client, "spend-breakdown").json()["rows"]

    assert [supplier["name"] for supplier in row["suppliers"]] == ["Ours ApS"]


@pytest.mark.parametrize("report", REPORTS)
def test_a_foreign_company_is_not_found(client, books, report):
    assert _get(client, report, company_id=books["theirs"]).status_code == 404


@pytest.mark.parametrize("report", REPORTS)
def test_a_period_that_ends_before_it_starts_is_refused(client, books, report):
    res = client.get(f"/api/v1/reports/{report}",
                     params={"from": "2026-09-30", "to": "2026-07-01"}, headers=auth("tokA"))

    assert res.status_code == 422


def test_a_period_is_required(client, books):
    assert client.get("/api/v1/reports/spend-overview", headers=auth("tokA")).status_code == 422


def test_the_supplier_limit_is_bounded(client, books):
    assert _get(client, "spend-breakdown", limit=51).status_code == 422
    assert _get(client, "spend-breakdown", limit=1).status_code == 200


def test_a_caller_without_companies_gets_no_rows(client, books):
    body = _get(client, "spend-overview", token="tok_empty").json()

    assert body["rows"] == []


def test_the_emissions_report_takes_the_same_scope(client, seed):
    res = client.get("/api/v1/reports/spend-emissions",
                     params={"from": "2026-09-01", "to": "2026-09-30"}, headers=auth("tokA"))

    assert res.status_code == 200, res.text
    assert res.json()["period"] == {"start": "2026-09-01", "end": "2026-09-30"}
