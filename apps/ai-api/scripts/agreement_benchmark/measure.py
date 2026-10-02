"""What one analysis costs: wall time, peak memory, model questions, embeddings and queries."""
from __future__ import annotations

import json
import re
import resource
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field

from sqlalchemy import event
from sqlalchemy.engine import Engine

_PURCHASES = re.compile(r"^Purchase (\d+):\n(.*?)(?=\n\n)", re.M | re.S)

IT_WORDS = ("laptop", "macbook", "thinkpad", "keyboard", "mouse", "trackpad", "monitor", "drive",
            "sandisk", "adapter", "headset", "webcam", "docking", "cable", "ssd")


@dataclass
class Cost:
    seconds: float = 0.0
    embed_seconds: float = 0.0
    judge_seconds: float = 0.0
    texts_embedded: int = 0
    questions: int = 0
    queries: int = 0
    peak_rss_mb: float = 0.0
    summary: dict = field(default_factory=dict)

    def as_json(self) -> str:
        return json.dumps(asdict(self), indent=2, default=str)


def stub_answer(prompt: str) -> str:
    """In scope when a purchase names IT equipment; the priced item when it names a ThinkPad.
    A numbered batch is answered by number."""
    numbered = _PURCHASES.findall(prompt)
    if numbered:
        return json.dumps({"answers": [{"n": int(number), **_verdict(text)}
                                       for number, text in numbered]})
    return json.dumps(_verdict(prompt.split("Purchase:", 1)[-1]))


def _verdict(purchase: str) -> dict:
    asked = purchase.split("\n\n", 1)[0].lower()
    return {"in_scope": any(word in asked for word in IT_WORDS),
            "same_item": "thinkpad" in asked, "units_comparable": True, "confidence": 0.9,
            "reason": "Benchmark stub."}


def measured(engine: Engine, cost: Cost, embed: Callable, ask: Callable,
             run: Callable[[Callable, Callable], dict]) -> Cost:
    """Run `run(ask, embed)` with both wrapped, counting queries on `engine`."""
    def count_query(*_args) -> None:
        cost.queries += 1

    def timed_embed(texts: list[str]) -> list[list[float]]:
        started = time.perf_counter()
        vectors = embed(texts)
        cost.embed_seconds += time.perf_counter() - started
        cost.texts_embedded += len(texts)
        return vectors

    def timed_ask(prompt: str) -> str:
        started = time.perf_counter()
        answer = ask(prompt)
        cost.judge_seconds += time.perf_counter() - started
        cost.questions += 1
        return answer

    event.listen(engine, "before_cursor_execute", count_query)
    started = time.perf_counter()
    try:
        cost.summary = run(timed_ask, timed_embed)
    finally:
        cost.seconds = time.perf_counter() - started
        event.remove(engine, "before_cursor_execute", count_query)
        cost.peak_rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    return cost
