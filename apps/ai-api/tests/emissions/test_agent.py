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
    tools = make_tools(line, index_of(all_sectors), "ceda-bea", by_code)
    return line, {tool.name: tool for tool in tools}, by_code


def test_searching_lists_the_nearest_sectors(setup):
    _, tools, _ = setup

    found = tools["search_sectors"].run(query="data center hosting")

    assert found.splitlines()[0].startswith("518200 — Data processing, hosting")


def test_a_sectors_details_are_read_by_code(setup):
    _, tools, _ = setup

    assert "Publishing software." in tools["sector_details"].run(code="511200")
    assert "No sector" in tools["sector_details"].run(code="000000")


def test_the_supplier_and_other_lines_are_the_lines_own(setup):
    _, tools, _ = setup

    assert "German hosting company." in tools["supplier_profile"].run()
    assert tools["other_lines"].run() == "- Backup space"


def test_a_known_code_becomes_the_answer(setup):
    line, tools, by_code = setup
    reply = '{"code": "518200", "confidence": 1.4, "rationale": "A rented server."}'

    answer = agent_match(line, list(tools.values()), by_code, kickoff=lambda *_: reply)

    assert answer.sector_id == by_code["518200"].id
    assert answer.confidence == 1.0
    assert answer.rationale == "A rented server."


def test_no_code_means_nothing_fits(setup):
    line, tools, by_code = setup
    reply = '{"code": null, "confidence": 0.8, "rationale": "A rounding line."}'

    assert agent_match(line, list(tools.values()), by_code,
                       kickoff=lambda *_: reply).sector_id is None


@pytest.mark.parametrize("reply", [
    '{"code": "999999", "confidence": 0.9, "rationale": "Made up."}',
    "I think it is hosting.",
])
def test_an_unknown_code_or_an_unreadable_answer_fails(setup, reply):
    line, tools, by_code = setup

    with pytest.raises(MatchFailed):
        agent_match(line, list(tools.values()), by_code, kickoff=lambda *_: reply)


def test_an_agent_that_stops_fails(setup):
    line, tools, by_code = setup

    def stops(*_):
        raise TimeoutError("took too long")

    with pytest.raises(MatchFailed, match="took too long"):
        agent_match(line, list(tools.values()), by_code, kickoff=stops)
