"""The emissions CLI matches one company and reports how."""
from __future__ import annotations

from sqlmodel import Session

from ai_api.emissions import runner
from web_api.db.models import Company, Organization


def _company(engine) -> str:
    with Session(engine) as s:
        organization = Organization(name="Org", clerk_org_id="clerk_cli")
        s.add(organization)
        s.commit()
        company = Company(organization_id=organization.id, name="Acme", base_currency="DKK")
        s.add(company)
        s.commit()
        return company.id


def test_the_counts_are_printed(engine, monkeypatch, capsys):
    company_id = _company(engine)
    monkeypatch.setattr(runner, "engine", engine)
    monkeypatch.setattr(runner, "match_company", lambda session, company_id, **_: {
        "agent": 3, "fallback": 1, "unmatched": 0, "cached": 2, "failed": 0})

    assert runner.main(["--company-id", company_id]) == 0

    out = capsys.readouterr().out
    assert "matched by the agent: 3" in out
    assert "answered from the cache: 2" in out


def test_without_factors_it_says_so_and_succeeds(engine, monkeypatch, capsys):
    company_id = _company(engine)
    monkeypatch.setattr(runner, "engine", engine)

    assert runner.main(["--company-id", company_id]) == 0
    assert "Import emission factors first" in capsys.readouterr().out


def test_an_unknown_company_fails(engine, monkeypatch):
    monkeypatch.setattr(runner, "engine", engine)

    assert runner.main(["--company-id", "nope"]) == 1
