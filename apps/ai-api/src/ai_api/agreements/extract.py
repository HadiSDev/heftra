"""Reading an agreement into its header and draft terms, one page at a time."""
from __future__ import annotations

import base64
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel

from .. import config
from ..parsing import json_format_hint, parse_model
from .models import ReadHeader, ReadTerms
from .pages import AgreementPage
from .prompts import HEADER, TERMS, page_marker
from .terms import DraftTerm, draft_term, merge_terms

logger = logging.getLogger("ai_api.agreements")

Complete = Callable[[list[dict]], str]
T = TypeVar("T", bound=BaseModel)


class AgreementUnreadable(RuntimeError):
    """No part of the agreement could be read."""


@dataclass(frozen=True)
class ReadAgreement:
    header: ReadHeader
    terms: list[DraftTerm]
    pages: int
    failed_pages: int
    dropped_terms: int


def read_agreement(pages: list[AgreementPage], *, complete: Complete) -> ReadAgreement:
    readable = [page for page in pages if page.text or page.image]
    if not readable:
        raise AgreementUnreadable("no page of the agreement has text or could be pictured")

    header = _ask(complete, HEADER, readable[:config.AGREEMENT_HEADER_PAGES], ReadHeader) \
        or ReadHeader()
    drafts: list[DraftTerm] = []
    failed = 0
    dropped = 0
    for page in readable:
        read = _ask(complete, TERMS, [page], ReadTerms)
        if read is None:
            failed += 1
            continue
        for term in read.terms:
            draft = draft_term(term, [page])
            if draft is None:
                dropped += 1
                logger.info("agreement: dropped a %s term whose quote or fields don't hold up",
                            term.kind or "unknown")
            else:
                drafts.append(draft)
    if failed == len(readable):
        raise AgreementUnreadable(f"none of the {len(readable)} page(s) could be read")
    return ReadAgreement(header, merge_terms(drafts), len(readable), failed, dropped)


def _ask(complete: Complete, instructions: str, pages: list[AgreementPage],
         model: type[T]) -> T | None:
    try:
        return parse_model(complete(_messages(instructions, pages, model)), model)
    except Exception as error:  # noqa: BLE001
        logger.warning("agreement: pages %s could not be read: %s",
                       [page.number for page in pages], error)
        return None


def _messages(instructions: str, pages: list[AgreementPage], model: type[BaseModel]) -> list[dict]:
    parts: list[dict] = [{"type": "text", "text": instructions}]
    for page in pages:
        if page.text:
            parts.append({"type": "text", "text": f"{page_marker(page.number)}\n{page.text}"})
        elif page.image:
            encoded = base64.b64encode(page.image.content).decode("ascii")
            parts.append({"type": "text", "text": page_marker(page.number)})
            parts.append({"type": "image_url",
                          "image_url": {"url": f"data:{page.image.media_type};base64,{encoded}"}})
    parts.append({"type": "text", "text": json_format_hint(model)})
    return [{"role": "user", "content": parts}]
