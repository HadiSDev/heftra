"""What a matcher concluded about a line."""
from __future__ import annotations

from typing import NamedTuple


class MatchFailed(Exception):
    """The matcher could not be reached, ran out of steps, or gave no usable answer."""


class SectorAnswer(NamedTuple):
    """The chosen sector, or none when nothing fits, with how sure and why."""

    sector_id: str | None
    confidence: float
    rationale: str


def bounded(confidence: float) -> float:
    """A confidence held to 0–1, however the model wrote it."""
    return min(max(confidence, 0.0), 1.0)
