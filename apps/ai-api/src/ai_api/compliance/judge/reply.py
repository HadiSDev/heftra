"""The judge's answer."""
from __future__ import annotations

from pydantic import BaseModel, field_validator


class JudgeReply(BaseModel):
    in_scope: bool = False
    same_item: bool | None = None
    units_comparable: bool | None = None
    confidence: float | None = None
    reason: str = ""

    @field_validator("confidence", mode="before")
    @classmethod
    def _confidence(cls, value: object) -> float | None:
        try:
            return min(max(float(value), 0.0), 1.0)
        except (TypeError, ValueError):
            return None
