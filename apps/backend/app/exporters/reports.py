from __future__ import annotations

from openpyxl import Workbook

from app.core.config import Settings
from app.utils.parsers import make_timestamped_filename, relative_to_project


def _save_workbook(settings: Settings, workbook: Workbook, prefix: str) -> str:
    filename = make_timestamped_filename(prefix, ".xlsx")
    path = settings.exports_dir / filename
    workbook.save(path)
    return relative_to_project(path, settings.project_root)


def export_student_analysis_report(settings: Settings, payload: dict[str, object]) -> str:
    workbook = Workbook()
    summary = workbook.active
    summary.title = "学生分析"
    summary.append(["考试", payload.get("exam_name")])
    summary.append(["学生", payload.get("student_name")])
    summary.append(["总分", payload.get("total_score")])
    summary.append(["班名", payload.get("class_rank")])
    summary.append(["年名", payload.get("grade_rank")])
    summary.append(["上次考试", payload.get("previous_exam_name")])
    summary.append(["总分变化", payload.get("total_score_delta")])

    detail = workbook.create_sheet("学科明细")
    detail.append(["科目", "分数", "班名", "年名", "班百分位", "年百分位", "分数变化", "名次变化"])
    for row in payload.get("subjects", []):
        detail.append(
            [
                row.get("subject_name"),
                row.get("score"),
                row.get("class_rank"),
                row.get("grade_rank"),
                row.get("class_percentile"),
                row.get("grade_percentile"),
                row.get("score_delta"),
                row.get("rank_delta"),
            ]
        )
    return _save_workbook(settings, workbook, "student_analysis_report")


def export_class_analysis_report(settings: Settings, payload: dict[str, object]) -> str:
    workbook = Workbook()
    summary = workbook.active
    summary.title = "班级分析"
    summary.append(["考试", payload.get("exam_name")])
    summary.append(["班级", payload.get("class_name")])
    summary.append(["学生数", payload.get("student_count")])
    summary.append(["总分均分", payload.get("total_average")])
    summary.append(["总分中位数", payload.get("total_median")])
    summary.append(["年级均分", payload.get("grade_average")])

    detail = workbook.create_sheet("学科统计")
    detail.append(["科目", "均分", "中位数", "最高分", "最低分", "标准差", "优秀率", "及格率", "有效人数"])
    for row in payload.get("subject_breakdown", []):
        detail.append(
            [
                row.get("subject_name"),
                row.get("average_score"),
                row.get("median_score"),
                row.get("max_score"),
                row.get("min_score"),
                row.get("standard_deviation"),
                row.get("excellent_rate"),
                row.get("pass_rate"),
                row.get("valid_count"),
            ]
        )
    return _save_workbook(settings, workbook, "class_analysis_report")


def export_grade_summary_report(
    settings: Settings,
    summary_rows: list[dict[str, object]],
    subject_rows: list[dict[str, object]],
    title: str,
) -> str:
    workbook = Workbook()
    summary = workbook.active
    summary.title = "班级汇总"
    summary.append(["班级", "人数", "总分均分", "总分中位数", "最高分", "最低分"])
    for row in summary_rows:
        summary.append(
            [
                row.get("class_name"),
                row.get("student_count"),
                row.get("average_score"),
                row.get("median_score"),
                row.get("max_score"),
                row.get("min_score"),
            ]
        )

    detail = workbook.create_sheet("学科汇总")
    detail.append(["科目", "有效人数", "均分", "优秀率", "及格率"])
    for row in subject_rows:
        detail.append(
            [
                row.get("subject_name"),
                row.get("valid_count"),
                row.get("average_score"),
                row.get("excellent_rate"),
                row.get("pass_rate"),
            ]
        )
    workbook.properties.title = title
    return _save_workbook(settings, workbook, "grade_summary_report")


def export_teacher_analysis_report(settings: Settings, payload: dict[str, object]) -> str:
    workbook = Workbook()
    summary = workbook.active
    summary.title = "教师分析"
    summary.append(["考试", payload.get("exam_name")])
    summary.append(["教师", payload.get("teacher_name")])
    summary.append(["整体均分", payload.get("overall_average")])

    detail = workbook.create_sheet("任教明细")
    detail.append(["班级", "学科", "均分", "优秀率", "及格率", "有效人数"])
    for row in payload.get("assignment_breakdown", []):
        detail.append(
            [
                row.get("class_name"),
                row.get("subject_name"),
                row.get("average_score"),
                row.get("excellent_rate"),
                row.get("pass_rate"),
                row.get("valid_count"),
            ]
        )
    return _save_workbook(settings, workbook, "teacher_analysis_report")


def export_evaluation_summary_report(
    settings: Settings,
    meta: dict[str, object],
    teacher_rows: list[dict[str, object]],
    detail_rows: list[dict[str, object]],
) -> str:
    workbook = Workbook()
    summary = workbook.active
    summary.title = "评教汇总"
    summary.append(["模板", meta.get("template_name")])
    summary.append(["学期", meta.get("semester_name")])
    summary.append(["教师数", len(teacher_rows)])

    teacher_sheet = workbook.create_sheet("教师总览")
    teacher_sheet.append(["教师", "综合得分", "有效条数", "名次", "维度得分"])
    for row in teacher_rows:
        dimension_scores = row.get("dimension_scores_json") or {}
        teacher_sheet.append(
            [
                row.get("teacher_name"),
                row.get("overall_avg_score"),
                row.get("response_count"),
                row.get("rank"),
                " / ".join(f"{key}:{value}" for key, value in dimension_scores.items()),
            ]
        )

    detail_sheet = workbook.create_sheet("维度明细")
    detail_sheet.append(["教师", "维度", "平均分", "样本数"])
    for row in detail_rows:
        detail_sheet.append(
            [
                row.get("teacher_name"),
                row.get("dimension_name"),
                row.get("avg_score"),
                row.get("response_count"),
            ]
        )
    return _save_workbook(settings, workbook, "evaluation_summary_report")


def export_adviser_quant_summary_report(
    settings: Settings,
    meta: dict[str, object],
    summary_rows: list[dict[str, object]],
    detail_rows: list[dict[str, object]],
) -> str:
    workbook = Workbook()
    summary = workbook.active
    summary.title = "量化汇总"
    summary.append(["学期", meta.get("semester_name")])
    summary.append(["规则版本", meta.get("rule_version_name")])
    summary.append(["教师数", len(summary_rows)])

    teacher_sheet = workbook.create_sheet("教师汇总")
    teacher_sheet.append(["教师", "总分", "加分", "扣分", "记录数", "班级", "分类汇总"])
    for row in summary_rows:
        category_scores = row.get("category_scores_json") or {}
        teacher_sheet.append(
            [
                row.get("teacher_name"),
                row.get("total_score"),
                row.get("positive_score"),
                row.get("negative_score"),
                row.get("record_count"),
                " / ".join(row.get("class_names") or []),
                " / ".join(f"{key}:{value}" for key, value in category_scores.items()),
            ]
        )

    detail_sheet = workbook.create_sheet("量化明细")
    detail_sheet.append(["教师", "班级", "月份", "量化项", "类型", "得分", "说明"])
    for row in detail_rows:
        detail_sheet.append(
            [
                row.get("teacher_name"),
                row.get("class_name"),
                row.get("record_month"),
                row.get("item_name"),
                row.get("item_type"),
                row.get("score"),
                row.get("description"),
            ]
        )
    return _save_workbook(settings, workbook, "adviser_quant_summary_report")
