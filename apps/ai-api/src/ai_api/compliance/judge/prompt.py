"""What the judge is shown: one term and one invoice line."""
from __future__ import annotations

from web_api.db.models import AgreementTerm, AgreementTermKind

from ...parsing import json_format_hint
from ..lines import AnalysedLine
from .reply import JudgeReply

_KIND_QUESTIONS = {
    AgreementTermKind.PREFERRED_SUPPLIER.value:
        "Is what this line bought covered by the term's scope?",
    AgreementTermKind.DISCOUNT.value:
        "Is what this line bought in the range the discount applies to?",
    AgreementTermKind.VOLUME_COMMITMENT.value:
        "Does what this line bought count towards the commitment's scope?",
    AgreementTermKind.AGREED_PRICE.value: (
        "Is this line for the priced item itself (same make and model, not an accessory or a "
        "different model)? Set same_item accordingly, and in_scope the same way. Set "
        "units_comparable to false when the line is for a different unit than the agreed one, "
        "such as a box or pack against a single unit."
    ),
}


def judge_prompt(term: AgreementTerm, line: AnalysedLine) -> str:
    term_lines = [f"Kind: {term.kind}", f"Scope: {term.scope}"]
    if term.item:
        term_lines.append(f"Item: {term.item}")
    if term.unit:
        term_lines.append(f"Agreed per: {term.unit}")
    if term.conditions:
        term_lines.append(f"Conditions: {term.conditions}")
    line_lines = [
        f"Item: {line.item_name or '(none)'}",
        f"Description: {line.description or '(none)'}",
        f"Quantity: {line.quantity if line.quantity is not None else '(none)'} "
        f"{line.unit or ''}".rstrip(),
        f"Unit price: {line.unit_price if line.unit_price is not None else '(none)'} "
        f"{line.currency or ''}".rstrip(),
        f"Spend category: {' / '.join(line.category_path) or '(none)'}",
        f"Supplier: {line.vendor_name or '(unknown)'}",
    ]
    return "\n".join([
        "You check purchases against a term of a trade agreement. Judge only what the line "
        "bought, not who sold it.",
        _KIND_QUESTIONS.get(term.kind, _KIND_QUESTIONS[AgreementTermKind.PREFERRED_SUPPLIER.value]),
        "Give a confidence from 0 to 1 and one short sentence of reason.",
        "",
        "Term:",
        *term_lines,
        "",
        "Invoice line:",
        *line_lines,
        "",
        json_format_hint(JudgeReply),
    ])
