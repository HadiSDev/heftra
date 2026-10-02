"""How one attribute of a candidate compares with the item's, and the outcome of a match."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from web_api.db.models import AlternativeMatch


class Verdict(str, Enum):
    SAME = "same"
    BETTER = "better"
    WORSE = "worse"
    MISSING = "missing"


@dataclass(frozen=True)
class AttributeComparison:
    """One key attribute of the item beside the candidate's, as the alternative shows it."""

    name: str
    item_value: str
    candidate_value: str | None
    verdict: Verdict
    reason: str = ""

    def stored(self) -> dict:
        return {"name": self.name, "item": self.item_value, "candidate": self.candidate_value,
                "verdict": self.verdict.value, "reason": self.reason}


@dataclass
class MatchResult:
    """`match` is None when the candidate is not an alternative, and `rejected` says why."""

    match: AlternativeMatch | None
    comparison: list[AttributeComparison] = field(default_factory=list)
    rejected: str | None = None

    @property
    def accepted(self) -> bool:
        return self.match is not None
