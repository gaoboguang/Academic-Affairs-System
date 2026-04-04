from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from app.core.config import Settings
from app.utils.parsers import make_timestamped_filename, relative_to_project


def export_students(settings: Settings, rows: list[dict[str, object]]) -> str:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "学生列表"
    headers = [
        "学号",
        "姓名",
        "性别",
        "年级",
        "班级",
        "学生状态",
        "学生类别",
        "艺体方向",
        "联系电话",
        "家庭住址",
        "备注",
    ]
    sheet.append(headers)
    for row in rows:
        sheet.append(
            [
                row.get("student_no"),
                row.get("name"),
                row.get("gender"),
                row.get("current_grade_name"),
                row.get("current_class_name"),
                row.get("status"),
                row.get("student_type"),
                row.get("art_track"),
                row.get("phone"),
                row.get("address"),
                row.get("note"),
            ]
        )

    filename = make_timestamped_filename("students_export", ".xlsx")
    path = settings.exports_dir / filename
    workbook.save(path)
    return relative_to_project(path, settings.project_root)

