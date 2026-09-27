"""The agent and its single-shot fallback, as one line-in, answer-out pair."""
from __future__ import annotations

from collections.abc import Callable
from typing import NamedTuple

from web_api.db.models import EmissionSector

from .. import config
from .agent.matcher import agent_match
from .agent.tools import make_tools
from .answer import SectorAnswer
from .choice.chooser import choose_sector
from .choice.prompt import search_query
from .line_context import LineContext
from .sector_index import SectorIndex

Match = Callable[[LineContext], SectorAnswer]


class Matchers(NamedTuple):
    """`agent` is tried first, `fallback` when it raises MatchFailed; None skips the agent."""

    agent: Match | None
    fallback: Match


def default_matchers(index: SectorIndex, classification: str,
                     sectors: list[EmissionSector]) -> Matchers:
    by_code = {sector.code: sector for sector in sectors}
    ids_by_code = {sector.code: sector.id for sector in sectors}

    def agent(context: LineContext) -> SectorAnswer:
        return agent_match(context, make_tools(context, index, classification, by_code), by_code)

    def fallback(context: LineContext) -> SectorAnswer:
        hits = index.search(classification, search_query(context),
                            config.EMISSION_FALLBACK_CANDIDATES)
        return choose_sector(context, hits, sector_ids_by_code=ids_by_code)

    return Matchers(agent if config.EMISSION_AGENT_ENABLED else None, fallback)
