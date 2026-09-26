from sqlalchemy import String, UniqueConstraint
from sqlmodel import Field, SQLModel

from ._base import _uuid


class EmissionCountryRegion(SQLModel, table=True):
    """The region a factor set averages a country into."""

    __tablename__ = "emission_country_regions"
    __table_args__ = (
        UniqueConstraint("factor_set_id", "country_code", name="uq_emission_country_region"),
    )

    id: str = Field(default_factory=_uuid, primary_key=True)
    factor_set_id: str = Field(
        sa_type=String, foreign_key="emission_factor_sets.id", nullable=False, index=True
    )
    country_code: str = Field(sa_type=String(2), nullable=False)
    region: str = Field(sa_type=String, nullable=False)
