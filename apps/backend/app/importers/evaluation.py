from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import Any

from app.importers.base import read_template_rows


EXPECTED_HEADERS = ["模板名称", "教师", "班级", "题目", "分值", "评价对象类型"]


def read_evaluation_rows(filename: str | None, content: bytes) -> tuple[list[str], list[tuple[int, dict[str, Any]]]]:
    suffix = Path(filename or "").suffix.lower()
    if suffix == ".csv":
        return _read_csv_rows(content)
    return read_template_rows(content)


def _read_csv_rows(content: bytes) -> tuple[list[str], list[tuple[int, dict[str, Any]]]]:
    buffer = StringIO(content.decode("utf-8-sig"))
    reader = csv.DictReader(buffer)
    headers = [header.strip() for header in (reader.fieldnames or [])]
    rows: list[tuple[int, dict[str, Any]]] = []
    for row_number, raw in enumerate(reader, start=2):
        row = {str(key).strip(): value for key, value in raw.items() if key is not None}
        if not any(value not in (None, "") for value in row.values()):
            continue
        rows.append((row_number, row))
    return headers, rows
