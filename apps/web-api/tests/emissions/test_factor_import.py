"""An Open CEDA workbook becomes an active factor set at purchaser prices."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlmodel import Session, select

from ceda_workbook import write_workbook
from web_api.db.models import (
    EmissionCountryRegion,
    EmissionFactor,
    EmissionFactorSet,
    EmissionSector,
)
from web_api.emissions.ceda.types import WorkbookError
from web_api.emissions.ceda.workbook import read_workbook
from web_api.emissions.factor_import import import_workbook


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def _import(session, path, *, activate=True):
    counts = import_workbook(session, read_workbook(path), activate=activate)
    session.commit()
    return counts


def _factor(session, code, *, country=None, region=None) -> Decimal:
    sector = session.exec(select(EmissionSector).where(EmissionSector.code == code)).one()
    return session.exec(
        select(EmissionFactor.kg_co2e_per_unit).where(
            EmissionFactor.sector_id == sector.id,
            EmissionFactor.country_code == country,
            EmissionFactor.region == region,
        )
    ).one()


def test_a_release_is_imported_and_activated(session, tmp_path):
    counts = _import(session, write_workbook(tmp_path / "ceda.xlsx"))

    factor_set = session.get(EmissionFactorSet, counts.factor_set_id)
    assert (factor_set.source, factor_set.version, factor_set.classification) == (
        "open_ceda", "CEDA 2025", "ceda-bea")
    assert (factor_set.currency, factor_set.price_year, factor_set.price_basis) == (
        "USD", 2023, "purchaser")
    assert factor_set.attribution == "CEDA by Watershed"
    assert factor_set.active is True
    assert (counts.sectors, counts.countries, counts.regions, counts.factors) == (2, 2, 3, 10)


def test_factors_are_converted_to_purchaser_prices(session, tmp_path):
    _import(session, write_workbook(tmp_path / "ceda.xlsx"))

    assert _factor(session, "518200", country="DK") == Decimal("0.08")
    assert _factor(session, "541511", country="DE") == Decimal("0.03")


def test_a_code_stored_as_a_number_is_read_as_its_digits(session, tmp_path):
    _import(session, write_workbook(tmp_path / "ceda.xlsx"))

    sector = session.exec(select(EmissionSector).where(EmissionSector.code == "541511")).one()
    assert sector.name == "Custom computer programming services"
    assert sector.description == "Writing software to order."


def test_rest_of_world_and_regions_are_stored_under_their_region_names(session, tmp_path):
    _import(session, write_workbook(tmp_path / "ceda.xlsx"))

    assert _factor(session, "518200", region="Rest of World") == Decimal("0.24")
    assert _factor(session, "518200", region="Caribbean") == Decimal("0.32")
    regions = dict(session.exec(
        select(EmissionCountryRegion.country_code, EmissionCountryRegion.region)).all())
    assert regions == {"DK": "Northern Europe", "TW": "Eastern Asia", "CU": "Caribbean"}


def test_an_unknown_country_code_is_skipped_and_reported(session, tmp_path):
    countries = [("DNK", "Denmark", ["0.1", "0.05"]), ("QQQ", "Nowhere", ["0.1", "0.1"])]

    counts = _import(session, write_workbook(tmp_path / "ceda.xlsx", countries=countries))

    assert counts.skipped_countries == ["QQQ"]
    assert counts.countries == 1


def test_a_missing_sheet_is_named(tmp_path):
    path = write_workbook(tmp_path / "ceda.xlsx", leave_out="Purchaser - producer conversion")

    with pytest.raises(WorkbookError, match="Purchaser - producer conversion"):
        read_workbook(path)


def test_a_country_listed_twice_fails_the_import(tmp_path):
    countries = [("DNK", "Denmark", ["0.1", "0.05"]), ("DNK", "Denmark", ["0.2", "0.06"])]

    with pytest.raises(WorkbookError, match="DNK twice"):
        read_workbook(write_workbook(tmp_path / "ceda.xlsx", countries=countries))


def test_re_importing_a_version_replaces_its_factors(session, tmp_path):
    path = write_workbook(tmp_path / "ceda.xlsx")
    first = _import(session, path)
    second = _import(session, path)

    assert first.factor_set_id == second.factor_set_id
    assert len(session.exec(select(EmissionFactorSet)).all()) == 1
    assert len(session.exec(select(EmissionFactor)).all()) == 10
    assert len(session.exec(select(EmissionSector)).all()) == 2


def test_activating_a_release_deactivates_the_others(session, tmp_path):
    older = EmissionFactorSet(source="open_ceda", version="CEDA 2024", classification="ceda-bea",
                              currency="USD", price_year=2022, price_basis="purchaser",
                              licence="CC BY-SA 4.0", attribution="CEDA by Watershed", active=True)
    session.add(older)
    session.commit()

    _import(session, write_workbook(tmp_path / "ceda.xlsx"))

    session.refresh(older)
    assert older.active is False


def test_an_import_without_activate_leaves_the_active_set_alone(session, tmp_path):
    counts = _import(session, write_workbook(tmp_path / "ceda.xlsx"), activate=False)

    assert session.get(EmissionFactorSet, counts.factor_set_id).active is False
