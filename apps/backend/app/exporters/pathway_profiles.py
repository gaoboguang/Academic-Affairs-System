from __future__ import annotations

from openpyxl import Workbook

from app.core.config import Settings
from app.importers.pathway_profiles import (
    PATHWAY_PROFILE_TEMPLATE_HEADERS,
    PATHWAY_PROFILE_SAMPLE_ROW,
    format_candidate_type,
    format_exam_type,
    format_pathway_profile_bool,
)
from app.utils.parsers import make_timestamped_filename, relative_to_project


def build_pathway_profile_template() -> Workbook:
    workbook = Workbook()
    intro_sheet = workbook.active
    intro_sheet.title = "说明"
    intro_sheet.append(["升学画像导入模板"])
    intro_sheet.append(["学号为必填列，姓名用于辅助核对。"])
    intro_sheet.append(["空白单元格导入时会保留系统已有值，不会清空原画像。"])
    intro_sheet.append(["布尔字段支持 是/否、true/false、1/0。"])

    data_sheet = workbook.create_sheet("数据")
    data_sheet.append(PATHWAY_PROFILE_TEMPLATE_HEADERS)
    data_sheet.append(PATHWAY_PROFILE_SAMPLE_ROW)
    return workbook


def export_pathway_profile_template(settings: Settings) -> str:
    workbook = build_pathway_profile_template()
    path = settings.templates_dir / "student_pathway_profiles_import_template.xlsx"
    workbook.save(path)
    return relative_to_project(path, settings.project_root)


def export_pathway_profiles(settings: Settings, rows: list[dict[str, object]]) -> str:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "数据"
    sheet.append(PATHWAY_PROFILE_TEMPLATE_HEADERS)
    for row in rows:
        materials = row.get("materials_json") if isinstance(row.get("materials_json"), dict) else {}
        body_limitations = row.get("known_body_limitations_json")
        body_note = body_limitations.get("note") if isinstance(body_limitations, dict) else None
        sheet.append(
            [
                row.get("student_no"),
                row.get("name"),
                row.get("province"),
                format_candidate_type(row.get("candidate_type") if isinstance(row.get("candidate_type"), str) else None),
                format_exam_type(row.get("exam_type") if isinstance(row.get("exam_type"), str) else None),
                row.get("subject_combination"),
                row.get("spring_exam_category"),
                row.get("art_track"),
                row.get("sports_track"),
                format_pathway_profile_bool(row.get("has_gaokao_registration") if isinstance(row.get("has_gaokao_registration"), bool) else None),
                format_pathway_profile_bool(row.get("is_fresh_graduate") if isinstance(row.get("is_fresh_graduate"), bool) else None),
                format_pathway_profile_bool(row.get("is_vocational_student") if isinstance(row.get("is_vocational_student"), bool) else None),
                format_pathway_profile_bool(row.get("is_social_candidate") if isinstance(row.get("is_social_candidate"), bool) else None),
                format_pathway_profile_bool(row.get("has_high_school_equivalent") if isinstance(row.get("has_high_school_equivalent"), bool) else None),
                format_pathway_profile_bool(row.get("accept_junior_college") if isinstance(row.get("accept_junior_college"), bool) else None),
                format_pathway_profile_bool(row.get("accept_private_college") if isinstance(row.get("accept_private_college"), bool) else None),
                format_pathway_profile_bool(row.get("accept_sino_foreign") if isinstance(row.get("accept_sino_foreign"), bool) else None),
                format_pathway_profile_bool(row.get("accept_outside_province") if isinstance(row.get("accept_outside_province"), bool) else None),
                format_pathway_profile_bool(row.get("accept_early_batch") if isinstance(row.get("accept_early_batch"), bool) else None),
                format_pathway_profile_bool(row.get("accept_service_commitment") if isinstance(row.get("accept_service_commitment"), bool) else None),
                format_pathway_profile_bool(
                    row.get("accept_interview_or_physical_test")
                    if isinstance(row.get("accept_interview_or_physical_test"), bool)
                    else None
                ),
                format_pathway_profile_bool(materials.get("gaokao_registration") if isinstance(materials.get("gaokao_registration"), bool) else None),
                format_pathway_profile_bool(
                    materials.get("comprehensive_quality_evaluation")
                    if isinstance(materials.get("comprehensive_quality_evaluation"), bool)
                    else None
                ),
                format_pathway_profile_bool(
                    materials.get("single_exam_college_chapter_plan")
                    if isinstance(materials.get("single_exam_college_chapter_plan"), bool)
                    else None
                ),
                body_note,
                row.get("note"),
            ]
        )

    filename = make_timestamped_filename("student_pathway_profiles_export", ".xlsx")
    path = settings.exports_dir / filename
    workbook.save(path)
    return relative_to_project(path, settings.project_root)
