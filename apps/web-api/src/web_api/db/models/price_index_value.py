from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, Numeric, String, UniqueConstraint
from sqlmodel import Field, SQLModel

from ._base import _ts, _uuid


class PriceIndexValue(SQLModel, table=True):
    """One month's value of a price index series, such as US CPI."""

    __tablename__ = "price_index_values"
    __table_args__ = (UniqueConstraint("series", "month", name="uq_price_index_value_month"),)

    id: str = Field(default_factory=_uuid, primary_key=True)
    series: str = Field(sa_type=String, nullable=False)
    month: date = Field(sa_type=Date, nullable=False)
    value: Decimal = Field(sa_type=Numeric(14, 4), nullable=False)
    source: str = Field(sa_type=String, nullable=False)
    imported_at: datetime = Field(sa_column=_ts())
