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
from app.models import AdmissionRecord, College, Major
from app.repositories.recommendations import (
    ensure_college_major,
    get_admission_record_by_key,
    get_college_by_name,
    get_major_by_name,
)
from app.schemas.common import ImportResult
from app.utils.parsers import clean_text, parse_int


@dataclass
class NormalizedStudentCategory:
    student_type: str
    art_track: str | None


class AdmissionImporter:
    expected_headers = ["年份", "省份", "批次", "院校", "专业", "最低分", "最低位次", "学生类别", "数据来源说明"]

    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.created_college_count = 0
        self.created_major_count = 0

    def execute(self, *, filename: str | None, content: bytes) -> tuple[ImportResult, int, int]:
        headers, rows = read_template_rows(content)
        if headers[: len(self.expected_headers)] != self.expected_headers:
            raise ValueError("录取数据导入模板表头不匹配，请先下载系统模板。")

        success_rows = 0
        failed_rows = 0
        row_errors: list[RowError] = []

        for row_number, values in rows:
            savepoint = self.session.begin_nested()
            try:
                self._upsert_row(values)
                savepoint.commit()
                success_rows += 1
            except Exception as exc:
                if savepoint.is_active:
                    savepoint.rollback()
                failed_rows += 1
                row_errors.append(build_row_error(row_number=row_number, values=values, message=str(exc)))

        error_report_path = save_error_report(
            settings=self.settings,
            prefix="admissions_import_errors",
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
                message=f"录取数据导入完成，成功 {success_rows} 条，失败 {failed_rows} 条。",
            ),
            self.created_college_count,
            self.created_major_count,
        )

    def _upsert_row(self, row: dict[str, object]) -> None:
        year = parse_int(row.get("年份"))
        province = clean_text(row.get("省份"))
        batch = clean_text(row.get("批次"))
        college_name = clean_text(row.get("院校"))
        major_name = clean_text(row.get("专业"))
        min_score = self._parse_float(row.get("最低分"))
        min_rank = parse_int(row.get("最低位次"))
        source_note = clean_text(row.get("数据来源说明"))
        category = self._normalize_student_category(clean_text(row.get("学生类别")))

        if year is None:
            raise ValueError("年份不能为空")
        if not province or not batch or not college_name:
            raise ValueError("省份、批次、院校不能为空")
        if min_score is None and min_rank is None:
            raise ValueError("最低分和最低位次至少填写一项")

        college = get_college_by_name(self.session, college_name)
        if college is None:
            college = College(
                name=college_name,
                province=province,
                supports_art=category.student_type != "general",
            )
            self.session.add(college)
            self.session.flush()
            self.created_college_count += 1
        elif not college.province:
            college.province = province
        if category.student_type != "general":
            college.supports_art = True

        major_id = None
        if major_name:
            major = get_major_by_name(self.session, major_name)
            if major is None:
                major = Major(
                    name=major_name,
                    is_art_related=category.student_type != "general",
                )
                self.session.add(major)
                self.session.flush()
                self.created_major_count += 1
            elif category.student_type != "general":
                major.is_art_related = True
            major_id = major.id
            ensure_college_major(self.session, college.id, major.id)

        current = get_admission_record_by_key(
            self.session,
            year=year,
            province=province,
            batch=batch,
            college_id=college.id,
            major_id=major_id,
            student_type=category.student_type,
            art_track=category.art_track,
        )
        if current is None:
            current = AdmissionRecord(
                year=year,
                province=province,
                batch=batch,
                college_id=college.id,
                major_id=major_id,
                student_type=category.student_type,
                art_track=category.art_track,
            )
            self.session.add(current)

        current.min_score = min_score
        current.min_rank = min_rank
        current.source_note = source_note
        current.is_active = True
        self.session.flush()

    @staticmethod
    def _parse_float(value: object) -> float | None:
        if value in (None, ""):
            return None
        return float(str(value).strip())

    @staticmethod
    def _normalize_student_category(value: str | None) -> NormalizedStudentCategory:
        if not value:
            return NormalizedStudentCategory(student_type="general", art_track=None)
        normalized = value.strip().lower()
        mapping = {
            "普通": ("general", None),
            "普通生": ("general", None),
            "普通类": ("general", None),
            "general": ("general", None),
            "艺体": ("art", None),
            "艺体生": ("art", None),
            "艺术类": ("art", None),
            "art": ("art", None),
            "美术类": ("art", "fine_art_design"),
            "美术": ("art", "fine_art_design"),
            "体育类": ("sports", "sports"),
            "体育": ("sports", "sports"),
            "音乐类": ("art", "music"),
            "音乐": ("art", "music"),
            "舞蹈类": ("art", "dance"),
            "舞蹈": ("art", "dance"),
            "传媒类": ("art", "media"),
            "传媒": ("art", "media"),
            "春季高考": ("spring_exam", None),
            "单独招生": ("independent_recruitment", None),
            "综合评价招生": ("comprehensive_evaluation", None),
        }
        if normalized in mapping:
            student_type, art_track = mapping[normalized]
            return NormalizedStudentCategory(student_type=student_type, art_track=art_track)
        return NormalizedStudentCategory(student_type=value.strip(), art_track=None)
