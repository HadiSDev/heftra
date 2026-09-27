"""Write an Open CEDA release into the factor tables, at purchaser prices."""
from __future__ import annotations

from decimal import Decimal
from typing import NamedTuple
from uuid import uuid4

from sqlalchemy import delete, insert
from sqlmodel import Session, select

from ..db.models import EmissionCountryRegion, EmissionFactor, EmissionFactorSet, EmissionSector
from ..db.models.audit_log import SYSTEM_ACTOR
from .activation import activate_factor_set
from .ceda.release import ATTRIBUTION, CLASSIFICATION, LICENCE, SOURCE
from .ceda.types import CedaWorkbook, WorkbookError

PURCHASER = "purchaser"
_FACTOR_PLACES = Decimal("0.00000001")


class ImportCounts(NamedTuple):
    factor_set_id: str
    version: str
    sectors: int
    countries: int
    regions: int
    factors: int
    skipped_countries: list[str]
    active: bool


def import_workbook(session: Session, workbook: CedaWorkbook, *, activate: bool,
                    actor: str = SYSTEM_ACTOR) -> ImportCounts:
    """Store `workbook` as its version's factor set, replacing any earlier import of that version.

    The caller commits, so a failure part-way leaves nothing behind.
    """
    ratios = _purchaser_ratios(workbook)
    sector_ids = _upsert_sectors(session, workbook)
    factor_set = _replace_set(session, workbook)

    rows = [
        _factor_row(factor_set.id, sector_ids, code, ratios[code], value, country_code=country)
        for (code, country), value in workbook.country_factors.items()
    ] + [
        _factor_row(factor_set.id, sector_ids, code, ratios[code], value, region=region)
        for (code, region), value in workbook.region_factors.items()
    ]
    if rows:
        session.execute(insert(EmissionFactor), rows)
    regions = [
        {"id": str(uuid4()), "factor_set_id": factor_set.id, "country_code": country, "region": region}
        for country, region in workbook.country_regions.items()
    ]
    if regions:
        session.execute(insert(EmissionCountryRegion), regions)

    if activate:
        activate_factor_set(session, factor_set, actor=actor)
    session.flush()
    return ImportCounts(
        factor_set_id=factor_set.id,
        version=factor_set.version,
        sectors=len(sector_ids),
        countries=len({country for _, country in workbook.country_factors}),
        regions=len({region for _, region in workbook.region_factors}),
        factors=len(rows),
        skipped_countries=workbook.skipped_countries,
        active=factor_set.active,
    )


def _purchaser_ratios(workbook: CedaWorkbook) -> dict[str, Decimal]:
    """Each sector's multiplier from the workbook's price type to purchaser prices."""
    codes = {sector.code for sector in workbook.sectors}
    if workbook.price_type == PURCHASER:
        return {code: Decimal(1) for code in codes}
    missing = sorted(codes - workbook.purchaser_ratios.keys())
    if missing:
        raise WorkbookError(f"no purchaser-to-producer ratio for sectors {missing[:5]}")
    return {code: workbook.purchaser_ratios[code] for code in codes}


def _upsert_sectors(session: Session, workbook: CedaWorkbook) -> dict[str, str]:
    existing = {
        sector.code: sector
        for sector in session.exec(
            select(EmissionSector).where(EmissionSector.classification == CLASSIFICATION)
        ).all()
    }
    for entry in workbook.sectors:
        sector = existing.get(entry.code) or EmissionSector(
            classification=CLASSIFICATION, code=entry.code, name=entry.name
        )
        sector.name = entry.name
        sector.description = entry.description
        session.add(sector)
        existing[entry.code] = sector
    session.flush()
    return {code: sector.id for code, sector in existing.items()}


def _replace_set(session: Session, workbook: CedaWorkbook) -> EmissionFactorSet:
    factor_set = session.exec(
        select(EmissionFactorSet).where(
            EmissionFactorSet.source == SOURCE, EmissionFactorSet.version == workbook.version
        )
    ).first()
    if factor_set is None:
        factor_set = EmissionFactorSet(
            source=SOURCE, version=workbook.version, classification=CLASSIFICATION,
            currency=workbook.currency, price_year=workbook.price_year, price_basis=PURCHASER,
            licence=LICENCE, attribution=ATTRIBUTION,
        )
    else:
        session.exec(delete(EmissionFactor).where(EmissionFactor.factor_set_id == factor_set.id))
        session.exec(
            delete(EmissionCountryRegion).where(
                EmissionCountryRegion.factor_set_id == factor_set.id
            )
        )
        factor_set.currency = workbook.currency
        factor_set.price_year = workbook.price_year
    session.add(factor_set)
    session.flush()
    return factor_set


def _factor_row(factor_set_id: str, sector_ids: dict[str, str], code: str, ratio: Decimal,
                value: Decimal, *, country_code: str | None = None,
                region: str | None = None) -> dict:
    if code not in sector_ids:
        raise WorkbookError(f"factor for sector {code!r}, which the metadata does not list")
    return {
        "id": str(uuid4()),
        "factor_set_id": factor_set_id,
        "sector_id": sector_ids[code],
        "country_code": country_code,
        "region": region,
        "kg_co2e_per_unit": (value * ratio).quantize(_FACTOR_PLACES),
    }
