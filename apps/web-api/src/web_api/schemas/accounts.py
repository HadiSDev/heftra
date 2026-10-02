"""Users and the organization profile."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: str
    role: str
    is_system_admin: bool
    organization_id: str


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str | None = None
    status: str
    price_benchmark_enabled: bool = True
    created_at: datetime


class OrganizationUpdate(BaseModel):
    """Request body to update the organization profile."""

    name: str | None = Field(default=None, min_length=1)
    slug: str | None = Field(default=None, min_length=1)
    price_benchmark_enabled: bool | None = None

    @field_validator("price_benchmark_enabled")
    @classmethod
    def _not_null(cls, value: bool | None) -> bool:
        if value is None:
            raise ValueError("Say whether the organization takes part in the price benchmark.")
        return value
