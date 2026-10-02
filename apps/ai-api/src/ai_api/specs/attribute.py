"""One key attribute of a specification: a number, a ranked part, or anything else."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, field_validator


class AttributeKind(str, Enum):
    NUMERIC = "numeric"
    TIERED = "tiered"
    OTHER = "other"


class Direction(str, Enum):
    """Which way a number is better for the buyer."""

    MORE = "more"
    LESS = "less"
    EQUAL = "equal"


class Attribute(BaseModel):
    """`value` is the attribute as stated. A numeric one also has `number`, `unit` and
    `direction`; a tiered one `family`, `tier` and `generation` (Intel Core, i7, 13)."""

    name: str
    kind: AttributeKind = AttributeKind.OTHER
    value: str = ""
    number: float | None = None
    unit: str | None = None
    direction: Direction = Direction.MORE
    family: str | None = None
    tier: str | None = None
    generation: str | None = None

    @field_validator("name")
    @classmethod
    def _snake(cls, name: str) -> str:
        return "_".join(name.strip().lower().replace("-", " ").split())

    @field_validator("kind", mode="before")
    @classmethod
    def _kind(cls, kind: object) -> object:
        return AttributeKind.OTHER if kind in (None, "") else kind

    @field_validator("direction", mode="before")
    @classmethod
    def _direction(cls, direction: object) -> object:
        return Direction.MORE if direction in (None, "") else direction

    @field_validator("value", mode="before")
    @classmethod
    def _value(cls, value: object) -> str:
        return "" if value is None else str(value)

    @field_validator("generation", "tier", mode="before")
    @classmethod
    def _text(cls, value: object) -> str | None:
        return None if value in (None, "") else str(value)
