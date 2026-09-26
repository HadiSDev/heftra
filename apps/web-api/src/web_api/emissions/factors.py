"""The active factor set, and the factor for a sector bought from a given country."""
from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import NamedTuple

from sqlmodel import Session, select

from ..db.models import EmissionCountryRegion, EmissionFactor, EmissionFactorSet

REST_OF_WORLD = "Rest of World"


class FactorMatch(NamedTuple):
    """A factor, and the country code or region name it is the factor for."""

    kg_co2e_per_unit: Decimal
    area: str


def active_factor_set(session: Session) -> EmissionFactorSet | None:
    return session.exec(
        select(EmissionFactorSet).where(EmissionFactorSet.active == True)  # noqa: E712
    ).first()


class FactorLookup:
    """One factor set's factors for a known set of sectors, held in memory."""

    def __init__(self, by_country: dict[tuple[str, str], Decimal],
                 by_region: dict[tuple[str, str], Decimal], regions: dict[str, str]) -> None:
        self._by_country = by_country
        self._by_region = by_region
        self._regions = regions

    @classmethod
    def load(cls, session: Session, factor_set: EmissionFactorSet,
             sector_ids: Iterable[str]) -> FactorLookup:
        wanted = set(sector_ids)
        by_country: dict[tuple[str, str], Decimal] = {}
        by_region: dict[tuple[str, str], Decimal] = {}
        if wanted:
            rows = session.exec(
                select(EmissionFactor.sector_id, EmissionFactor.country_code,
                       EmissionFactor.region, EmissionFactor.kg_co2e_per_unit)
                .where(EmissionFactor.factor_set_id == factor_set.id,
                       EmissionFactor.sector_id.in_(wanted))  # type: ignore[attr-defined]
            ).all()
            for sector_id, country_code, region, factor in rows:
                if country_code is not None:
                    by_country[(sector_id, country_code)] = factor
                else:
                    by_region[(sector_id, region)] = factor
        regions = dict(session.exec(
            select(EmissionCountryRegion.country_code, EmissionCountryRegion.region)
            .where(EmissionCountryRegion.factor_set_id == factor_set.id)
        ).all())
        return cls(by_country, by_region, regions)

    def find(self, sector_id: str, supplier_country: str | None,
             company_country: str | None) -> FactorMatch | None:
        """The supplier's country, its region, the company's country, its region, then the world."""
        for country in (supplier_country, company_country):
            if not country:
                continue
            code = country.upper()
            factor = self._by_country.get((sector_id, code))
            if factor is not None:
                return FactorMatch(factor, code)
            region = self._regions.get(code)
            factor = self._by_region.get((sector_id, region)) if region else None
            if factor is not None:
                return FactorMatch(factor, region)
        factor = self._by_region.get((sector_id, REST_OF_WORLD))
        if factor is not None:
            return FactorMatch(factor, REST_OF_WORLD)
        return None
