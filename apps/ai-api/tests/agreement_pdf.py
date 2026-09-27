"""Small agreement PDFs for tests: one list of lines per page, an empty list for a blank page."""
from __future__ import annotations

import io

from reportlab.pdfgen import canvas


def agreement_pdf(pages: list[list[str]]) -> bytes:
    buf = io.BytesIO()
    pdf = canvas.Canvas(buf)
    for lines in pages:
        y = 800
        for line in lines:
            pdf.drawString(50, y, line)
            y -= 16
        pdf.showPage()
    pdf.save()
    return buf.getvalue()


FRAMEWORK = [
    ["Framework agreement FA-2026-17", "between Acme ApS and Atea A/S (CVR DK12345678)",
     "Valid from 2026-01-01 to 2027-12-31. Prices in DKK."],
    ["3. Purchasing", "IT equipment shall be purchased from Atea when available from stock."],
    ["7. Prices", "Lenovo ThinkPad T14 Gen 5: DKK 8.000,00 per unit.",
     "Accessories carry a discount of 10 percent off list price."],
]
