"""A factor is found for the supplier's country, else its region, the company's, or the world."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlmodel import Session

from web_api.db.models import (
    EmissionCountryRegion,
    EmissionFactor,
    EmissionFactorSet,
    EmissionSector,
)
from web_api.emissions.factors import FactorLookup, FactorMatch, active_factor_set


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def _set(session, *, version="CEDA 2025", active=True) -> EmissionFactorSet:
    factor_set = EmissionFactorSet(source="open_ceda", version=version, classification="ceda-bea",
                                   currency="USD", price_year=2023, price_basis="purchaser",
                                   licence="CC BY-SA 4.0", attribution="CEDA by Watershed",
                                   active=active)
    session.add(factor_set)
    session.commit()
    return factor_set


def _lookup(session, factors: dict, regions: dict | None = None) -> tuple[FactorLookup, str]:
    factor_set = _set(session)
    sector = EmissionSector(classification="ceda-bea", code="518200", name="Hosting")
    session.add(sector)
    session.commit()
    for area, value in factors.items():
        is_country = len(area) == 2
        session.add(EmissionFactor(
            factor_set_id=factor_set.id, sector_id=sector.id,
            country_code=area if is_country else None, region=None if is_country else area,
            kg_co2e_per_unit=Decimal(value),
        ))
    for country, region in (regions or {}).items():
        session.add(EmissionCountryRegion(factor_set_id=factor_set.id, country_code=country,
                                          region=region))
    session.commit()
    return FactorLookup.load(session, factor_set, [sector.id]), sector.id


def test_the_suppliers_country_comes_first(session):
    lookup, sector = _lookup(session, {"DE": "0.2", "DK": "0.1"})

    assert lookup.find(sector, "DE", "DK") == FactorMatch(Decimal("0.2"), "DE")


def test_a_country_without_factors_uses_its_region(session):
    lookup, sector = _lookup(session, {"DK": "0.1", "Eastern Asia": "0.5"}, {"TW": "Eastern Asia"})

    assert lookup.find(sector, "tw", "DK") == FactorMatch(Decimal("0.5"), "Eastern Asia")


def test_no_supplier_country_falls_back_to_the_companys(session):
    lookup, sector = _lookup(session, {"DK": "0.1"})

    assert lookup.find(sector, None, "DK") == FactorMatch(Decimal("0.1"), "DK")


def test_the_rest_of_the_world_is_the_last_resort(session):
    lookup, sector = _lookup(session, {"Rest of World": "0.3"})

    assert lookup.find(sector, "BR", "DK") == FactorMatch(Decimal("0.3"), "Rest of World")


def test_no_factor_anywhere_is_none(session):
    lookup, sector = _lookup(session, {"DE": "0.2"})

    assert lookup.find(sector, "BR", "DK") is None


def test_only_the_active_set_is_used(session):
    _set(session, version="CEDA 2024", active=False)
    active = _set(session, version="CEDA 2025", active=True)

    assert active_factor_set(session).id == active.id


def test_no_active_set_is_none(session):
    _set(session, active=False)

    assert active_factor_set(session) is None
