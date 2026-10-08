"""Uploading, listing, correcting, reading again and deleting agreements, and their reports."""
from __future__ import annotations

from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlmodel import Session

from .. import config
from ..agreements.access import get_agreement
from ..agreements.analysis import request_analysis, request_full_analysis
from ..agreements.constants import AUDIT_AGREEMENT, PDF_MEDIA_TYPE
from ..agreements.deletion import delete_agreements
from ..agreements.header import patch_header
from ..agreements.reads import agreement_read, list_agreements
from ..agreements.stored_files import discard_files
from ..agreements.upload import AgreementTooLarge, NotAPdf, check_pdf, record_agreement
from ..audit import record_audit
from ..auth.deps import (
    TenantScope,
    get_managed_company,
    get_session,
    require_management,
    resolve_company_ids,
    tenant_scope,
)
from ..compliance.findings import FindingSort, SortOrder, default_order
from ..compliance.report import agreement_report
from ..db.models import (
    AgreementStatus,
    FindingKind,
    FindingReviewStatus,
    PipelineRun,
)
from ..db.models import File as FileRow
from ..schemas import PipelineRunRead
from ..schemas.agreements import (
    AgreementPatch,
    AgreementRead,
    AgreementReport,
    AgreementSummaryRead,
)
from ..storage.dependency import get_file_store
from ..storage.errors import StorageUnavailable, StoredFileMissing
from ..storage.store import FileStore

router = APIRouter(prefix="/api/v1", tags=["agreements"])


@router.post("/companies/{company_id}/agreements", response_model=AgreementRead,
             status_code=status.HTTP_201_CREATED)
async def upload_agreement(
    company_id: str,
    file: UploadFile = File(...),
    scope: TenantScope = Depends(require_management),
    session: Session = Depends(get_session),
    store: FileStore = Depends(get_file_store),
) -> AgreementRead:
    """Store an agreement PDF; the worker reads it next."""
    company = get_managed_company(session, scope, company_id)
    filename = file.filename or "agreement.pdf"
    data = await file.read(config.AGREEMENT_MAX_BYTES + 1)
    try:
        check_pdf(filename, data, config.AGREEMENT_MAX_BYTES)
    except NotAPdf as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail=str(error)) from error
    except AgreementTooLarge as error:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                            detail=str(error)) from error

    agreement, key = record_agreement(session, company.id, filename, len(data), scope.user_id)
    try:
        await store.put(key, data, PDF_MEDIA_TYPE)
    except StorageUnavailable as error:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="File storage is unavailable") from error
    session.commit()
    return agreement_read(session, agreement, date.today())


@router.get("/agreements", response_model=list[AgreementSummaryRead])
def get_agreements(
    company_id: str | None = Query(default=None),
    scope: TenantScope = Depends(tenant_scope),
    session: Session = Depends(get_session),
) -> list[AgreementSummaryRead]:
    """The agreements of the chosen company, or of every active one, newest first."""
    return list_agreements(session, resolve_company_ids(scope, company_id), date.today())


@router.get("/agreements/{agreement_id}", response_model=AgreementRead)
def get_agreement_detail(
    agreement_id: str,
    scope: TenantScope = Depends(tenant_scope),
    session: Session = Depends(get_session),
) -> AgreementRead:
    return agreement_read(session, get_agreement(session, scope, agreement_id), date.today())


@router.patch("/agreements/{agreement_id}", response_model=AgreementRead)
def update_agreement(
    agreement_id: str,
    body: AgreementPatch,
    scope: TenantScope = Depends(require_management),
    session: Session = Depends(get_session),
) -> AgreementRead:
    """Correct the supplier, title, reference, dates or currency."""
    agreement = get_agreement(session, scope, agreement_id)
    patch_header(session, agreement, body, scope.user_id)
    session.commit()
    return agreement_read(session, agreement, date.today())


@router.delete("/agreements/{agreement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_agreement(
    agreement_id: str,
    scope: TenantScope = Depends(require_management),
    session: Session = Depends(get_session),
    store: FileStore = Depends(get_file_store),
) -> Response:
    """Delete the agreement, its terms and findings, and its stored file."""
    agreement = get_agreement(session, scope, agreement_id)
    record_audit(session, entity_type=AUDIT_AGREEMENT, entity_id=agreement.id, action="delete",
                 actor=scope.user_id, changes=[{"field": "title", "old": agreement.title,
                                                "new": None}])
    keys = delete_agreements(session, [agreement.id])
    session.commit()
    await discard_files(store, keys)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/agreements/{agreement_id}/document")
async def get_agreement_document(
    agreement_id: str,
    scope: TenantScope = Depends(tenant_scope),
    session: Session = Depends(get_session),
    store: FileStore = Depends(get_file_store),
) -> Response:
    """The agreement's PDF, shown inline."""
    agreement = get_agreement(session, scope, agreement_id)
    file_row = session.get(FileRow, agreement.file_id)
    if file_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No document")
    try:
        content = await store.get(file_row.storage_path)
    except StoredFileMissing as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="The document is missing from storage") from error
    except StorageUnavailable as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="File storage is unavailable") from error
    return Response(content=content, media_type=PDF_MEDIA_TYPE,
                    headers={"Content-Disposition": f'inline; filename="{file_row.filename}"'})


@router.post("/agreements/{agreement_id}/read", response_model=AgreementRead)
def read_agreement_again(
    agreement_id: str,
    scope: TenantScope = Depends(require_management),
    session: Session = Depends(get_session),
) -> AgreementRead:
    """Queue the document to be read again; confirmed and rejected terms are kept."""
    agreement = get_agreement(session, scope, agreement_id)
    agreement.status = AgreementStatus.PENDING.value
    agreement.read_attempts = 0
    agreement.read_error = None
    agreement.read_started_at = None
    session.add(agreement)
    record_audit(session, entity_type=AUDIT_AGREEMENT, entity_id=agreement.id, action="read",
                 actor=scope.user_id, changes=[])
    session.commit()
    return agreement_read(session, agreement, date.today())


@router.post("/companies/{company_id}/agreements/analyse", response_model=PipelineRunRead,
             status_code=status.HTTP_202_ACCEPTED)
def analyse_company_agreements(
    company_id: str,
    full: bool = Query(default=False),
    scope: TenantScope = Depends(require_management),
    session: Session = Depends(get_session),
) -> PipelineRun:
    """Check the company's spend against its agreements again; `full` rechecks every line."""
    company = get_managed_company(session, scope, company_id)
    if full:
        run = request_full_analysis(session, company.id, scope.user_id)
    else:
        run = request_analysis(session, company.id, scope.user_id)
    session.commit()
    session.refresh(run)
    return run


@router.get("/agreements/{agreement_id}/report", response_model=AgreementReport)
def get_agreement_report(
    agreement_id: str,
    kind: list[FindingKind] | None = Query(default=None),
    review_status: list[FindingReviewStatus] | None = Query(default=None),
    sort: FindingSort = Query(default="severity"),
    order: SortOrder | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    scope: TenantScope = Depends(tenant_scope),
    session: Session = Depends(get_session),
) -> AgreementReport:
    """Totals, spend in scope, commitments, and the findings, rule breaks first unless sorted
    otherwise."""
    agreement = get_agreement(session, scope, agreement_id)
    return agreement_report(
        session, agreement, date.today(),
        kinds=[value.value for value in kind] if kind else None,
        review_statuses=[value.value for value in review_status] if review_status else None,
        sort=sort, order=order or default_order(sort),
        page=page, page_size=page_size,
    )
