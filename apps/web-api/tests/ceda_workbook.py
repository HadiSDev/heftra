"""A small workbook laid out as an Open CEDA 2025 release, for the import's tests."""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

SECTORS = [
    ("518200", "Data processing, hosting, and related services", "Hosting and data centres."),
    (541511, "Custom computer programming services", "Writing software to order."),
]
COUNTRIES = [
    ("DNK", "Denmark", ["0.1", "0.05"]),
    ("DEU", "Germany", ["0.2", "0.06"]),
    ("ROW", "Rest of World", ["0.3", "0.07"]),
]
REGIONS = [
    ("Northern Europe", ["0.11", "0.051"]),
    ("Carribean", ["0.4", "0.08"]),
]
RATIOS = ["0.8", "0.5"]
MAPPING = [("DNK", "Northern Europe"), ("TWN", "Eastern Asia"), ("CUB", "Caribbean")]


def write_workbook(path: Path, *, leave_out: str | None = None,
                   countries: list | None = None) -> Path:
    workbook = Workbook()
    workbook.remove(workbook.active)
    sheets = {
        "Cover": _cover,
        "GHG_t_Raw": lambda sheet: _factors(sheet, countries or COUNTRIES),
        "Regional Average EFs": _regions,
        "Purchaser - producer conversion": _ratios,
        "Country to region mapping": _mapping,
        "Metadata": _metadata,
    }
    for name, fill in sheets.items():
        if name != leave_out:
            fill(workbook.create_sheet(name))
    workbook.save(path)
    return path


def _cover(sheet) -> None:
    sheet.append([None, None, None, None, None, None, "Year", "2025"])
    sheet.append([None, "Version", None, "CEDA 2025", None, None, "Price type", "Producer price"])


def _factors(sheet, countries) -> None:
    sheet.append(["Year", "2023"])
    sheet.append(["Price type", "Producer price", "Currency", "US Dollar"])
    sheet.append([None, None, None] + [name for _, name, _ in SECTORS])
    sheet.append(["Country Code", "Country", "country"] + [code for code, _, _ in SECTORS])
    for code, name, values in countries:
        sheet.append([code, name, "kgCO2e/US Dollar"] + values)


def _regions(sheet) -> None:
    sheet.append(["Year", "2023"])
    sheet.append(["Price type", "Producer price", "Currency", "USD"])
    sheet.append([None, None] + [name for _, name, _ in SECTORS])
    sheet.append(["Region", "Unit"] + [code for code, _, _ in SECTORS])
    for region, values in REGIONS:
        sheet.append([region, "kgCO2e/US Dollar"] + values)


def _ratios(sheet) -> None:
    sheet.append(["Purchaser - Producer conversion"])
    sheet.append(["Source", "U.S. Bureau of Economic Analysis (BEA)"])
    sheet.append([])
    sheet.append(["Sector Name"] + [name for _, name, _ in SECTORS])
    sheet.append(["Sector Code"] + [code for code, _, _ in SECTORS])
    sheet.append(["Purchaser - Producer conversion"] + RATIOS)


def _mapping(sheet) -> None:
    sheet.append(["Country Code", "UN Subregion"])
    for row in MAPPING:
        sheet.append(list(row))


def _metadata(sheet) -> None:
    sheet.append(["Sector Code", "Sector Name", "Industry sector descriptions"])
    for row in SECTORS:
        sheet.append(list(row))
