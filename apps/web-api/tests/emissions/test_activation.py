"""Activating a factor set: one active at a time, audited, and flagged when lines need matching."""
from __future__ import annotations

import pytest
from sqlmodel import Session, select

from emission_factors import Factors
from web_api.db.models import AuditLog, EmissionFactorSet
from web_api.emissions.activation import activate_factor_set


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def _active_versions(session) -> list[str]:
    return [factor_set.version for factor_set in session.exec(
        select(EmissionFactorSet).where(EmissionFactorSet.active == True)  # noqa: E712
    )]


def test_activating_replaces_the_active_set_and_is_audited(session):
    current = Factors(session, version="CEDA 2025").factor_set
    older = Factors(session, version="CEDA 2024", active=False).factor_set

    activation = activate_factor_set(session, older, actor="user-1")
    session.commit()

    assert _active_versions(session) == ["CEDA 2024"]
    assert activation.previous.id == current.id
    assert activation.rematch_needed is False
    (entry,) = session.exec(select(AuditLog).where(AuditLog.entity_id == older.id)).all()
    assert (entry.action, entry.actor) == ("activate", "user-1")
    assert {"field": "active_set", "old": "CEDA 2025", "new": "CEDA 2024"} in entry.changes


def test_activating_the_active_set_changes_nothing(session):
    current = Factors(session).factor_set

    activation = activate_factor_set(session, current)
    session.commit()

    assert activation.previous is None
    assert _active_versions(session) == ["CEDA 2025"]
    assert session.exec(select(AuditLog)).all() == []


def test_another_classification_needs_matching_again(session):
    Factors(session, version="CEDA 2025")
    other = Factors(session, version="EXIO 3.8", classification="exiobase",
                    active=False).factor_set

    assert activate_factor_set(session, other).rematch_needed is True
