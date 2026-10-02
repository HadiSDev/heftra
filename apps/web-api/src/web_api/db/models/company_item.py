from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import JSON, Date, DateTime, Integer, Numeric, String, UniqueConstraint
from sqlmodel import Field, SQLModel

from ._base import _uuid


class CompanyItem(SQLModel, table=True):
    """One distinct thing a company buys, with its specification and price per pricing unit.

    Spend, quantity and prices cover the last 12 months, in the company's base currency.
    `line_quantity` is what the lines bought in their own unit and `priced_spend` what the lines
    stating a quantity cost; with the specification's units per line unit they give `quantity`
    in the pricing unit and `unit_price`. `order_quantity` is the average quantity per line, and
    `unit_price_eur` lets organizations with other base currencies be compared.
    """

    __tablename__ = "company_items"
    __table_args__ = (
        UniqueConstraint("company_id", "item_key", name="uq_company_item"),
    )

    id: str = Field(default_factory=_uuid, primary_key=True)
    company_id: str = Field(sa_type=String, foreign_key="companies.id", nullable=False, index=True)
    item_key: str = Field(sa_type=String, nullable=False)
    item_name: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    description: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    unit: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    vendor_id: Optional[str] = Field(sa_type=String, foreign_key="vendors.id", nullable=True,
                                     default=None)
    category_id: Optional[str] = Field(sa_type=String, foreign_key="spend_categories.id",
                                       nullable=True, default=None)
    base_currency: Optional[str] = Field(sa_type=String(3), nullable=True, default=None)
    spend: Decimal = Field(sa_type=Numeric(16, 2), nullable=False, default=Decimal("0"))
    lines: int = Field(sa_type=Integer, nullable=False, default=0)
    last_bought_on: Optional[date] = Field(sa_type=Date, nullable=True, default=None)
    line_quantity: Optional[Decimal] = Field(sa_type=Numeric(18, 4), nullable=True, default=None)
    priced_spend: Optional[Decimal] = Field(sa_type=Numeric(16, 2), nullable=True, default=None)
    order_quantity: Optional[Decimal] = Field(sa_type=Numeric(14, 4), nullable=True, default=None)
    spec: Optional[dict] = Field(sa_type=JSON, nullable=True, default=None)
    item_class: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    spec_source: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    spec_text_hash: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    spec_failures: int = Field(sa_type=Integer, nullable=False, default=0)
    spec_signature: Optional[str] = Field(sa_type=String, nullable=True, default=None, index=True)
    product_id: Optional[str] = Field(sa_type=String, foreign_key="products.id", nullable=True,
                                      default=None, index=True)
    quantity: Optional[Decimal] = Field(sa_type=Numeric(18, 4), nullable=True, default=None)
    unit_price: Optional[Decimal] = Field(sa_type=Numeric(18, 6), nullable=True, default=None)
    unit_price_eur: Optional[Decimal] = Field(sa_type=Numeric(18, 6), nullable=True, default=None)
    price_note: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    searched_at: Optional[datetime] = Field(sa_type=DateTime(timezone=True), nullable=True,
                                            default=None)
    refreshed_at: Optional[datetime] = Field(sa_type=DateTime(timezone=True), nullable=True,
                                             default=None)
