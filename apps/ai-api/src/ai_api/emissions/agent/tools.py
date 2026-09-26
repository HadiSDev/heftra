"""The agent's tools, bound to the one line it is matching."""
from __future__ import annotations

from crewai.tools import tool
from crewai.tools.base_tool import Tool

from web_api.db.models import EmissionSector

from ... import config
from ..line_context import LineContext
from ..sector_index import SectorIndex


def make_tools(context: LineContext, index: SectorIndex, classification: str,
               sectors_by_code: dict[str, EmissionSector]) -> list[Tool]:
    """Search, sector details, supplier profile and other lines, for `context`'s line."""

    @tool("search_sectors")
    def search_sectors(query: str) -> str:
        """Find the emission sectors closest to a short description of what was bought,
        such as "data center hosting" or "passenger airline tickets". Returns code, name and
        the start of each sector's description."""
        hits = index.search(classification, query, config.EMISSION_SEARCH_RESULTS)
        if not hits:
            return "No sectors matched. Try other words."
        return "\n".join(f"{hit.code} — {hit.name}: {hit.summary}" for hit in hits)

    @tool("sector_details")
    def sector_details(code: str) -> str:
        """Read the full description of one sector by its code, to tell close sectors apart."""
        sector = sectors_by_code.get(code.strip())
        if sector is None:
            return f"No sector has the code {code!r}."
        return f"{sector.code} — {sector.name}: {sector.description or '(no description)'}"

    @tool("supplier_profile")
    def supplier_profile() -> str:
        """Read what is known about the supplier: its description, website and country."""
        known = [
            f"Description: {context.supplier_description}" if context.supplier_description
            else None,
            f"Website: {context.supplier_website}" if context.supplier_website else None,
            f"Country: {context.supplier_country}" if context.supplier_country else None,
        ]
        facts = [fact for fact in known if fact]
        if not facts:
            return "Nothing is known about the supplier beyond its name."
        return "\n".join(facts)

    @tool("other_lines")
    def other_lines() -> str:
        """List the other lines of the same invoice, for context on a vague line."""
        if not context.other_lines:
            return "The invoice has no other lines."
        return "\n".join(f"- {label}" for label in context.other_lines)

    return [search_sectors, sector_details, supplier_profile, other_lines]
