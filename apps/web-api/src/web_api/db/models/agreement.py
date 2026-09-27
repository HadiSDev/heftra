from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Integer, String
from sqlmodel import Field, SQLModel

from ._base import _ts, _uuid
from .agreement_enums import AgreementStatus


class Agreement(SQLModel, table=True):
    """A trade or framework agreement a company uploaded, as read and reviewed."""

    __tablename__ = "agreements"

    id: str = Field(default_factory=_uuid, primary_key=True)
    company_id: str = Field(sa_type=String, foreign_key="companies.id", nullable=False, index=True)
    file_id: str = Field(sa_type=String, foreign_key="files.id", nullable=False)
    title: str = Field(sa_type=String, nullable=False)
    reference: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    vendor_id: Optional[str] = Field(sa_type=String, foreign_key="vendors.id", nullable=True,
                                     default=None)
    supplier_name: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    supplier_vat_number: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    supplier_website: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    starts_on: Optional[date] = Field(sa_type=Date, nullable=True, default=None)
    ends_on: Optional[date] = Field(sa_type=Date, nullable=True, default=None)
    currency: Optional[str] = Field(sa_type=String(3), nullable=True, default=None)
    summary: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    status: str = Field(sa_type=String, nullable=False, default=AgreementStatus.PENDING.value,
                        index=True)
    read_attempts: int = Field(sa_type=Integer, nullable=False, default=0)
    read_error: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    read_started_at: Optional[datetime] = Field(sa_type=DateTime(timezone=True), nullable=True,
                                                default=None)
    read_at: Optional[datetime] = Field(sa_type=DateTime(timezone=True), nullable=True,
                                        default=None)
    analysed_at: Optional[datetime] = Field(sa_type=DateTime(timezone=True), nullable=True,
                                            default=None)
    uploaded_by: str = Field(sa_type=String, nullable=False)
    created_at: datetime = Field(sa_column=_ts())
