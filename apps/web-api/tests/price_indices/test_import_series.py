"""The import CLI replaces a series from FRED or a file, or changes nothing."""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from web_api.db.models import PriceIndexValue
from web_api.price_indices import import_series
from web_api.price_indices.fred import SeriesDownloadError

FRED_CSV = """observation_date,CPIAUCSL
2026-07-01,332.813
2026-08-01,334.131
"""


@pytest.fixture
def cli(engine, monkeypatch):
    monkeypatch.setattr(import_series, "engine", engine)
    return import_series.main


def _stored(engine) -> dict[date, Decimal]:
    with Session(engine) as session:
        rows = session.exec(select(PriceIndexValue).where(PriceIndexValue.series == "CPIAUCSL"))
        return {row.month: row.value for row in rows}


def test_a_series_is_imported_from_fred(cli, engine, monkeypatch, caplog):
    monkeypatch.setattr(import_series, "download_series_csv", lambda series: FRED_CSV)
    caplog.set_level(logging.INFO)

    assert cli(["--series", "CPIAUCSL"]) == 0

    assert _stored(engine) == {date(2026, 7, 1): Decimal("332.813"),
                               date(2026, 8, 1): Decimal("334.131")}
    assert "CPIAUCSL: 2 months, latest August 2026" in caplog.text


def test_a_reimport_replaces_the_series(cli, engine, tmp_path):
    first = tmp_path / "first.csv"
    first.write_text("observation_date,CPIAUCSL\n2026-03-01,330\n2026-04-01,331\n")
    revised = tmp_path / "revised.csv"
    revised.write_text("observation_date,CPIAUCSL\n2026-03-01,330.293\n")

    assert cli(["--series", "CPIAUCSL", "--file", str(first)]) == 0
    assert cli(["--series", "CPIAUCSL", "--file", str(revised)]) == 0

    assert _stored(engine) == {date(2026, 3, 1): Decimal("330.293")}


def test_a_malformed_file_changes_nothing(cli, engine, tmp_path, caplog):
    good = tmp_path / "good.csv"
    good.write_text(FRED_CSV)
    bad = tmp_path / "bad.csv"
    bad.write_text("observation_date,PCEPI\n2026-08-01,126\n")

    assert cli(["--series", "CPIAUCSL", "--file", str(good)]) == 0
    assert cli(["--series", "CPIAUCSL", "--file", str(bad)]) == 1

    assert len(_stored(engine)) == 2
    assert "no CPIAUCSL column" in caplog.text


def test_a_failed_download_changes_nothing(cli, engine, monkeypatch, caplog):
    def unreachable(series):
        raise SeriesDownloadError("downloading CPIAUCSL: timed out")

    monkeypatch.setattr(import_series, "download_series_csv", unreachable)

    assert cli(["--series", "CPIAUCSL"]) == 1

    assert _stored(engine) == {}
    assert "timed out" in caplog.text
