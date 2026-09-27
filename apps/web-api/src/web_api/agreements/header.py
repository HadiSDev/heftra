"""A person correcting an agreement's supplier, title, reference, dates or currency."""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session

from ..audit import diff_changes, record_audit
from ..db.models import Agreement, AgreementStatus, Vendor
from ..schemas.agreements import AgreementPatch
from .analysis import request_analysis
from .constants import AUDIT_AGREEMENT
from .status import settle_status

HEADER_FIELDS = ("vendor_id", "title", "reference", "starts_on", "ends_on", "currency")


def patch_header(session: Session, agreement: Agreement, body: AgreementPatch,
                 actor: str) -> Agreement:
    before = {field: getattr(agreement, field) for field in HEADER_FIELDS}
    sent = body.model_fields_set
    if "vendor_id" in sent and body.vendor_id is not None \
            and session.get(Vendor, body.vendor_id) is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail="No such supplier")
    for field in sent:
        value = getattr(body, field)
        if field == "currency" and value is not None:
            value = value.upper()
        setattr(agreement, field, value)
    if agreement.starts_on and agreement.ends_on and agreement.ends_on < agreement.starts_on:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail="The agreement cannot end before it starts.")
    session.add(agreement)
    changes = diff_changes(before, {field: getattr(agreement, field) for field in HEADER_FIELDS},
                           HEADER_FIELDS)
    if not changes:
        return agreement
    record_audit(session, entity_type=AUDIT_AGREEMENT, entity_id=agreement.id, action="update",
                 actor=actor, changes=changes)
    settle_status(session, agreement)
    if agreement.status == AgreementStatus.ACTIVE.value:
        request_analysis(session, agreement.company_id, actor)
    return agreement
