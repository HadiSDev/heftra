"""Import jobs for reference data, and the request to refresh a price index."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from web_api.db.models import ReferenceImportKind, ReferenceImportStatus


class PriceIndexRefresh(BaseModel):
    series: str


class ReferenceImportRead(BaseModel):
    """A workbook upload or index refresh, and its counts or error once it has run."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    kind: ReferenceImportKind
    status: ReferenceImportStatus
    subject: str
    activate: bool
    requested_by: str
    requested_by_name: str | None = None
    requested_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: dict | None = None
    error: str | None = None
