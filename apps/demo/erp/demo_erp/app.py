"""The ERP document endpoint the web API's mock connector calls."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Response

from . import invoices, registration
from .render import invoice_pdf

logger = logging.getLogger("demo_erp")


@asynccontextmanager
async def lifespan(_: FastAPI):
    count = registration.register()
    logger.warning("registered with %d ERP integration(s)", count)
    yield


app = FastAPI(title="Heftra demo ERP", lifespan=lifespan)


@lru_cache(maxsize=512)
def _document(voucher_id: str) -> tuple[bytes, str] | None:
    invoice = invoices.find(voucher_id)
    if invoice is None:
        return None
    return invoice_pdf(invoice), f"{invoice.number}.pdf"


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/documents/{voucher_id}")
def document(voucher_id: str) -> Response:
    found = _document(voucher_id)
    if found is None:
        raise HTTPException(status_code=404, detail="No document for this voucher")
    content, filename = found
    return Response(
        content=content, media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
