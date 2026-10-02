"""Alternatives over the API: the list, an item, correcting its specification, asking for a
search, reviewing an alternative, and the organization's benchmark setting."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from web_api.db.models import AuditLog, CompanyItem, ItemAlternative, Organization, PipelineRun
from web_api_testkit import auth

CABLE = {"item_class": "material", "product_type": "network installation cable",
         "name": "Cat6 U/UTP", "pricing_unit": "m", "units_per_line_unit": 305,
         "confidence": 0.9, "attributes": []}
NOW = datetime(2026, 6, 1, tzinfo=timezone.utc)


def _item(s, company_id, name, *, spec=None, unit_price=None) -> CompanyItem:
    item = CompanyItem(company_id=company_id, item_key=f"key-{name}", item_name=name, unit="stk",
                       base_currency="DKK", lines=4, spend=Decimal("3660"),
                       line_quantity=Decimal("4"), priced_spend=Decimal("3660"), spec=spec,
                       item_class=(spec or {}).get("item_class"), unit_price=unit_price)
    s.add(item)
    s.flush()
    return item


def _alternative(s, item, *, source="history", saving="732", ref="item:x") -> ItemAlternative:
    alternative = ItemAlternative(
        company_id=item.company_id, item_id=item.id, source=source, match="exact", ref_key=ref,
        name=item.item_name, unit_price=Decimal("2.40"), currency="DKK",
        saving_yearly=Decimal(saving), saving_percent=Decimal("20"),
        comparison=[{"name": "category", "item": "Cat6", "candidate": "Cat6", "verdict": "same",
                     "reason": ""}],
        origin={"supplier": "Proshop"}, found_at=NOW)
    s.add(alternative)
    s.flush()
    return alternative


@pytest.fixture
def stocked(engine, seed) -> dict:
    with Session(engine) as s:
        cable = _item(s, seed["comp_a"], "Cat6 cable", spec=CABLE, unit_price=Decimal("3"))
        laptop = _item(s, seed["comp_a"], "ThinkPad")
        _alternative(s, cable)
        best = _alternative(s, laptop, source="marketplace", saving="4200", ref="offer:shop:1")
        _alternative(s, laptop, saving="100", ref="item:y")
        other = _item(s, seed["comp_b"], "Beta paper")
        _alternative(s, other)
        s.commit()
        return {"cable": cable.id, "laptop": laptop.id, "best": best.id, "other": other.id}


def test_items_are_listed_by_their_best_saving_with_the_total(client, seed, stocked):
    body = client.get("/api/v1/alternatives", headers=auth("tokA")).json()

    assert [item["id"] for item in body["items"]] == [stocked["laptop"], stocked["cable"]]
    assert body["items"][0]["best"]["id"] == stocked["best"]
    assert body["items"][0]["alternatives"] == 2
    assert (Decimal(body["total_saving"]), body["currency"], body["total"]) == \
        (Decimal("4932"), "DKK", 2)


def test_the_list_filters_by_source_and_class(client, seed, stocked):
    by_source = client.get("/api/v1/alternatives?source=marketplace", headers=auth("tokA")).json()
    by_class = client.get("/api/v1/alternatives?item_class=material", headers=auth("tokA")).json()

    assert [item["id"] for item in by_source["items"]] == [stocked["laptop"]]
    assert [item["id"] for item in by_class["items"]] == [stocked["cable"]]


def test_another_organizations_items_are_not_found(client, seed, stocked):
    listed = client.get("/api/v1/alternatives", headers=auth("tokA")).json()
    assert stocked["other"] not in [item["id"] for item in listed["items"]]
    assert client.get(f"/api/v1/items/{stocked['other']}",
                      headers=auth("tokA")).status_code == 404


def test_an_item_shows_its_specification_and_alternatives(client, seed, stocked):
    body = client.get(f"/api/v1/items/{stocked['cable']}", headers=auth("tok_viewerA")).json()

    assert body["spec"]["pricing_unit"] == "m"
    assert (Decimal(body["unit_price"]), body["searching"]) == (Decimal("3"), False)
    assert body["alternatives"][0]["comparison"][0]["verdict"] == "same"


def test_a_corrected_specification_prices_the_item_and_searches_it_again(client, engine, seed,
                                                                        stocked):
    res = client.patch(f"/api/v1/items/{stocked['laptop']}/specification", headers=auth("tokA"),
                       json={**CABLE, "units_per_line_unit": 8, "pricing_unit": "roll"})

    assert res.status_code == 200, res.text
    body = res.json()
    assert (Decimal(body["unit_price"]), body["spec_source"], body["searching"]) == \
        (Decimal("114.375"), "human", True)
    with Session(engine) as s:
        assert s.exec(select(AuditLog).where(AuditLog.entity_id == stocked["laptop"])).one()


def test_a_viewer_cannot_correct_a_specification_or_ask_for_a_search(client, seed, stocked):
    assert client.patch(f"/api/v1/items/{stocked['cable']}/specification",
                        headers=auth("tok_viewerA"), json=CABLE).status_code == 403
    assert client.post(f"/api/v1/items/{stocked['cable']}/find-alternatives",
                       headers=auth("tok_viewerA")).status_code == 403


def test_asking_twice_reuses_the_queued_search(client, engine, seed, stocked):
    first = client.post(f"/api/v1/items/{stocked['cable']}/find-alternatives",
                        headers=auth("tokA"))
    second = client.post(f"/api/v1/items/{stocked['cable']}/find-alternatives",
                         headers=auth("tokA"))

    assert first.status_code == 202
    assert first.json()["id"] == second.json()["id"]
    with Session(engine) as s:
        (run,) = s.exec(select(PipelineRun)).all()
        assert (run.kind, run.params) == ("find_alternatives", {"item_id": stocked["cable"]})


def test_a_dismissal_needs_its_reason_and_is_audited(client, engine, seed, stocked):
    url = f"/api/v1/alternatives/{stocked['best']}"
    assert client.patch(url, headers=auth("tokA"),
                        json={"review_status": "dismissed"}).status_code == 422

    body = client.patch(url, headers=auth("tokA"), json={
        "review_status": "dismissed", "dismiss_reason": "supplier_not_approved",
        "note": "Not an approved shop"}).json()

    assert (body["review_status"], body["dismiss_reason"], body["reviewed_by_name"]) == \
        ("dismissed", "supplier_not_approved", "Alice")
    reopened = client.patch(url, headers=auth("tokA"), json={"review_status": "open"}).json()
    assert (reopened["dismiss_reason"], reopened["review_note"]) == (None, None)
    with Session(engine) as s:
        assert len(s.exec(select(AuditLog).where(AuditLog.entity_id == stocked["best"])).all()) == 2


def test_a_lines_item_is_stored_when_it_is_first_searched(client, engine, seed):
    url = f"/api/v1/invoice-lines/{seed['line_a1']}"
    assert client.get(f"{url}/item", headers=auth("tokA")).status_code == 404

    res = client.post(f"{url}/find-alternatives", headers=auth("tokA"))

    assert res.status_code == 202, res.text
    assert res.json()["searching"] is True
    assert client.get(f"{url}/item", headers=auth("tokA")).json()["id"] == res.json()["id"]
    listed = client.get("/api/v1/invoice-lines", headers=auth("tokA")).json()["items"]
    (line,) = [entry for entry in listed if entry["id"] == seed["line_a1"]]
    assert line["item_key"] is not None


def test_an_admin_opts_the_organization_out_of_the_benchmark(client, engine, seed):
    res = client.patch("/api/v1/organization", headers=auth("tokA"),
                       json={"price_benchmark_enabled": False})

    assert (res.status_code, res.json()["price_benchmark_enabled"]) == (200, False)
    with Session(engine) as s:
        assert s.get(Organization, seed["org_a"]).price_benchmark_enabled is False
        assert s.exec(select(AuditLog).where(AuditLog.entity_type == "organization")).one()
    assert client.patch("/api/v1/organization", headers=auth("tokA"),
                        json={"price_benchmark_enabled": None}).status_code == 422
    assert client.patch("/api/v1/organization", headers=auth("tok_moderatorA"),
                        json={"price_benchmark_enabled": True}).status_code == 403


def test_the_run_endpoint_refuses_an_item_search_without_an_item(client, seed):
    res = client.post(f"/api/v1/companies/{seed['comp_a']}/runs", headers=auth("tok_sysadmin"),
                      json={"kind": "find_alternatives"})
    assert res.status_code == 422
