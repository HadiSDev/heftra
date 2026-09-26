"""The single-shot question: a line and a numbered shortlist of sectors."""
from __future__ import annotations

from ...parsing import json_format_hint
from ..facts import line_facts
from ..line_context import LineContext
from ..sector_index import SectorHit
from .reply import ChoiceReply

INSTRUCTIONS = (
    "You are a carbon accountant matching one invoice line to the industry sector whose "
    "products or services it paid for, so its spend can be turned into an emissions estimate. "
    "Classify by what was bought, not by who sold it.\n"
    "\n"
    "Choose the best sector from the numbered list and answer with its number. Give a sector "
    "whenever one is plausible and put your doubt in the confidence (0.9 plainly right, 0.3 "
    "closest of poor options). Answer 0 only when the line is not a purchase at all."
)


def search_query(context: LineContext) -> str:
    """What the shortlist is retrieved with: the line, its category and its supplier."""
    parts = [context.item_name, context.description, " > ".join(context.category_path),
             (context.supplier_description or "")[:300]]
    return " ".join(part for part in parts if part)


def choice_prompt(context: LineContext, hits: list[SectorHit]) -> str:
    facts = "\n".join(line_facts(context))
    if context.supplier_description:
        facts += f"\nAbout the supplier: {context.supplier_description}"
    numbered = "\n".join(
        f"{number}. {hit.code} — {hit.name}: {hit.summary}"
        for number, hit in enumerate(hits, start=1)
    )
    return (
        f"{INSTRUCTIONS}\n\nInvoice line:\n{facts}\n\nSectors:\n{numbered}\n\n"
        + json_format_hint(ChoiceReply, allow_reasoning=True)
    )
