"""A plain agreement PDF holding the clauses the terms quote, one list of lines per page."""
from __future__ import annotations

import io

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

TOP = 790
LEFT = 60
LEADING = 18
TITLE_FONT = ("Helvetica-Bold", 14)
BODY_FONT = ("Helvetica", 10.5)


def agreement_pdf(title: str, pages: tuple[tuple[str, ...], ...]) -> bytes:
    """The pages as an A4 PDF; each page's first line is set as its heading."""
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(title)
    for number, lines in enumerate(pages, start=1):
        y = TOP
        for index, line in enumerate(lines):
            font = TITLE_FONT if index == 0 else BODY_FONT
            pdf.setFont(*font)
            pdf.drawString(LEFT, y, line)
            y -= LEADING
        pdf.setFont(*BODY_FONT)
        pdf.drawString(LEFT, 40, f"Page {number} of {len(pages)}")
        pdf.showPage()
    pdf.save()
    return buffer.getvalue()
