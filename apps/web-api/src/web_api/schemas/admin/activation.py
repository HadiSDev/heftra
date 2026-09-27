"""The outcome of activating a factor set."""
from __future__ import annotations

from pydantic import BaseModel

from .status import AdminFactorSetRead


class FactorSetActivationRead(BaseModel):
    factor_set: AdminFactorSetRead
    previous_version: str | None = None
    rematch_needed: bool = False
