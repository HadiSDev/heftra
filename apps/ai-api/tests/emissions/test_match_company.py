"""A company's lines are matched from the cache, by the agent, or by its fallback; people win."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlmodel import Session, select

from ai_api.emissions.answer import MatchFailed, SectorAnswer
from ai_api.emissions.lines import match_company
from ai_api.emissions.matchers import Matchers
from web_api.db.models import (
    Company,
    EmissionFactorSet,
    EmissionSector,
    EmissionSectorSource,
    Invoice,
    InvoiceLine,
    Organization,
)


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


class World:
    """One company with an invoice, an active factor set and two sectors."""

    def __init__(self, session: Session, *, classification: str = "ceda-bea") -> None:
        self.session = session
        organization = Organization(name="Org", clerk_org_id="clerk_match")
        session.add(organization)
        session.commit()
        self.company = Company(organization_id=organization.id, name="Acme", base_currency="DKK")
        session.add(self.company)
        session.add(EmissionFactorSet(
            source="open_ceda", version="CEDA 2025", classification=classification,
            currency="USD", price_year=2023, price_basis="purchaser", licence="CC BY-SA 4.0",
            attribution="CEDA by Watershed", active=True,
        ))
        session.commit()
        self.invoice = Invoice(company_id=self.company.id, currency="DKK", status="uncategorized")
        session.add(self.invoice)
        self.hosting = self.sector("518200", "Hosting", classification)
        self.software = self.sector("511200", "Software", classification)
        session.commit()

    def sector(self, code: str, name: str, classification: str) -> EmissionSector:
        sector = EmissionSector(classification=classification, code=code, name=name)
        self.session.add(sector)
        self.session.commit()
        return sector

    def line(self, name: str, **fields) -> InvoiceLine:
        line = InvoiceLine(company_id=self.company.id, invoice_id=self.invoice.id,
                           item_name=name, status="uncategorized", amount=Decimal("10"),
                           sequence=len(self.lines()), **fields)
        self.session.add(line)
        self.session.commit()
        return line

    def lines(self) -> list[InvoiceLine]:
        return list(self.session.exec(select(InvoiceLine)).all())


def _always(sector_id: str | None, confidence: float = 0.8):
    calls: list[str] = []

    def match(context):
        calls.append(context.line_id)
        return SectorAnswer(sector_id, confidence, "Because.")

    match.calls = calls
    return match


def _failing(context):
    raise MatchFailed("gave up")


def _run(session, world, agent, fallback=None, **options):
    matchers = Matchers(agent, fallback or _failing)
    return match_company(session, world.company.id, matchers_for=lambda *_: matchers, **options)


def test_the_agent_matches_a_line(session):
    world = World(session)
    line = world.line("Dedicated server")

    counts = _run(session, world, _always(world.hosting.id, 0.4))

    session.refresh(line)
    assert counts["agent"] == 1
    assert line.emission_sector_id == world.hosting.id
    assert line.emission_sector_source == EmissionSectorSource.AI
    assert line.emission_sector_confidence == Decimal("0.400")
    assert line.emission_sector_rationale == "Because."


def test_a_failing_agent_falls_back(session):
    world = World(session)
    line = world.line("Dedicated server")

    counts = _run(session, world, _failing, _always(world.software.id))

    session.refresh(line)
    assert (counts["agent"], counts["fallback"]) == (0, 1)
    assert line.emission_sector_id == world.software.id


def test_both_failing_leaves_the_line_unmatched(session):
    world = World(session)
    line = world.line("Dedicated server")

    counts = _run(session, world, _failing, _failing)

    session.refresh(line)
    assert counts["failed"] == 1
    assert line.emission_sector_id is None


def test_nothing_fits_is_counted_unmatched(session):
    world = World(session)
    world.line("Rounding")

    assert _run(session, world, _always(None))["unmatched"] == 1


def test_the_same_question_is_answered_once(session):
    world = World(session)
    for _ in range(3):
        world.line("Monthly licence")
    agent = _always(world.software.id)

    counts = _run(session, world, agent)

    assert (counts["agent"], counts["cached"]) == (1, 2)
    assert len(agent.calls) == 1
    assert {line.emission_sector_id for line in world.lines()} == {world.software.id}


def test_a_humans_sector_is_never_touched(session):
    world = World(session)
    line = world.line("Dedicated server", emission_sector_id=world.hosting.id,
                      emission_sector_source=EmissionSectorSource.HUMAN)
    agent = _always(world.software.id)

    _run(session, world, agent)
    _run(session, world, agent, rematch=True)

    session.refresh(line)
    assert line.emission_sector_id == world.hosting.id
    assert agent.calls == []


def test_ai_sectors_of_another_classification_are_matched_again(session):
    world = World(session)
    old = world.sector("X1", "Old hosting", "old-scheme")
    line = world.line("Dedicated server", emission_sector_id=old.id,
                      emission_sector_source=EmissionSectorSource.AI)

    _run(session, world, _always(world.hosting.id))

    session.refresh(line)
    assert line.emission_sector_id == world.hosting.id


def test_a_current_ai_sector_is_left_until_a_rematch(session):
    world = World(session)
    line = world.line("Dedicated server")
    _run(session, world, _always(world.hosting.id))

    _run(session, world, _always(world.software.id))
    session.refresh(line)
    assert line.emission_sector_id == world.hosting.id

    counts = _run(session, world, _always(world.software.id), rematch=True)
    session.refresh(line)
    assert line.emission_sector_id == world.software.id
    assert counts["cached"] == 0


def test_the_limit_caps_the_lines_considered(session):
    world = World(session)
    for name in ("a", "b", "c"):
        world.line(name)

    counts = _run(session, world, _always(world.hosting.id), limit=2)

    assert counts["agent"] == 2


def test_without_an_active_set_nothing_is_matched(session):
    world = World(session)
    world.line("Dedicated server")
    for factor_set in session.exec(select(EmissionFactorSet)).all():
        factor_set.active = False
        session.add(factor_set)
    session.commit()

    assert _run(session, world, _always(world.hosting.id)) == {"skipped": "no active factor set"}
