"""Ask the model once to pick a sector from a shortlist."""
from __future__ import annotations

from collections.abc import Callable

from ...config import get_llm
from ...parsing import parse_model
from ..answer import MatchFailed, SectorAnswer, bounded
from ..line_context import LineContext
from ..sector_index import SectorHit
from .prompt import choice_prompt
from .reply import ChoiceReply

Complete = Callable[[str], str]


def choose_sector(context: LineContext, hits: list[SectorHit], *,
                  complete: Complete | None = None,
                  sector_ids_by_code: dict[str, str] | None = None) -> SectorAnswer:
    """The shortlisted sector the model picks, none when it says none fits, else MatchFailed.

    A model that answers with a real sector code instead of a list number is taken at its word.
    """
    if not hits:
        raise MatchFailed("no sectors were found to choose from")
    ask = complete or _complete
    try:
        reply = ask(choice_prompt(context, hits))
    except Exception as error:  # noqa: BLE001
        raise MatchFailed(f"the model could not be reached: {error}") from error
    try:
        answer = parse_model(reply, ChoiceReply)
    except Exception as error:  # noqa: BLE001
        raise MatchFailed(f"the model's answer could not be read: {error}") from error

    confidence = bounded(answer.confidence)
    if answer.choice == 0:
        return SectorAnswer(None, confidence, answer.rationale)
    if 1 <= answer.choice <= len(hits):
        return SectorAnswer(hits[answer.choice - 1].sector_id, confidence, answer.rationale)
    named = (sector_ids_by_code or {}).get(str(answer.choice))
    if named is not None:
        return SectorAnswer(named, confidence, answer.rationale)
    raise MatchFailed(f"the model chose {answer.choice}, outside the {len(hits)} offered")


def _complete(prompt: str) -> str:
    return get_llm().call(prompt)
