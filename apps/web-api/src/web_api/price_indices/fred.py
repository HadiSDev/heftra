"""Downloading a series' CSV from FRED, which needs no API key."""
from __future__ import annotations

import httpx

from .. import config


class SeriesDownloadError(RuntimeError):
    """FRED could not be reached or refused the series."""


def download_series_csv(series: str) -> str:
    try:
        response = httpx.get(
            config.PRICE_INDEX_CSV_URL,
            params={"id": series},
            timeout=config.PRICE_INDEX_HTTP_TIMEOUT_SECONDS,
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise SeriesDownloadError(f"downloading {series}: {error}") from error
    return response.text
