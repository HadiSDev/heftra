"""The agent's tools answer about its one line, and its answer must name a real sector."""
from __future__ import annotations

import pytest

from ai_api.emissions.agent.matcher import agent_match
from ai_api.emissions.agent.tools import make_tools
from ai_api.emissions.answer import MatchFailed
from emission_matching_kit import context, index_of, sectors


@pytest.fixture
def setup():
    all_sectors = sectors()
    by_code = {sector.code: sector for sector in all_sectors}
    line = context()
    agent_tools = make_tools(line, index_of(all_sectors), "ceda-bea", by_code)
    return line, agent_tools, by_code


def _named(agent_tools):
    return {tool.name: tool for tool in agent_tools.tools}


def _searching_then(agent_tools, reply):
    """A kickoff that searches as a real agent would, then replies."""

    def kickoff(tools, prompt):
        _named(agent_tools)["search_sectors"].run(query="data center hosting")
        return reply

    return kickoff


def test_searching_lists_the_nearest_sectors(setup):
    _, agent_tools, _ = setup

    found = _named(agent_tools)["search_sectors"].run(query="data center hosting")

    assert found.splitlines()[0].startswith("518200 — Data processing, hosting")


def test_a_sectors_details_are_read_by_code(setup):
    _, agent_tools, _ = setup
    tools = _named(agent_tools)

    assert "Publishing software." in tools["sector_details"].run(code="511200")
    assert "No sector" in tools["sector_details"].run(code="000000")


def test_the_supplier_and_other_lines_are_the_lines_own(setup):
    _, agent_tools, _ = setup
    tools = _named(agent_tools)

    assert "German hosting company." in tools["supplier_profile"].run()
    assert tools["other_lines"].run() == "- Backup space"


def test_a_code_a_tool_showed_becomes_the_answer(setup):
    line, agent_tools, by_code = setup
    reply = '{"code": "518200", "confidence": 1.4, "rationale": "A rented server."}'

    answer = agent_match(line, agent_tools, by_code, kickoff=_searching_then(agent_tools, reply))

    assert answer.sector_id == by_code["518200"].id
    assert answer.confidence == 1.0
    assert answer.rationale == "A rented server."


def test_no_code_means_nothing_fits(setup):
    line, agent_tools, by_code = setup
    reply = '{"code": null, "confidence": 0.8, "rationale": "A rounding line."}'

    assert agent_match(line, agent_tools, by_code, kickoff=lambda *_: reply).sector_id is None


def test_a_real_code_no_tool_showed_fails(setup):
    line, agent_tools, by_code = setup
    reply = '{"code": "511200", "confidence": 0.9, "rationale": "From memory."}'

    with pytest.raises(MatchFailed, match="no tool showed"):
        agent_match(line, agent_tools, by_code, kickoff=lambda *_: reply)


@pytest.mark.parametrize("reply", [
    '{"code": "999999", "confidence": 0.9, "rationale": "Made up."}',
    "I think it is hosting.",
])
def test_an_unknown_code_or_an_unreadable_answer_fails(setup, reply):
    line, agent_tools, by_code = setup

    with pytest.raises(MatchFailed):
        agent_match(line, agent_tools, by_code, kickoff=_searching_then(agent_tools, reply))


def test_an_agent_that_stops_fails(setup):
    line, agent_tools, by_code = setup

    def stops(*_):
        raise TimeoutError("took too long")

    with pytest.raises(MatchFailed, match="took too long"):
        agent_match(line, agent_tools, by_code, kickoff=stops)
