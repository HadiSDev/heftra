"""Import an Open CEDA workbook: `python -m web_api.emissions.import_factors --file <xlsx>`."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from sqlmodel import Session

from ..db.session import engine
from .ceda.types import WorkbookError
from .ceda.workbook import read_workbook
from .factor_import import import_workbook

logger = logging.getLogger("web_api.emissions.import_factors")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import an Open CEDA emission factor workbook.")
    parser.add_argument("--file", required=True, type=Path, help="the Open CEDA .xlsx workbook")
    parser.add_argument("--activate", action="store_true",
                        help="make this release the one estimates use")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if not args.file.is_file():
        logger.error("No such file: %s", args.file)
        return 1
    try:
        workbook = read_workbook(args.file)
    except WorkbookError as error:
        logger.error("Not an Open CEDA workbook: %s", error)
        return 1

    with Session(engine) as session:
        try:
            counts = import_workbook(session, workbook, activate=args.activate)
            session.commit()
        except WorkbookError as error:
            session.rollback()
            logger.error("Import failed, nothing was written: %s", error)
            return 1

    logger.info(
        "%s: %d sectors, %d countries, %d regions, %d factors%s",
        counts.version, counts.sectors, counts.countries, counts.regions, counts.factors,
        " (active)" if counts.active else "",
    )
    if counts.skipped_countries:
        logger.warning("Skipped unknown country codes: %s", ", ".join(counts.skipped_countries))
    return 0


if __name__ == "__main__":
    sys.exit(main())
