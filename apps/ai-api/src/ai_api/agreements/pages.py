"""An agreement PDF as numbered pages: each page's text, or a picture of it."""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass

import pdfplumber

from .. import config
from ..documents.images import DocumentImage, pdf_page_image
from ..documents.numbers import normalize_numbers

logger = logging.getLogger("ai_api.agreements")


@dataclass(frozen=True)
class AgreementPage:
    """One page: its text layer, else a picture of it, else nothing readable."""

    number: int
    text: str | None = None
    image: DocumentImage | None = None


class UnreadablePdf(ValueError):
    """The bytes don't open as a PDF with pages."""


def agreement_pages(content: bytes) -> list[AgreementPage]:
    """Every page, text first; pages without text are pictured up to the configured cap."""
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            texts = [(page.extract_text() or "").strip() for page in pdf.pages]
    except Exception as error:  # noqa: BLE001
        raise UnreadablePdf(str(error)) from error
    if not texts:
        raise UnreadablePdf("the PDF has no pages")

    pages: list[AgreementPage] = []
    pictured = 0
    for index, text in enumerate(texts):
        number = index + 1
        if text:
            pages.append(AgreementPage(number, text=normalize_numbers(text)))
        elif pictured < config.AGREEMENT_VISION_MAX_PAGES:
            pages.append(AgreementPage(number, image=pdf_page_image(content, index)))
            pictured += 1
        else:
            pages.append(AgreementPage(number))
    skipped = sum(1 for page in pages if page.text is None and page.image is None)
    if skipped:
        logger.warning("agreement: %d page(s) without text were not read (cap %d)",
                       skipped, config.AGREEMENT_VISION_MAX_PAGES)
    return pages
