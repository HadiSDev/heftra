"""The single-shot fallback picks a numbered sector from a shortlist."""
from __future__ import annotations

import pytest

from ai_api.emissions.answer import MatchFailed
from ai_api.emissions.choice.chooser import choose_sector
from ai_api.emissions.choice.prompt import choice_prompt
from ai_api.emissions.sector_index import SectorHit
from emission_matching_kit import context

HITS = [
    SectorHit("s-hosting", "518200", "Data processing, hosting", "Hosting."),
    SectorHit("s-software", "511200", "Software publishers", "Software."),
]


def test_the_chosen_number_becomes_the_sector():
    answer = choose_sector(context(), HITS, complete=lambda _: (
        'Hosting fits. {"choice": 1, "confidence": 0.8, "rationale": "A rented server."}'))

    assert (answer.sector_id, answer.confidence) == ("s-hosting", 0.8)


def test_zero_means_nothing_fits():
    answer = choose_sector(context(), HITS, complete=lambda _: (
        '{"choice": 0, "confidence": 0.7, "rationale": "Not a purchase."}'))

    assert answer.sector_id is None


@pytest.mark.parametrize("reply", [
    '{"choice": 7, "confidence": 0.9, "rationale": "x"}',
    "no idea",
])
def test_an_out_of_range_or_unreadable_answer_fails(reply):
    with pytest.raises(MatchFailed):
        choose_sector(context(), HITS, complete=lambda _: reply)


def test_no_shortlist_fails_without_asking():
    with pytest.raises(MatchFailed):
        choose_sector(context(), [], complete=lambda _: pytest.fail("asked"))


def test_the_prompt_numbers_the_sectors_and_tells_the_supplier():
    prompt = choice_prompt(context(), HITS)

    assert "1. 518200 — Data processing, hosting" in prompt
    assert "German hosting company." in prompt


def test_a_real_code_instead_of_a_number_is_taken():
    answer = choose_sector(
        context(), HITS,
        complete=lambda _: '{"choice": 311920, "confidence": 0.8, "rationale": "Coffee."}',
        sector_ids_by_code={"311920": "s-coffee"},
    )

    assert answer.sector_id == "s-coffee"
