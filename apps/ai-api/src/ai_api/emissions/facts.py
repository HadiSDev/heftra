"""A line's facts as a matcher is told them, leaving out what is not known."""
from __future__ import annotations

from .line_context import LineContext


def line_facts(context: LineContext) -> list[str]:
    facts: list[str] = []
    name = (context.item_name or "").strip()
    detail = (context.description or "").strip()
    if name:
        facts.append(f"Item: {name}")
    if detail and detail != name:
        facts.append(f"Detail: {detail}")
    if context.amount is not None:
        facts.append(f"Amount: {context.amount}" + (f" {context.currency}" if context.currency
                                                    else ""))
    if context.category_path:
        facts.append(f"Spend category: {' > '.join(context.category_path)}")
    if context.supplier_name:
        facts.append(f"Supplier: {context.supplier_name}")
    if context.supplier_country:
        facts.append(f"Supplier country: {context.supplier_country}")
    return facts or ["(no details were recorded for this line)"]
