"""Run the agent on one line and hold it to a sector that exists."""
from __future__ import annotations

import logging
from collections.abc import Callable

from crewai import Agent
from crewai.tools.base_tool import Tool

from web_api.db.models import EmissionSector

from ... import config
from ...config import get_llm
from ...parsing import parse_model
from ..answer import MatchFailed, SectorAnswer, bounded
from ..line_context import LineContext
from .prompt import BACKSTORY, GOAL, ROLE, agent_prompt
from .reply import AgentReply

logger = logging.getLogger("ai_api.emissions.agent")

Kickoff = Callable[[list[Tool], str], str]


def agent_match(context: LineContext, tools: list[Tool],
                sectors_by_code: dict[str, EmissionSector], *,
                kickoff: Kickoff | None = None) -> SectorAnswer:
    """The agent's sector for the line, or MatchFailed when it gives no usable one."""
    run = kickoff or _kickoff
    try:
        reply = run(tools, agent_prompt(context))
    except Exception as error:  # noqa: BLE001
        raise MatchFailed(f"the agent stopped: {error}") from error
    try:
        answer = parse_model(reply, AgentReply)
    except Exception as error:  # noqa: BLE001
        raise MatchFailed(f"the agent's answer could not be read: {error}") from error

    if answer.code is None or not answer.code.strip():
        return SectorAnswer(None, bounded(answer.confidence), answer.rationale)
    sector = sectors_by_code.get(answer.code.strip())
    if sector is None:
        raise MatchFailed(f"the agent answered {answer.code!r}, which is no sector")
    return SectorAnswer(sector.id, bounded(answer.confidence), answer.rationale)


def _kickoff(tools: list[Tool], prompt: str) -> str:
    agent = Agent(
        role=ROLE, goal=GOAL, backstory=BACKSTORY, llm=get_llm(), tools=tools,
        max_iter=config.EMISSION_AGENT_MAX_ITER,
        max_execution_time=config.EMISSION_AGENT_TIMEOUT_S,
        allow_delegation=False, verbose=False,
    )
    return agent.kickoff(prompt).raw

