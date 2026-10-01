"""Researching what a company does from its website."""
from __future__ import annotations

from sqlmodel import Session

from ai_api import config
from ai_api.enrichment.company import research_pending_companies
from ai_api.enrichment.supplier_profile import SupplierProfile
from web_api.company_context import HUMAN, RESEARCHED
from web_api.db.models import Company


def _with_website(engine, company_id: str, website: str | None = "https://vectorlab.dk/") -> None:
    with Session(engine) as s:
        company = s.get(Company, company_id)
        company.website = website
        s.add(company)
        s.commit()


def _describing(text: str):
    asked = []

    def describe(name, country_code, website):
        asked.append((name, website))
        return SupplierProfile(text, website)

    return describe, asked


def test_a_company_with_a_website_is_described_from_it(engine, make_tenant):
    company_id = make_tenant()["company_id"]
    _with_website(engine, company_id)
    describe, asked = _describing("Builds software for smartwatches and wearables.")

    assert research_pending_companies(engine, describe=describe) is True

    with Session(engine) as s:
        company = s.get(Company, company_id)
        assert company.description == "Builds software for smartwatches and wearables."
        assert company.description_source == RESEARCHED
        assert company.researched_at is not None
    assert [website for _, website in asked] == ["https://vectorlab.dk/"]
    assert research_pending_companies(engine, describe=describe) is False


def test_a_site_that_says_nothing_is_not_researched_again(engine, make_tenant):
    company_id = make_tenant()["company_id"]
    _with_website(engine, company_id)
    describe, asked = _describing("")

    research_pending_companies(engine, describe=describe)
    research_pending_companies(engine, describe=describe)

    with Session(engine) as s:
        company = s.get(Company, company_id)
        assert (company.description, company.researched_at is not None) == (None, True)
    assert len(asked) == 1


def test_a_description_written_meanwhile_is_kept(engine, make_tenant):
    company_id = make_tenant()["company_id"]
    _with_website(engine, company_id)

    def describe(name, country_code, website):
        with Session(engine) as s:
            company = s.get(Company, company_id)
            company.description = "We build apps for smartwatches."
            company.description_source = HUMAN
            s.add(company)
            s.commit()
        return SupplierProfile("A software company.", website)

    research_pending_companies(engine, describe=describe)

    with Session(engine) as s:
        assert s.get(Company, company_id).description == "We build apps for smartwatches."


def test_nothing_is_researched_when_it_is_switched_off(engine, make_tenant, monkeypatch):
    monkeypatch.setattr(config, "COMPANY_RESEARCH_ENABLED", False)
    _with_website(engine, make_tenant()["company_id"])
    describe, asked = _describing("A software company.")

    assert research_pending_companies(engine, describe=describe) is False
    assert asked == []
