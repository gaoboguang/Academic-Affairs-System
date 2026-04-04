from __future__ import annotations

from openpyxl import Workbook

from app.core.config import Settings
from app.utils.parsers import make_timestamped_filename, relative_to_project


def export_workload_results(settings: Settings, rows: list[dict[str, object]]) -> str:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "教师工作量"
    headers = ["教师", "学期", "规则版本", "周课时", "学期课时", "学期工作量", "计算时间"]
    sheet.append(headers)
    for row in rows:
        sheet.append(
            [
                row.get("teacher_name"),
                row.get("semester_name"),
                row.get("rule_version_name"),
                row.get("weekly_hours"),
                row.get("semester_hours"),
                row.get("semester_workload"),
                row.get("calculated_at"),
            ]
        )
    filename = make_timestamped_filename("teacher_workload_export", ".xlsx")
    path = settings.exports_dir / filename
    workbook.save(path)
    return relative_to_project(path, settings.project_root)

