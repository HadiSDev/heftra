"""A stand-in for the specification reader's model: answers by the item's name."""
from __future__ import annotations

import json
import re

_PURCHASES = re.compile(r"^Purchase (\d+):\nItem: (.*)$", re.M)
_SINGLE = re.compile(r"^Purchase:\nItem: (.*)$", re.M)


def spec(name: str, **fields) -> dict:
    """A specification answer, as the model would give it."""
    return {"item_class": "finished_good", "product_type": "business laptop", "name": name,
            "pricing_unit": "piece", "units_per_line_unit": 1, "confidence": 0.9,
            "attributes": [], **fields}


class SpecModel:
    """Answers each purchase with the specification whose key its item name contains; counts
    prompts, and fails batches when told to."""

    def __init__(self, answers: dict[str, dict], *, fail_batches: bool = False) -> None:
        self.answers = answers
        self.fail_batches = fail_batches
        self.prompts = 0

    def __call__(self, prompt: str) -> str:
        self.prompts += 1
        numbered = _PURCHASES.findall(prompt)
        if numbered:
            if self.fail_batches:
                return "not json"
            return json.dumps({"answers": [{"n": int(number), **self._answer(name)}
                                           for number, name in numbered
                                           if self._answer(name) is not None]})
        (name,) = _SINGLE.findall(prompt)
        answer = self._answer(name)
        if answer is None:
            raise TimeoutError("the model did not answer")
        return json.dumps(answer)

    def _answer(self, name: str) -> dict | None:
        return next((answer for key, answer in self.answers.items() if key in name), None)
