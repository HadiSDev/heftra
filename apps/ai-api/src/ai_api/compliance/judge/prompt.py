"""What the judge is shown: one term, and one item or a numbered batch of items."""
from __future__ import annotations

from web_api.db.models import AgreementTerm, AgreementTermKind

from ...items.item import Item
from ...parsing import json_format_hint
from .reply import BatchReply, JudgeReply

_KIND_QUESTIONS = {
    AgreementTermKind.PREFERRED_SUPPLIER.value:
        "Is what was bought covered by the term's scope?",
    AgreementTermKind.DISCOUNT.value:
        "Is what was bought in the range the discount applies to?",
    AgreementTermKind.VOLUME_COMMITMENT.value:
        "Does what was bought count towards the commitment's scope?",
    AgreementTermKind.AGREED_PRICE.value: (
        "Is the purchase the priced item itself (same make and model, not an accessory or a "
        "different model)? Set same_item accordingly, and in_scope the same way. Set "
        "units_comparable to false when it is bought in a different unit than the agreed one, "
        "such as a box or pack against a single unit."
    ),
}

_RULES = [
    "When the scope says what one of its words means (In this agreement, \"Accessories\" "
    "means keyboards, mice and cables), a purchase is covered by that word only if what it "
    "bought is one of the things listed in that meaning. Something of another kind is not, "
    "however much it seems to belong with them.",
    "Use what the buyer does only to tell what an item is to them: a smartwatch is a "
    "development device to a company that builds software for watches, and a personal "
    "item to most others. Do not count something as in scope because the buyer might use "
    "it for work, and never let it override what the scope lists.",
    "Give a confidence from 0 to 1 and one short sentence of reason.",
]


def judge_prompt(term: AgreementTerm, item: Item, buyer: str = "") -> str:
    """The question about one item."""
    return "\n".join([
        *_preamble(term, buyer),
        "Purchase:",
        *_item_lines(item),
        "",
        json_format_hint(JudgeReply),
    ])


def batch_prompt(term: AgreementTerm, items: list[Item], buyer: str = "") -> str:
    """The question about several items at once, each answered separately by its number."""
    purchases: list[str] = []
    for number, item in enumerate(items, start=1):
        purchases.extend([f"Purchase {number}:", *_item_lines(item), ""])
    return "\n".join([
        *_preamble(term, buyer),
        f"Judge each of these {len(items)} purchases on its own, and answer for every one by "
        "its number.",
        "",
        *purchases,
        json_format_hint(BatchReply),
    ])


def _preamble(term: AgreementTerm, buyer: str) -> list[str]:
    return [
        "You check purchases against a term of a trade agreement. Judge only what was bought, "
        "not who sold it.",
        _KIND_QUESTIONS.get(term.kind, _KIND_QUESTIONS[AgreementTermKind.PREFERRED_SUPPLIER.value]),
        *_RULES,
        "",
        f"The buyer: {buyer or '(not described)'}",
        "",
        "Term:",
        *_term_lines(term),
        "",
    ]


def _term_lines(term: AgreementTerm) -> list[str]:
    lines = [f"Kind: {term.kind}", f"Scope: {term.scope}"]
    if term.item:
        lines.append(f"Item: {term.item}")
    if term.unit:
        lines.append(f"Agreed per: {term.unit}")
    if term.conditions:
        lines.append(f"Conditions: {term.conditions}")
    return lines


def _item_lines(item: Item) -> list[str]:
    return [
        f"Item: {item.item_name or '(none)'}",
        f"Description: {item.description or '(none)'}",
        f"Bought per: {item.unit or '(none)'}",
        f"Typical unit price: {item.unit_price if item.unit_price is not None else '(none)'}",
        f"Spend category: {' / '.join(item.category_path) or '(none)'}",
        f"Supplier: {item.vendor_name or '(unknown)'}",
    ]
