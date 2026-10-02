from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import JSON, Boolean, Numeric, String
from sqlmodel import Field, SQLModel

from ._base import _ts, _uuid


class MarketplaceOffer(SQLModel, table=True):
    """A product offered for sale, as a marketplace connector found it.

    `price` is for one pack of `pack_quantity` `pack_unit`, in `currency`, with VAT when
    `vat_included`; `price_breaks` holds `[{"quantity", "price"}]` when the seller gives them.
    `spec` is the offer read as an item specification.
    """

    __tablename__ = "marketplace_offers"

    id: str = Field(default_factory=_uuid, primary_key=True)
    query_id: str = Field(sa_type=String, foreign_key="marketplace_queries.id", nullable=False,
                          index=True)
    connector: str = Field(sa_type=String, nullable=False)
    seller: str = Field(sa_type=String, nullable=False)
    url: str = Field(sa_type=String, nullable=False)
    title: str = Field(sa_type=String, nullable=False)
    identifiers: dict = Field(sa_type=JSON, nullable=False, default_factory=dict)
    spec: Optional[dict] = Field(sa_type=JSON, nullable=True, default=None)
    price: Decimal = Field(sa_type=Numeric(16, 4), nullable=False)
    price_breaks: list = Field(sa_type=JSON, nullable=False, default_factory=list)
    currency: str = Field(sa_type=String(3), nullable=False)
    vat_included: bool = Field(sa_type=Boolean, nullable=False)
    seller_country: Optional[str] = Field(sa_type=String(2), nullable=True, default=None)
    pack_quantity: Decimal = Field(sa_type=Numeric(14, 4), nullable=False, default=Decimal("1"))
    pack_unit: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    availability: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    shipping: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    seen_at: datetime = Field(sa_column=_ts())
