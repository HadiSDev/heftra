"""Finding things in a worksheet by their labels rather than their positions."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from openpyxl.workbook.workbook import Workbook

from .types import WorkbookError

Row = tuple[Any, ...]


def sheet_rows(workbook: Workbook, name: str) -> list[Row]:
    """Every row of the named sheet, as values."""
    if name not in workbook.sheetnames:
        raise WorkbookError(f"the workbook has no sheet named {name!r}")
    return list(workbook[name].iter_rows(values_only=True))


def text(value: Any) -> str:
    """A cell as trimmed text; a code stored as a number reads as its digits."""
    if value is None:
        return ""
    return str(value).strip()


def labelled_value(rows: list[Row], label: str, sheet: str) -> str:
    """The first non-empty cell to the right of the first cell reading `label`."""
    for row in rows:
        cells = [text(cell) for cell in row]
        if label not in cells:
            continue
        for cell in cells[cells.index(label) + 1:]:
            if cell:
                return cell
    raise WorkbookError(f"sheet {sheet!r} has no value labelled {label!r}")


def header_index(rows: list[Row], first_label: str, sheet: str, *, after: int = -1) -> int:
    """The index of the first row after `after` whose first cell reads `first_label`."""
    for index, row in enumerate(rows):
        if index > after and row and text(row[0]) == first_label:
            return index
    raise WorkbookError(f"sheet {sheet!r} has no row headed {first_label!r}")


def decimal(value: Any, where: str) -> Decimal:
    try:
        return Decimal(text(value))
    except InvalidOperation as error:
        raise WorkbookError(f"{where} is not a number: {value!r}") from error
