"""System-admin controls for emission factors: status, activation, CPI refresh, workbook upload."""
from __future__ import annotations

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlmodel import Session, col, select

from .. import config
from ..admin.factor_sets import counted_factor_set
from ..admin.status import emission_factors_status
from ..auth.deps import TenantScope, get_session, require_system_admin
from ..db.models import EmissionFactorSet, ReferenceDataImport, ReferenceImportKind, User
from ..emissions.activation import activate_factor_set
from ..price_indices.series import index_for_currency
from ..reference_imports.jobs import ImportInProgress, ensure_idle, recent_jobs, request_job
from ..reference_imports.runners import run_price_index_job, run_workbook_job
from ..reference_imports.uploads import NotAWorkbook, UploadTooLarge, save_workbook
from ..schemas.admin import (
    EmissionFactorsStatusRead,
    FactorSetActivationRead,
    PriceIndexRefresh,
    ReferenceImportRead,
)

router = APIRouter(prefix="/api/v1/admin/emission-factors", tags=["admin"],
                   dependencies=[Depends(require_system_admin)])


@router.get("", response_model=EmissionFactorsStatusRead)
def get_status(session: Session = Depends(get_session)) -> EmissionFactorsStatusRead:
    """The factor sets, their price indices, and each company's sector coverage."""
    return emission_factors_status(session)


@router.post("/sets/{factor_set_id}/activate", response_model=FactorSetActivationRead)
def activate(
    factor_set_id: str,
    scope: TenantScope = Depends(require_system_admin),
    session: Session = Depends(get_session),
) -> FactorSetActivationRead:
    """Make this set the one every estimate uses."""
    factor_set = session.get(EmissionFactorSet, factor_set_id)
    if factor_set is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Factor set not found")
    activation = activate_factor_set(session, factor_set, actor=scope.user_id)
    session.commit()
    session.refresh(factor_set)
    return FactorSetActivationRead(
        factor_set=counted_factor_set(session, factor_set),
        previous_version=activation.previous.version if activation.previous else None,
        rematch_needed=activation.rematch_needed,
    )


@router.post("/price-index/refresh", response_model=ReferenceImportRead,
             status_code=status.HTTP_202_ACCEPTED)
def refresh_price_index(
    body: PriceIndexRefresh,
    background: BackgroundTasks,
    scope: TenantScope = Depends(require_system_admin),
    session: Session = Depends(get_session),
) -> ReferenceImportRead:
    """Download the series from FRED in the background and replace its values."""
    if body.series not in _mapped_series(session):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail=f"No factor set is deflated with {body.series}")
    job = _request(session, ReferenceImportKind.PRICE_INDEX, body.series, scope)
    background.add_task(run_price_index_job, session.get_bind(), job.id)
    return _job_read(session, job)


@router.post("/workbooks", response_model=ReferenceImportRead,
             status_code=status.HTTP_202_ACCEPTED)
def upload_workbook(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    activate: bool = Form(False),
    scope: TenantScope = Depends(require_system_admin),
    session: Session = Depends(get_session),
) -> ReferenceImportRead:
    """Save an Open CEDA workbook and import it in the background."""
    filename = file.filename or "workbook.xlsx"
    _refuse_if_busy(session, ReferenceImportKind.FACTOR_WORKBOOK)
    try:
        path = save_workbook(filename, file.file, max_bytes=config.EMISSION_WORKBOOK_MAX_BYTES,
                             directory=config.UPLOAD_TMP_DIR)
    except UploadTooLarge as error:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                            detail=str(error)) from error
    except NotAWorkbook as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail=str(error)) from error
    try:
        job = _request(session, ReferenceImportKind.FACTOR_WORKBOOK, filename, scope,
                       activate=activate)
    except HTTPException:
        path.unlink(missing_ok=True)
        raise
    background.add_task(run_workbook_job, session.get_bind(), job.id, path)
    return _job_read(session, job)


@router.get("/imports", response_model=list[ReferenceImportRead])
def list_imports(
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
) -> list[ReferenceImportRead]:
    """The most recent uploads and refreshes, newest first."""
    jobs = recent_jobs(session, limit)
    names = _user_names(session, {job.requested_by for job in jobs})
    return [_as_read(job, names) for job in jobs]


def _request(session: Session, kind: ReferenceImportKind, subject: str, scope: TenantScope, *,
             activate: bool = False) -> ReferenceDataImport:
    try:
        return request_job(session, kind, subject, requested_by=scope.user_id, activate=activate)
    except ImportInProgress as error:
        raise _busy() from error


def _refuse_if_busy(session: Session, kind: ReferenceImportKind) -> None:
    """Refuse before saving an upload that couldn't be queued anyway."""
    try:
        ensure_idle(session, kind)
    except ImportInProgress as error:
        raise _busy() from error


def _busy() -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT,
                         detail="An import of this kind is already queued or running")


def _mapped_series(session: Session) -> set[str]:
    currencies = session.exec(select(EmissionFactorSet.currency).distinct()).all()
    return {series.id for currency in currencies
            if (series := index_for_currency(currency)) is not None}


def _job_read(session: Session, job: ReferenceDataImport) -> ReferenceImportRead:
    return _as_read(job, _user_names(session, {job.requested_by}))


def _as_read(job: ReferenceDataImport, names: dict[str, str]) -> ReferenceImportRead:
    return ReferenceImportRead.model_validate(job).model_copy(
        update={"requested_by_name": names.get(job.requested_by)}
    )


def _user_names(session: Session, user_ids: set[str]) -> dict[str, str]:
    if not user_ids:
        return {}
    return dict(session.exec(
        select(User.id, User.name).where(col(User.id).in_(user_ids))
    ).all())
