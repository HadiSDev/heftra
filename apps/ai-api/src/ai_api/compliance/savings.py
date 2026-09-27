"""What a purchase made off contract would have saved, told with its rule break."""
from __future__ import annotations

from dataclasses import replace

from web_api.db.models import FindingKind

from .drafts import FindingDraft


def fold_savings(drafts: list[FindingDraft], currency: str | None) -> list[FindingDraft]:
    """Each off-contract line's potential savings, moved into its off-contract finding."""
    off_contract = {draft.line.line_id for draft in drafts
                    if draft.kind == FindingKind.OFF_CONTRACT}
    savings: dict[str, list[FindingDraft]] = {}
    for draft in drafts:
        if draft.kind == FindingKind.POTENTIAL_SAVING and draft.line.line_id in off_contract:
            savings.setdefault(draft.line.line_id, []).append(draft)
    folded: list[FindingDraft] = []
    for draft in drafts:
        if draft.kind == FindingKind.POTENTIAL_SAVING and draft.line.line_id in savings:
            continue
        if draft.kind == FindingKind.OFF_CONTRACT and draft.line.line_id in savings:
            draft = _with_savings(draft, savings[draft.line.line_id], currency)
        folded.append(draft)
    return folded


def _with_savings(rule_break: FindingDraft, savings: list[FindingDraft],
                  currency: str | None) -> FindingDraft:
    priced = next((saving for saving in savings if saving.actual is not None), None)
    told = " ".join(f"{saving.reason} On the agreement's terms it would have cost "
                    f"{saving.amount:,.2f} {currency or ''}".rstrip() + " less."
                    for saving in savings)
    return replace(
        rule_break,
        reason=f"{rule_break.reason} {told}",
        expected=priced.expected if priced else rule_break.expected,
        actual=priced.actual if priced else rule_break.actual,
    )
