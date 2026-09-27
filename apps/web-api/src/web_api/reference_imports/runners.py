"""Running an import job to the end in its own session, whatever happens."""
from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.engine import Engine
from sqlmodel import Session

from ..db.models import ReferenceDataImport
from ..emissions.ceda.types import WorkbookError
from ..emissions.ceda.workbook import read_workbook
from ..emissions.factor_import import import_workbook
from ..price_indices.csv_file import SeriesFileError
from ..price_indices.fred import FRED_SOURCE, SeriesDownloadError, download_series_csv
from ..price_indices.refresh import store_series
from .jobs import mark_failed, mark_running, mark_succeeded

logger = logging.getLogger(__name__)


def run_workbook_job(engine: Engine, job_id: str, path: Path) -> None:
    """Import the workbook at `path`, activating it if asked; the file is deleted either way."""
    try:
        with Session(engine) as session:
            job = session.get(ReferenceDataImport, job_id)
            if job is None:
                return
            mark_running(session, job)
            try:
                counts = import_workbook(session, read_workbook(path), activate=job.activate,
                                         actor=job.requested_by)
                session.commit()
            except (WorkbookError, OSError) as error:
                session.rollback()
                mark_failed(session, job, str(error))
                return
            except Exception as error:
                session.rollback()
                logger.exception("Workbook import %s failed", job_id)
                mark_failed(session, job, f"Unexpected error: {error}")
                return
            mark_succeeded(session, job, {
                "version": counts.version,
                "sectors": counts.sectors,
                "countries": counts.countries,
                "regions": counts.regions,
                "factors": counts.factors,
                "skipped_countries": counts.skipped_countries,
                "active": counts.active,
            })
    finally:
        path.unlink(missing_ok=True)


def run_price_index_job(engine: Engine, job_id: str) -> None:
    """Download the job's series from FRED and replace its stored values."""
    with Session(engine) as session:
        job = session.get(ReferenceDataImport, job_id)
        if job is None:
            return
        mark_running(session, job)
        try:
            stored = store_series(session, job.subject, download_series_csv(job.subject),
                                  FRED_SOURCE)
            session.commit()
        except (SeriesDownloadError, SeriesFileError) as error:
            session.rollback()
            mark_failed(session, job, str(error))
            return
        except Exception as error:
            session.rollback()
            logger.exception("Price index refresh %s failed", job_id)
            mark_failed(session, job, f"Unexpected error: {error}")
            return
        mark_succeeded(session, job, {"months": stored.months,
                                      "latest_month": stored.latest_month.isoformat()})
