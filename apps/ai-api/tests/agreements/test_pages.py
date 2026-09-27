"""An agreement PDF read page by page: text where there is some, a picture where there isn't."""
from __future__ import annotations

import pytest

from agreement_pdf import agreement_pdf
from ai_api import config
from ai_api.agreements.pages import UnreadablePdf, agreement_pages


def test_pages_with_text_are_read_as_text():
    pages = agreement_pages(agreement_pdf([["Page one"], ["Page two"]]))

    assert [(page.number, page.text) for page in pages] == [(1, "Page one"), (2, "Page two")]


def test_a_page_without_text_is_pictured():
    (first, blank) = agreement_pages(agreement_pdf([["Page one"], []]))

    assert first.image is None
    assert blank.text is None and blank.image is not None


def test_pictures_are_capped(monkeypatch):
    monkeypatch.setattr(config, "AGREEMENT_VISION_MAX_PAGES", 1)

    pages = agreement_pages(agreement_pdf([[], []]))

    assert pages[0].image is not None
    assert pages[1].image is None and pages[1].text is None


def test_bytes_that_are_not_a_pdf_are_refused():
    with pytest.raises(UnreadablePdf):
        agreement_pages(b"not a pdf")
