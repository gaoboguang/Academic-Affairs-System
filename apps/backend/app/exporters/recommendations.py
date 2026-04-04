from __future__ import annotations

from openpyxl import Workbook

from app.core.config import Settings
from app.utils.parsers import make_timestamped_filename, relative_to_project


def export_recommendation_summary(settings: Settings, meta: dict[str, object], rows: list[dict[str, object]]) -> str:
    workbook = Workbook()
    summary = workbook.active
    summary.title = "推荐概况"
    summary.append(["推荐方案", meta.get("scheme_name")])
    summary.append(["学生", meta.get("student_name")])
    summary.append(["考试", meta.get("exam_name")])
    summary.append(["省份", meta.get("province")])
    summary.append(["结果数量", len(rows)])

    detail = workbook.create_sheet("推荐结果")
    detail.append(["分组", "院校", "专业", "参考位次", "学生位次", "比值", "依据", "理由", "风险提示"])
    for row in rows:
        detail.append(
            [
                row.get("result_type"),
                row.get("college_name"),
                row.get("major_name"),
                row.get("reference_rank"),
                row.get("student_rank"),
                row.get("ratio"),
                row.get("score_basis"),
                row.get("reason_text"),
                ",".join(row.get("risk_flags_json") or []),
            ]
        )

    filename = make_timestamped_filename("recommendation_summary_report", ".xlsx")
    path = settings.exports_dir / filename
    workbook.save(path)
    return relative_to_project(path, settings.project_root)
