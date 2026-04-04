from __future__ import annotations

from openpyxl import Workbook

from app.core.config import Settings
from app.utils.parsers import make_timestamped_filename, relative_to_project


def export_growth_summary(
    settings: Settings,
    student_meta: dict[str, object],
    records: list[dict[str, object]],
) -> str:
    workbook = Workbook()
    summary_sheet = workbook.active
    summary_sheet.title = "学生概况"
    summary_sheet.append(["学号", student_meta.get("student_no")])
    summary_sheet.append(["姓名", student_meta.get("student_name")])
    summary_sheet.append(["当前年级", student_meta.get("grade_name")])
    summary_sheet.append(["当前班级", student_meta.get("class_name")])
    summary_sheet.append(["记录数量", len(records)])

    detail_sheet = workbook.create_sheet("成长记录")
    detail_sheet.append(["日期", "类型", "标题", "内容", "责任人", "备注", "附件数"])
    for record in records:
        detail_sheet.append(
            [
                record.get("occurred_on"),
                record.get("record_type"),
                record.get("title"),
                record.get("content"),
                record.get("owner_name"),
                record.get("note"),
                len(record.get("attachments", [])),
            ]
        )

    filename = make_timestamped_filename("growth_summary_report", ".xlsx")
    path = settings.exports_dir / filename
    workbook.save(path)
    return relative_to_project(path, settings.project_root)

