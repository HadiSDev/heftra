"""How many of a company's lines have an emission sector."""
from __future__ import annotations

from pydantic import BaseModel


class SectorCoverageRow(BaseModel):
    """`ai` includes `needs_review`; `unmatched` has no sector in the active classification."""

    company_id: str
    company_name: str
    organization_name: str
    lines: int
    ai: int
    human: int
    needs_review: int
    unmatched: int
