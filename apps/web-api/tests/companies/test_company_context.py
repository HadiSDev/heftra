"""What a company does: its website and description, researched or written by a manager."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session

from web_api.company_context import HUMAN, RESEARCHED
from web_api.db.models import Company


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _patch(client, company_id: str, body: dict):
    return client.patch(f"/api/v1/companies/{company_id}", json=body, headers=_auth("tokA"))


def _researched(engine, company_id: str, website: str = "https://vectorlab.dk/") -> None:
    with Session(engine) as s:
        company = s.get(Company, company_id)
        company.website = website
        company.description = "Builds software for wearables."
        company.description_source = RESEARCHED
        company.researched_at = datetime.now(timezone.utc)
        s.add(company)
        s.commit()


def test_a_website_is_stored_as_its_site_root(client, engine, seed):
    response = _patch(client, seed["comp_a"], {"website": "VectorLab.dk/about"})

    assert response.status_code == 200
    assert response.json()["website"] == "https://vectorlab.dk/"


def test_something_that_is_not_a_website_is_refused(client, seed):
    assert _patch(client, seed["comp_a"], {"website": "not a site"}).status_code == 422


def test_a_new_website_is_researched_again(client, engine, seed):
    _researched(engine, seed["comp_a"])

    body = _patch(client, seed["comp_a"], {"website": "https://vectorlab.io"}).json()

    assert (body["website"], body["description"]) == ("https://vectorlab.io/", None)
    with Session(engine) as s:
        assert s.get(Company, seed["comp_a"]).researched_at is None


def test_a_manager_s_description_is_kept_over_research(client, engine, seed):
    _researched(engine, seed["comp_a"])

    _patch(client, seed["comp_a"], {"description": "  We build apps for smartwatches.  "})
    body = _patch(client, seed["comp_a"], {"website": "https://vectorlab.io"}).json()

    assert body["description"] == "We build apps for smartwatches."
    assert body["description_source"] == HUMAN


def test_clearing_the_description_asks_for_research_again(client, engine, seed):
    _researched(engine, seed["comp_a"])

    body = _patch(client, seed["comp_a"], {"description": ""}).json()

    assert (body["description"], body["description_source"]) == (None, None)
    with Session(engine) as s:
        assert s.get(Company, seed["comp_a"]).researched_at is None


def test_a_company_is_created_with_its_website(client, seed):
    response = client.post("/api/v1/companies", json={
        "name": "New Co", "base_currency": "DKK", "website": "newco.dk",
        "integration": {"erp_type": "mock", "credentials": {}},
    }, headers=_auth("tokA"))

    assert response.status_code == 201
    assert response.json()["website"] == "https://newco.dk/"
