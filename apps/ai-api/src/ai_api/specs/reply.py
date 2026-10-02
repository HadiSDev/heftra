"""The reader's answer for each of a batch of items."""
from __future__ import annotations

from pydantic import BaseModel
from web_api.specs.specification import Specification



class NumberedSpecification(Specification):
    n: int = 0


class BatchSpecifications(BaseModel):
    answers: list[NumberedSpecification] = []
