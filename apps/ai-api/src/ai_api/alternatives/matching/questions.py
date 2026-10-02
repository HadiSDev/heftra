"""What the LLM is asked about a candidate, and its answer."""
from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, field_validator

from web_api.specs.specification import Specification

from .verdicts import Verdict


@dataclass(frozen=True)
class Question:
    """A candidate whose kind of product, or some of whose attributes, code couldn't decide."""

    key: str
    candidate: Specification
    ask_kind: bool
    attributes: tuple[str, ...]


class AttributeAnswer(BaseModel):
    name: str
    verdict: Verdict = Verdict.WORSE
    reason: str = ""

    @field_validator("verdict", mode="before")
    @classmethod
    def _verdict(cls, value: object) -> object:
        text = str(value or "").strip().lower()
        return text if text in {verdict.value for verdict in Verdict} else Verdict.WORSE.value


class CandidateAnswer(BaseModel):
    n: int = 0
    same_kind: bool = False
    kind_reason: str = ""
    attributes: list[AttributeAnswer] = []


class Answers(BaseModel):
    candidates: list[CandidateAnswer] = []
