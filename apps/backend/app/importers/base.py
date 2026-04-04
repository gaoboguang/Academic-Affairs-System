from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook

from app.core.config import Settings
from app.utils.parsers import make_timestamped_filename, relative_to_project


@dataclass
class RowError:
    row_number: int
    values: dict[str, Any]
    message: str


def read_template_rows(content: bytes) -> tuple[list[str], list[tuple[int, dict[str, Any]]]]:
    workbook = load_workbook(filename=BytesIO(content), data_only=True)
    worksheet = workbook["数据"] if "数据" in workbook.sheetnames else workbook.active

    header_row = next(worksheet.iter_rows(min_row=1, max_row=1, values_only=True), None)
    headers = [str(cell).strip() if cell is not None else "" for cell in (header_row or [])]

    rows: list[tuple[int, dict[str, Any]]] = []
    for row_number, values in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
        row_map = {headers[index]: value for index, value in enumerate(values)}
        if not any(value not in (None, "") for value in row_map.values()):
            continue
        rows.append((row_number, row_map))
    return headers, rows


def save_error_report(
    *,
    settings: Settings,
    prefix: str,
    headers: list[str],
    errors: list[RowError],
) -> str | None:
    if not errors:
        return None

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "错误报告"
    sheet.append(["行号", "错误原因", *headers])
    for error in errors:
        row = [error.row_number, error.message]
        for header in headers:
            row.append(error.values.get(header))
        sheet.append(row)

    filename = make_timestamped_filename(prefix, ".xlsx")
    path = settings.logs_dir / filename
    workbook.save(path)
    return relative_to_project(path, settings.project_root)

