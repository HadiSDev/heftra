from typing import Optional

from sqlalchemy import String, UniqueConstraint
from sqlmodel import Field, SQLModel

from ._base import _uuid


class EmissionSector(SQLModel, table=True):
    """A sector of an emission classification, shared by every release of it."""

    __tablename__ = "emission_sectors"
    __table_args__ = (
        UniqueConstraint("classification", "code", name="uq_emission_sector_code"),
    )

    id: str = Field(default_factory=_uuid, primary_key=True)
    classification: str = Field(sa_type=String, nullable=False, index=True)
    code: str = Field(sa_type=String, nullable=False)
    name: str = Field(sa_type=String, nullable=False)
    description: Optional[str] = Field(sa_type=String, nullable=True)
