from decimal import Decimal
from typing import Optional

from sqlalchemy import CheckConstraint, Index, Numeric, String, text
from sqlmodel import Field, SQLModel

from ._base import _uuid


class EmissionFactor(SQLModel, table=True):
    """kg CO2e per unit of money spent on a sector in one country or region."""

    __tablename__ = "emission_factors"
    __table_args__ = (
        CheckConstraint(
            "(country_code IS NULL) <> (region IS NULL)",
            name="ck_emission_factor_one_area",
        ),
        Index(
            "uq_emission_factor_country",
            "factor_set_id", "sector_id", "country_code",
            unique=True,
            postgresql_where=text("country_code IS NOT NULL"),
            sqlite_where=text("country_code IS NOT NULL"),
        ),
        Index(
            "uq_emission_factor_region",
            "factor_set_id", "sector_id", "region",
            unique=True,
            postgresql_where=text("region IS NOT NULL"),
            sqlite_where=text("region IS NOT NULL"),
        ),
    )

    id: str = Field(default_factory=_uuid, primary_key=True)
    factor_set_id: str = Field(
        sa_type=String, foreign_key="emission_factor_sets.id", nullable=False, index=True
    )
    sector_id: str = Field(sa_type=String, foreign_key="emission_sectors.id", nullable=False)
    country_code: Optional[str] = Field(sa_type=String(2), nullable=True)
    region: Optional[str] = Field(sa_type=String, nullable=True)
    kg_co2e_per_unit: Decimal = Field(sa_type=Numeric(18, 8), nullable=False)
