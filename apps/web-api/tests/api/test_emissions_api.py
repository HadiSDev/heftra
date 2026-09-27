"""Spend Lines' emissions over the API: per voucher and line, summarized, searched and corrected."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from emission_factors import Factors, euro_rates
from web_api.db.models import (
    AuditLog,
    Company,
    EmissionSectorSource,
    ErpEntry,
    InvoiceLine,
    SpendCategory,
    SpendTree,
)
from web_api_testkit import auth

_LIST = "/api/v1/erp-entries/vouchers"
_EMISSIONS = "/api/v1/erp-entries/vouchers/emissions"
_SECTORS = "/api/v1/emission-sectors"


@pytest.fixture
def books(engine, voucher_seed):
    """Voucher 4821 posted in DKK, its company Danish, and a rate to USD on its date."""
    with Session(engine) as s:
        for entry in s.exec(select(ErpEntry)).all():
            entry.base_currency = "DKK"
            entry.base_debit_amount = entry.debit_amount
            entry.base_credit_amount = entry.credit_amount
            s.add(entry)
        company = s.get(Company, voucher_seed["comp_a"])
        company.country_code = "DK"
        s.add(company)
        s.commit()
        euro_rates(s, date(2025, 7, 1), DKK="10", USD="1.45")
    return voucher_seed


@pytest.fixture
def hosting(engine) -> str:
    with Session(engine) as s:
        return Factors(s).sector("518200", "Data processing, hosting", {"DK": "0.5"}).id


def _set_line(engine, line_id: str, **fields) -> None:
    with Session(engine) as s:
        line = s.get(InvoiceLine, line_id)
        for name, value in fields.items():
            setattr(line, name, value)
        s.add(line)
        s.commit()


def _line(engine, line_id: str) -> InvoiceLine:
    with Session(engine) as s:
        return s.get(InvoiceLine, line_id)


def _voucher(client, voucher_id: str) -> dict:
    res = client.get(_LIST, headers=auth("tokA"))
    assert res.status_code == 200, res.text
    return next(item for item in res.json()["items"] if item["voucher_id"] == voucher_id)


def test_a_voucher_and_its_lines_carry_their_emissions(client, engine, books, hosting):
    _set_line(engine, books["line_a1"], emission_sector_id=hosting,
              emission_sector_source=EmissionSectorSource.AI,
              emission_sector_confidence=Decimal("0.4"), emission_sector_rationale="Servers.")

    voucher = _voucher(client, "4821")

    assert voucher["emissions_status"] == "partial"
    assert Decimal(voucher["kg_co2e"]) == Decimal("5.800")
    line = next(line for line in voucher["lines"] if line["id"] == books["line_a1"])
    assert Decimal(line["kg_co2e"]) == Decimal("5.800")
    assert line["emission_area"] == "DK"
    assert line["emission_sector"] == {"id": hosting, "code": "518200",
                                       "name": "Data processing, hosting"}
    assert line["emission_sector_rationale"] == "Servers."
    assert line["emission_needs_review"] is True


def test_the_summary_follows_the_filters(client, engine, books, hosting):
    _set_line(engine, books["line_a1"], emission_sector_id=hosting)

    res = client.get(_EMISSIONS, params={"company_id": books["comp_a"]}, headers=auth("tokA"))

    assert res.status_code == 200, res.text
    body = res.json()
    assert body["factor_set"]["attribution"] == "CEDA by Watershed"
    assert body["factor_set"]["price_year"] == 2023
    assert Decimal(body["kg_co2e"]) == Decimal("5.800")
    assert [(row["currency"], Decimal(row["posted_spend"]), Decimal(row["estimated_spend"]))
            for row in body["spend"]] == [("DKK", Decimal("110.00"), Decimal("80.00"))]
    assert body["vouchers_by_status"] == {"partial": 1, "no_lines": 1}


def test_without_a_factor_set_nothing_is_estimated(client, books):
    body = client.get(_EMISSIONS, headers=auth("tokA")).json()

    assert body["factor_set"] is None
    assert body["kg_co2e"] is None
    assert body["vouchers_by_status"] == {"no_factor_set": 2}


def test_another_organizations_company_is_not_found(client, books):
    res = client.get(_EMISSIONS, params={"company_id": books["comp_a"]}, headers=auth("tokB"))

    assert res.status_code == 404


def test_sectors_are_searched_by_name_or_code(client, engine, books, hosting):
    with Session(engine) as s:
        Factors(s, active=False, version="old", classification="other").sector(
            "999", "Hosting elsewhere", {})

    by_name = client.get(_SECTORS, params={"q": "HOST"}, headers=auth("tokA")).json()
    by_code = client.get(_SECTORS, params={"q": "5182"}, headers=auth("tokA")).json()

    assert [sector["code"] for sector in by_name] == ["518200"]
    assert [sector["code"] for sector in by_code] == ["518200"]


def test_no_active_set_offers_no_sectors(client, books):
    assert client.get(_SECTORS, headers=auth("tokA")).json() == []


def test_a_reviewer_chooses_a_sector(client, engine, books, hosting):
    res = client.patch(f"/api/v1/invoice-lines/{books['line_a2']}",
                       json={"emission_sector_id": hosting}, headers=auth("tokA"))

    assert res.status_code == 200, res.text
    line = _line(engine, books["line_a2"])
    assert (line.emission_sector_id, line.emission_sector_source) == (hosting, "human")
    with Session(engine) as s:
        audit = s.exec(select(AuditLog).where(AuditLog.entity_id == books["line_a2"])).all()
    changed = [change["field"] for entry in audit for change in entry.changes]
    assert "emission_sector_id" in changed


def test_clearing_a_sector_frees_the_line_for_matching(client, engine, books, hosting):
    _set_line(engine, books["line_a1"], emission_sector_id=hosting,
              emission_sector_source=EmissionSectorSource.HUMAN)

    client.patch(f"/api/v1/invoice-lines/{books['line_a1']}",
                 json={"emission_sector_id": None}, headers=auth("tokA"))

    line = _line(engine, books["line_a1"])
    assert (line.emission_sector_id, line.emission_sector_source) == (None, None)


def test_a_sector_outside_the_active_set_is_refused(client, engine, books, hosting):
    with Session(engine) as s:
        other = Factors(s, active=False, version="old", classification="other").sector(
            "999", "Elsewhere", {}).id

    res = client.patch(f"/api/v1/invoice-lines/{books['line_a1']}",
                       json={"emission_sector_id": other}, headers=auth("tokA"))

    assert res.status_code == 422
    assert _line(engine, books["line_a1"]).emission_sector_id is None


def test_editing_the_description_forgets_an_ai_sector(client, engine, books, hosting):
    _set_line(engine, books["line_a1"], emission_sector_id=hosting,
              emission_sector_source=EmissionSectorSource.AI,
              emission_sector_confidence=Decimal("0.9"))

    client.patch(f"/api/v1/invoice-lines/{books['line_a1']}",
                 json={"description": "Colocation rack"}, headers=auth("tokA"))

    line = _line(engine, books["line_a1"])
    assert (line.emission_sector_id, line.emission_sector_confidence) == (None, None)


def test_editing_the_description_keeps_a_human_sector(client, engine, books, hosting):
    _set_line(engine, books["line_a1"], emission_sector_id=hosting,
              emission_sector_source=EmissionSectorSource.HUMAN)

    client.patch(f"/api/v1/invoice-lines/{books['line_a1']}",
                 json={"description": "Colocation rack"}, headers=auth("tokA"))

    assert _line(engine, books["line_a1"]).emission_sector_id == hosting


def test_recategorizing_forgets_an_ai_sector(client, engine, books, hosting):
    with Session(engine) as s:
        tree = SpendTree(organization_id=books["org_a"], name="Tree")
        s.add(tree)
        s.commit()
        node = SpendCategory(spend_tree_id=tree.id, depth=1, name="Technology", code="T",
                             level_1="Technology")
        s.add(node)
        company = s.get(Company, books["comp_a"])
        company.spend_tree_id = tree.id
        s.add(company)
        s.commit()
        node_id = node.id
    _set_line(engine, books["line_a1"], emission_sector_id=hosting,
              emission_sector_source=EmissionSectorSource.AI)

    res = client.post(f"/api/v1/invoice-lines/{books['line_a1']}/verify",
                      json={"spend_category_id": node_id}, headers=auth("tokA"))

    assert res.status_code == 200, res.text
    assert _line(engine, books["line_a1"]).emission_sector_id is None


def test_an_emissions_matching_run_can_be_requested(client, books):
    res = client.post(f"/api/v1/companies/{books['comp_a']}/runs",
                      json={"kind": "match_emissions"}, headers=auth("tok_sysadmin"))

    assert res.status_code == 201, res.text
    assert res.json()["kind"] == "match_emissions"


def test_an_estimated_line_carries_the_calculation_that_multiplies_out(client, engine, books,
                                                                       hosting):
    _set_line(engine, books["line_a1"], emission_sector_id=hosting,
              emission_sector_source=EmissionSectorSource.AI)

    line = next(line for line in _voucher(client, "4821")["lines"]
                if line["id"] == books["line_a1"])

    calculation = line["emission_calculation"]
    assert (Decimal(calculation["spend"]), calculation["currency"]) == (Decimal("80.00"), "DKK")
    assert Decimal(calculation["rate"]) == Decimal("0.145")
    assert calculation["rate_date"] == "2025-07-01"
    assert Decimal(calculation["converted"]) == Decimal("11.60")
    assert (Decimal(calculation["factor"]), calculation["factor_currency"]) == (Decimal("0.5"),
                                                                                "USD")
    assert calculation["factor_area"] == "DK"
    assert calculation["sector"]["code"] == "518200"
    assert Decimal(calculation["kg_co2e"]) == Decimal("5.800")


def test_a_line_without_an_estimate_carries_no_calculation(client, engine, books, hosting):
    line = next(line for line in _voucher(client, "4821")["lines"]
                if line["id"] == books["line_a2"])

    assert line["emission_calculation"] is None


def test_the_voucher_detail_carries_the_calculation_too(client, engine, books, hosting):
    _set_line(engine, books["line_a1"], emission_sector_id=hosting,
              emission_sector_source=EmissionSectorSource.AI)

    res = client.get("/api/v1/erp-entries/vouchers/4821", headers=auth("tokA"))

    assert res.status_code == 200, res.text
    line = next(line for line in res.json()["invoice"]["lines"]
                if line["id"] == books["line_a1"])
    assert Decimal(line["emission_calculation"]["kg_co2e"]) == Decimal("5.800")
