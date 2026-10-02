"""Reading items' specifications with the LLM, a numbered batch to a prompt."""
from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from web_api.specs.specification import Specification

from .. import config
from ..parsing import parse_model
from .prompt import ItemText, batch_spec_prompt, spec_prompt
from .reply import BatchSpecifications

logger = logging.getLogger("ai_api.specs")

Ask = Callable[[str], str]


class SpecReader:
    """Reads specifications, `batch` items to a prompt and `concurrency` prompts at a time; a
    batch that can't be read is asked again one item at a time."""

    def __init__(self, ask: Ask, *, batch: int | None = None,
                 concurrency: int | None = None) -> None:
        self._ask = ask
        self._batch = max(1, batch or config.ALTERNATIVES_SPEC_BATCH)
        self._concurrency = max(1, concurrency or config.ALTERNATIVES_SPEC_CONCURRENCY)

    def read(self, items: dict[str, ItemText]) -> dict[str, Specification]:
        """The specification of each item that could be read, by its key in `items`."""
        keys = list(items)
        batches = [keys[start:start + self._batch] for start in range(0, len(keys), self._batch)]
        read: dict[str, Specification] = {}
        if not batches:
            return read
        with ThreadPoolExecutor(max_workers=min(self._concurrency, len(batches))) as pool:
            for answered in pool.map(lambda batch: self._read_batch(batch, items), batches):
                read.update(answered)
        return read

    def _read_batch(self, keys: list[str], items: dict[str, ItemText]) -> dict[str, Specification]:
        if len(keys) == 1:
            return self._read_each(keys, items)
        try:
            reply = parse_model(self._ask(batch_spec_prompt([items[key] for key in keys])),
                                BatchSpecifications)
        except Exception as error:  # noqa: BLE001
            logger.warning("specs: a batch of %d item(s) was not read, reading one at a time: %s",
                           len(keys), error)
            return self._read_each(keys, items)
        by_number = {answer.n: answer for answer in reply.answers}
        read = {key: Specification.model_validate(by_number[number].model_dump(mode="json", exclude={"n"}))
                for number, key in enumerate(keys, start=1) if number in by_number}
        return {**read, **self._read_each([key for key in keys if key not in read], items)}

    def _read_each(self, keys: list[str], items: dict[str, ItemText]) -> dict[str, Specification]:
        read: dict[str, Specification] = {}
        for key in keys:
            try:
                read[key] = parse_model(self._ask(spec_prompt(items[key])), Specification)
            except Exception as error:  # noqa: BLE001
                logger.warning("specs: item %s was not read: %s", key[:12], error)
        return read
