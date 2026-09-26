"""An active factor set with a few sectors, and exchange rates to price spend in its currency."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlmodel import Session

from web_api.db.models import (
    EmissionCountryRegion,
    EmissionFactor,
    EmissionFactorSet,
    EmissionSector,
    FxRate,
)


class Factors:
    """A factor set written straight into the session, with sectors added by code."""

    def __init__(self, session: Session, *, active: bool = True, classification: str = "ceda-bea",
                 version: str = "CEDA 2025") -> None:
        self.session = session
        self.factor_set = EmissionFactorSet(
            source="open_ceda", version=version, classification=classification, currency="USD",
            price_year=2023, price_basis="purchaser", licence="CC BY-SA 4.0",
            attribution="CEDA by Watershed", active=active,
        )
        session.add(self.factor_set)
        session.commit()

    def sector(self, code: str, name: str, factors: dict[str, str]) -> EmissionSector:
        """A sector with a factor per country code (two letters) or region name."""
        sector = EmissionSector(classification=self.factor_set.classification, code=code,
                                name=name, description=f"{name}.")
        self.session.add(sector)
        self.session.commit()
        for area, value in factors.items():
            is_country = len(area) == 2
            self.session.add(EmissionFactor(
                factor_set_id=self.factor_set.id, sector_id=sector.id,
                country_code=area if is_country else None,
                region=None if is_country else area,
                kg_co2e_per_unit=Decimal(value),
            ))
        self.session.commit()
        return sector

    def region(self, country_code: str, region: str) -> None:
        self.session.add(EmissionCountryRegion(factor_set_id=self.factor_set.id,
                                               country_code=country_code, region=region))
        self.session.commit()


def euro_rates(session: Session, on: date, **per_euro: str) -> None:
    """Store the rates of one day as units of each currency per euro."""
    for currency, rate in per_euro.items():
        session.add(FxRate(quote_currency=currency, rate_date=on, published_date=on,
                           rate=Decimal(rate), source="test"))
    session.commit()
