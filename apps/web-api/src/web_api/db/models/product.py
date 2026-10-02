from datetime import datetime
from typing import Optional

from sqlalchemy import String
from sqlmodel import Field, SQLModel

from ._base import _ts, _uuid


class Product(SQLModel, table=True):
    """A product as its maker identifies it, shared by every item that is it, from any supplier,
    company or organization. Identifiers are stored normalised."""

    __tablename__ = "products"

    id: str = Field(default_factory=_uuid, primary_key=True)
    gtin: Optional[str] = Field(sa_type=String, nullable=True, default=None, unique=True)
    brand: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    part_number: Optional[str] = Field(sa_type=String, nullable=True, default=None, index=True)
    model: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    name: str = Field(sa_type=String, nullable=False)
    item_class: str = Field(sa_type=String, nullable=False)
    pricing_unit: str = Field(sa_type=String, nullable=False)
    created_at: datetime = Field(sa_column=_ts())
