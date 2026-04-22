from __future__ import annotations

from openpyxl import Workbook

from app.core.config import Settings
from app.utils.parsers import make_timestamped_filename, relative_to_project


def _append_analysis_insight_sheet(
    workbook: Workbook,
    rows: list[dict[str, object]],
) -> None:
    insight_sheet = workbook.create_sheet("摘要概览")
    insight_sheet.append(["标题", "摘要", "说明", "提示级别"])
    for row in rows:
        insight_sheet.append([
            row.get("title"),
            row.get("summary"),
            row.get("detail"),
            row.get("tone"),
        ])


def _format_number(value: object) -> str:
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value or "-")


def _pick_max_by(rows: list[dict[str, object]], key: str) -> dict[str, object] | None:
    valid_rows = [row for row in rows if isinstance(row.get(key), (int, float))]
    if not valid_rows:
        return None
    return max(valid_rows, key=lambda row: float(row.get(key) or 0))


def _build_workload_insight_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    if not rows:
        return []

    total_workload = sum(float(row.get("semester_workload") or 0) for row in rows if isinstance(row.get("semester_workload"), (int, float)))
    total_hours = sum(float(row.get("semester_hours") or 0) for row in rows if isinstance(row.get("semester_hours"), (int, float)))
    average_workload = total_workload / len(rows)
    max_teacher = _pick_max_by(rows, "semester_workload")
    focus_teacher = _pick_max_by(rows, "weekly_hours")

    insight_rows: list[dict[str, object]] = [
        {
            "title": "工作量整体状态",
            "summary": f"{rows[0].get('semester_name') or '当前学期'}共 {len(rows)} 位教师，总工作量 {_format_number(total_workload)}",
            "detail": f"总学期课时 {_format_number(total_hours)}，人均工作量 {_format_number(average_workload)}，规则版本 {rows[0].get('rule_version_name') or '未指定'}。",
            "tone": "info",
        }
    ]

    if max_teacher:
        insight_rows.append(
            {
                "title": "工作量最高教师",
                "summary": f"{max_teacher.get('teacher_name') or '未命名教师'} 当前学期工作量最高",
                "detail": f"学期工作量 {_format_number(max_teacher.get('semester_workload'))}，学期课时 {_format_number(max_teacher.get('semester_hours'))}，周课时 {_format_number(max_teacher.get('weekly_hours'))}。",
                "tone": "warning",
            }
        )

    if focus_teacher and focus_teacher.get("teacher_name") != (max_teacher or {}).get("teacher_name"):
        insight_rows.append(
            {
                "title": "周课时最高教师",
                "summary": f"{focus_teacher.get('teacher_name') or '未命名教师'} 当前周课时最高",
                "detail": f"周课时 {_format_number(focus_teacher.get('weekly_hours'))}，学期工作量 {_format_number(focus_teacher.get('semester_workload'))}。导出前建议确认是否存在需额外说明的工作量来源。",
                "tone": "info",
            }
        )

    return insight_rows


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
    _append_analysis_insight_sheet(workbook, _build_workload_insight_rows(rows))
    filename = make_timestamped_filename("teacher_workload_export", ".xlsx")
    path = settings.exports_dir / filename
    workbook.save(path)
    return relative_to_project(path, settings.project_root)
