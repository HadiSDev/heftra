from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, String, Text
from sqlmodel import Field, SQLModel

from ._base import _ts, _uuid


class DemoRequest(SQLModel, table=True):
    """A landing-site visitor asking for a demo, kept for 24 months."""

    __tablename__ = "demo_requests"

    id: str = Field(default_factory=_uuid, primary_key=True)
    name: str = Field(sa_type=String, nullable=False)
    email: str = Field(sa_type=String, nullable=False)
    company: str = Field(sa_type=String, nullable=False)
    company_size: str = Field(sa_type=String, nullable=False)
    message: Optional[str] = Field(sa_type=Text, nullable=True)
    consented_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    source_ip: Optional[str] = Field(sa_type=String, nullable=True)
    user_agent: Optional[str] = Field(sa_type=String, nullable=True)
    created_at: datetime = Field(sa_column=_ts())
