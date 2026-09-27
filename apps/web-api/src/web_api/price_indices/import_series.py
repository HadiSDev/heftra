"""Import a price index: `python -m web_api.price_indices.import_series --series CPIAUCSL`."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from sqlmodel import Session

from ..db.session import engine
from .csv_file import SeriesFileError
from .fred import FRED_SOURCE, SeriesDownloadError, download_series_csv
from .refresh import store_series

logger = logging.getLogger("web_api.price_indices.import_series")

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import a monthly price index series.")
    parser.add_argument("--series", required=True, help="the series id, e.g. CPIAUCSL")
    parser.add_argument("--file", type=Path,
                        help="a downloaded CSV of the series; without it, FRED is read")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    try:
        text, source = _read(args.series, args.file)
        with Session(engine) as session:
            stored = store_series(session, args.series, text, source)
            session.commit()
    except (OSError, SeriesDownloadError, SeriesFileError) as error:
        logger.error("Nothing was imported: %s", error)
        return 1

    logger.info("%s: %d months, latest %s", args.series, stored.months,
                stored.latest_month.strftime("%B %Y"))
    return 0


def _read(series: str, file: Path | None) -> tuple[str, str]:
    if file is None:
        return download_series_csv(series), FRED_SOURCE
    return file.read_text(encoding="utf-8"), file.name


if __name__ == "__main__":
    sys.exit(main())
