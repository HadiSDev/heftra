"""A finding as analysis works it out, before it is stored."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from web_api.db.models import FindingKind, FindingSeverity

from .lines import AnalysedLine

SEVERITY = {
    FindingKind.OFF_CONTRACT: FindingSeverity.RULE_BREAK,
    FindingKind.OVERCHARGE: FindingSeverity.RULE_BREAK,
    FindingKind.MISSED_DISCOUNT: FindingSeverity.WARNING,
    FindingKind.PRICE_UNVERIFIABLE: FindingSeverity.WARNING,
    FindingKind.POTENTIAL_SAVING: FindingSeverity.INFO,
    FindingKind.COMPLIANT: FindingSeverity.INFO,
}


@dataclass(frozen=True)
class FindingDraft:
    term_id: str
    line: AnalysedLine
    kind: FindingKind
    amount: Decimal
    reason: str
    from_supplier: bool
    confidence: Decimal | None = None
    expected: Decimal | None = None
    actual: Decimal | None = None

    @property
    def severity(self) -> FindingSeverity:
        return SEVERITY[self.kind]
