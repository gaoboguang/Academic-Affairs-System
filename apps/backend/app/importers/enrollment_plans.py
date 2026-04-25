from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.importers.base import (
    RowError,
    build_error_preview,
    build_row_error,
    read_template_rows,
    resolve_import_status,
    save_error_report,
)
from app.models import College, EnrollmentPlan, Major
from app.repositories.recommendations import (
    ensure_college_major,
    get_college_by_name,
    get_enrollment_plan_by_key,
    get_major_by_name,
)
from app.schemas.common import ImportResult
from app.utils.parsers import clean_text, parse_int


@dataclass
class NormalizedPlanCategory:
    student_type: str


class EnrollmentPlanImporter:
    expected_headers = [
        "年份",
        "省份",
        "批次",
        "科类/模式",
        "院校",
        "院校代码",
        "专业组编号",
        "专业",
        "专业代码",
        "计划人数",
        "选科要求",
        "学费",
        "学制",
        "培养地点",
        "学生类别",
        "数据来源",
        "导入批次",
    ]

    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.created_college_count = 0
        self.created_major_count = 0

    def execute(self, *, filename: str | None, content: bytes) -> tuple[ImportResult, int, int]:
        headers, rows = read_template_rows(content)
        if headers[: len(self.expected_headers)] != self.expected_headers:
            raise ValueError("招生计划导入模板表头不匹配，请先下载系统模板。")

        success_rows = 0
        failed_rows = 0
        row_errors: list[RowError] = []

        for row_number, values in rows:
            try:
                self._upsert_row(values)
                success_rows += 1
            except Exception as exc:
                failed_rows += 1
                row_errors.append(build_row_error(row_number=row_number, values=values, message=str(exc)))

        error_report_path = save_error_report(
            settings=self.settings,
            prefix="enrollment_plans_import_errors",
            headers=self.expected_headers,
            errors=row_errors,
        )
        return (
            ImportResult(
                status=resolve_import_status(
                    total_rows=len(rows),
                    success_rows=success_rows,
                    failed_rows=failed_rows,
                ),
                total_rows=len(rows),
                success_rows=success_rows,
                failed_rows=failed_rows,
                skipped_rows=0,
                created_rows=self.created_college_count + self.created_major_count,
                error_report_path=error_report_path,
                error_preview=build_error_preview(row_errors),
                message=f"招生计划导入完成，成功 {success_rows} 条，失败 {failed_rows} 条。",
            ),
            self.created_college_count,
            self.created_major_count,
        )

    def _upsert_row(self, row: dict[str, object]) -> None:
        year = parse_int(row.get("年份"))
        province = clean_text(row.get("省份"))
        batch = clean_text(row.get("批次"))
        exam_mode = clean_text(row.get("科类/模式")) or "普通类"
        college_name = clean_text(row.get("院校"))
        college_code = clean_text(row.get("院校代码"))
        major_group_code = clean_text(row.get("专业组编号")) or ""
        major_name = clean_text(row.get("专业"))
        major_code = clean_text(row.get("专业代码"))
        plan_count = parse_int(row.get("计划人数"))
        subject_requirement = clean_text(row.get("选科要求"))
        tuition_fee = clean_text(row.get("学费"))
        schooling_years = clean_text(row.get("学制"))
        training_location = clean_text(row.get("培养地点"))
        source_note = clean_text(row.get("数据来源"))
        import_batch_name = clean_text(row.get("导入批次"))
        category = self._normalize_student_category(clean_text(row.get("学生类别")))

        if year is None:
            raise ValueError("年份不能为空")
        if not province or not batch or not college_name:
            raise ValueError("省份、批次、院校不能为空")
        if not major_name and not major_group_code:
            raise ValueError("专业或专业组编号至少填写一项")
        if plan_count is None or plan_count <= 0:
            raise ValueError("计划人数必须为正整数")

        college = get_college_by_name(self.session, college_name)
        if college is None:
            college = College(
                name=college_name,
                college_code=college_code,
                province=province,
            )
            self.session.add(college)
            self.session.flush()
            self.created_college_count += 1
        else:
            if college_code and not college.college_code:
                college.college_code = college_code
            if not college.province:
                college.province = province

        major_id = None
        major_name_snapshot = major_name or ""
        if major_name:
            major = get_major_by_name(self.session, major_name)
            if major is None:
                major = Major(
                    name=major_name,
                    major_code=major_code,
                )
                self.session.add(major)
                self.session.flush()
                self.created_major_count += 1
            elif major_code and not major.major_code:
                major.major_code = major_code
            major_id = major.id
            ensure_college_major(self.session, college.id, major.id)

        current = get_enrollment_plan_by_key(
            self.session,
            year=year,
            province=province,
            batch=batch,
            exam_mode=exam_mode,
            college_id=college.id,
            major_group_code=major_group_code,
            major_name_snapshot=major_name_snapshot,
            student_type=category.student_type,
        )
        if current is None:
            current = EnrollmentPlan(
                year=year,
                province=province,
                batch=batch,
                exam_mode=exam_mode,
                college_id=college.id,
                major_group_code=major_group_code,
                major_name_snapshot=major_name_snapshot,
                student_type=category.student_type,
                plan_count=plan_count,
            )
            self.session.add(current)

        current.major_id = major_id
        current.college_code_snapshot = college_code or college.college_code
        current.major_code_snapshot = major_code
        current.plan_count = plan_count
        current.subject_requirement = subject_requirement
        current.tuition_fee = tuition_fee
        current.schooling_years = schooling_years
        current.training_location = training_location
        current.source_note = source_note
        current.import_batch_name = import_batch_name
        current.is_active = True
        self.session.flush()

    @staticmethod
    def _normalize_student_category(value: str | None) -> NormalizedPlanCategory:
        if not value:
            return NormalizedPlanCategory(student_type="general")
        normalized = value.strip().lower()
        mapping = {
            "普通": "general",
            "普通生": "general",
            "普通类": "general",
            "general": "general",
            "艺体": "art",
            "艺体生": "art",
            "艺术类": "art",
            "art": "art",
            "美术类": "art",
            "美术": "art",
            "体育类": "sports",
            "体育": "sports",
            "复读": "repeat",
            "复读生": "repeat",
            "春季高考": "spring_exam",
            "单独招生": "independent_recruitment",
            "综合评价招生": "comprehensive_evaluation",
        }
        return NormalizedPlanCategory(student_type=mapping.get(normalized, value.strip()))
