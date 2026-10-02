"""Matching candidates to an item: exact, or equivalent and never worse."""
from __future__ import annotations

from dataclasses import dataclass

from web_api.db.models import AlternativeMatch
from web_api.specs.attribute import Attribute, AttributeKind
from web_api.specs.specification import Specification

from ... import config
from .exact import is_exact
from .judge import PairJudge
from .numbers import compare_numbers
from .questions import CandidateAnswer, Question
from .tiers import compare_tiers
from .verdicts import AttributeComparison, MatchResult, Verdict

SYNONYMS = {
    "ram": "memory", "memory_size": "memory", "ram_size": "memory",
    "storage_capacity": "storage", "ssd": "storage", "ssd_capacity": "storage",
    "cpu": "processor", "processor_model": "processor",
    "display_size": "screen_size", "screen": "screen_size", "screen_diagonal": "screen_size",
    "grade": "steel_grade", "material_grade": "steel_grade",
    "plies": "ply", "layers": "ply", "number_of_plies": "ply",
}
REJECTING = (Verdict.WORSE, Verdict.MISSING)


@dataclass(frozen=True)
class Candidate:
    key: str
    spec: Specification
    product_id: str | None


@dataclass(frozen=True)
class _Partial:
    decided: list[AttributeComparison]
    undecided: list[Attribute]


def match_candidates(item: Specification, item_product: str | None,
                     candidates: list[Candidate], judge: PairJudge) -> dict[str, MatchResult]:
    """Each candidate's match, deciding in code what it can and asking the LLM the rest."""
    results: dict[str, MatchResult] = {}
    partials: dict[str, _Partial] = {}
    questions: list[Question] = []
    for candidate in candidates:
        spec = candidate.spec
        if spec.item_class != item.item_class or spec.pricing_unit != item.pricing_unit:
            results[candidate.key] = MatchResult(None, rejected="another class or pricing unit")
            continue
        if is_exact(item, item_product, spec, candidate.product_id):
            results[candidate.key] = MatchResult(AlternativeMatch.EXACT, _side_by_side(item, spec))
            continue
        partial = _in_code(item, spec)
        if any(comparison.verdict in REJECTING for comparison in partial.decided):
            results[candidate.key] = MatchResult(None, partial.decided, rejected="worse")
            continue
        ask_kind = _words(spec.product_type) != _words(item.product_type)
        if not ask_kind and not partial.undecided:
            results[candidate.key] = MatchResult(AlternativeMatch.EQUIVALENT, partial.decided)
            continue
        partials[candidate.key] = partial
        questions.append(Question(candidate.key, spec, ask_kind,
                                  tuple(attribute.name for attribute in partial.undecided)))
    answers = judge.answer(item, questions) if questions else {}
    for question in questions:
        results[question.key] = _judged(item, question, partials[question.key],
                                        answers.get(question.key))
    return results


def _in_code(item: Specification, candidate: Specification) -> _Partial:
    stated = {_canonical(attribute.name): attribute for attribute in candidate.attributes}
    decided: list[AttributeComparison] = []
    undecided: list[Attribute] = []
    for attribute in item.attributes:
        theirs = stated.get(_canonical(attribute.name))
        verdict = _verdict(attribute, theirs) if theirs is not None else None
        if verdict is None:
            undecided.append(attribute)
        else:
            decided.append(AttributeComparison(attribute.name, _shown(attribute), _shown(theirs),
                                               verdict))
    return _Partial(decided, undecided)


def _verdict(mine: Attribute, theirs: Attribute) -> Verdict | None:
    if mine.kind == AttributeKind.NUMERIC:
        return compare_numbers(mine, theirs, config.ALTERNATIVES_EQUAL_TOLERANCE_PERCENT)
    if mine.kind == AttributeKind.TIERED:
        return compare_tiers(mine, theirs)
    return Verdict.SAME if _words(mine.value) == _words(theirs.value) else None


def _judged(item: Specification, question: Question, partial: _Partial,
            answer: CandidateAnswer | None) -> MatchResult:
    if answer is None:
        return MatchResult(None, partial.decided, rejected="could not be compared")
    if question.ask_kind and not answer.same_kind:
        return MatchResult(None, partial.decided,
                           rejected=f"another kind of product: {answer.kind_reason}".strip())
    answered = {_canonical(found.name): found for found in answer.attributes}
    stated = {_canonical(attribute.name): attribute for attribute in question.candidate.attributes}
    comparison = list(partial.decided)
    for attribute in partial.undecided:
        found = answered.get(_canonical(attribute.name))
        theirs = stated.get(_canonical(attribute.name))
        comparison.append(AttributeComparison(
            attribute.name, _shown(attribute), _shown(theirs) if theirs else None,
            found.verdict if found is not None else Verdict.MISSING,
            found.reason if found is not None else "Not answered."))
    if any(entry.verdict in REJECTING for entry in comparison):
        return MatchResult(None, comparison, rejected="worse")
    return MatchResult(AlternativeMatch.EQUIVALENT, comparison)


def _side_by_side(item: Specification, candidate: Specification) -> list[AttributeComparison]:
    stated = {_canonical(attribute.name): attribute for attribute in candidate.attributes}
    return [AttributeComparison(attribute.name, _shown(attribute),
                                _shown(stated[_canonical(attribute.name)])
                                if _canonical(attribute.name) in stated else None,
                                Verdict.SAME, "The same product.")
            for attribute in item.attributes]


def _canonical(name: str) -> str:
    return SYNONYMS.get(name, name)


def _shown(attribute: Attribute) -> str:
    if attribute.kind == AttributeKind.NUMERIC and attribute.number is not None:
        return f"{attribute.number:g} {attribute.unit or ''}".strip()
    return attribute.value


def _words(text: str | None) -> str:
    return " ".join((text or "").lower().split())
