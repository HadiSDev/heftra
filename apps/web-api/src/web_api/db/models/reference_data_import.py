"""An upload or refresh of global reference data, run in the background."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Index, String
from sqlmodel import Field, SQLModel

from ._base import _ts, _uuid


class ReferenceImportKind(str, Enum):
    FACTOR_WORKBOOK = "factor_workbook"
    PRICE_INDEX = "price_index"


class ReferenceImportStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ReferenceDataImport(SQLModel, table=True):
    """The request to import a factor workbook or refresh a price index, and its outcome."""

    __tablename__ = "reference_data_imports"
    __table_args__ = (
        Index("ix_reference_data_imports_requested", "requested_at"),
        Index("ix_reference_data_imports_kind_status", "kind", "status"),
    )

    id: str = Field(default_factory=_uuid, primary_key=True)
    kind: str = Field(sa_type=String, nullable=False)
    status: str = Field(sa_type=String, nullable=False, default=ReferenceImportStatus.QUEUED.value)
    subject: str = Field(sa_type=String, nullable=False)
    activate: bool = Field(sa_type=Boolean, nullable=False, default=False)
    requested_by: str = Field(sa_type=String, nullable=False)
    requested_at: datetime = Field(sa_column=_ts())
    started_at: Optional[datetime] = Field(sa_type=DateTime(timezone=True), nullable=True)
    finished_at: Optional[datetime] = Field(sa_type=DateTime(timezone=True), nullable=True)
    result: Optional[dict] = Field(sa_type=JSON, nullable=True)
    error: Optional[str] = Field(sa_type=String, nullable=True)
