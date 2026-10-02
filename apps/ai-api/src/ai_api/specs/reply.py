"""The reader's answer for each of a batch of items."""
from __future__ import annotations

from pydantic import BaseModel

from .specification import Specification


class NumberedSpecification(Specification):
    n: int = 0


class BatchSpecifications(BaseModel):
    answers: list[NumberedSpecification] = []
