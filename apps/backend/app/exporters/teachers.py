from __future__ import annotations

from openpyxl import Workbook

from app.core.config import Settings
from app.utils.parsers import make_timestamped_filename, relative_to_project


def export_teachers(settings: Settings, rows: list[dict[str, object]]) -> str:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "教师列表"
    headers = [
        "工号",
        "姓名",
        "性别",
        "学科",
        "联系方式",
        "职称",
        "岗位",
        "是否班主任",
        "任教状态",
        "入职日期",
        "备注",
    ]
    sheet.append(headers)
    for row in rows:
        sheet.append(
            [
                row.get("teacher_no"),
                row.get("name"),
                row.get("gender"),
                row.get("subject_name"),
                row.get("phone"),
                row.get("title_code"),
                row.get("position_code"),
                "是" if row.get("is_head_teacher") else "否",
                row.get("employment_status"),
                row.get("entry_date"),
                row.get("note"),
            ]
        )

    filename = make_timestamped_filename("teachers_export", ".xlsx")
    path = settings.exports_dir / filename
    workbook.save(path)
    return relative_to_project(path, settings.project_root)

