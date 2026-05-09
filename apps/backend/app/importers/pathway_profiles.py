from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
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
from app.models import Student, StudentPathwayProfile
from app.repositories.students import get_student_by_no
from app.schemas.common import ImportResult
from app.utils.parsers import clean_text

PATHWAY_PROFILE_TEMPLATE_HEADERS = [
    "学号",
    "姓名",
    "班级",
    "生源地",
    "考生类型",
    "考试类型",
    "选科组合",
    "春考专业类别",
    "艺术类别",
    "体育类别",
    "已完成高考报名",
    "普通高中应届",
    "中职学生",
    "社会人员",
    "高中阶段学历或同等学力",
    "接受专科",
    "接受民办院校",
    "接受中外合作",
    "接受省外院校",
    "接受提前批",
    "接受定向服务",
    "接受面试体检政审",
    "高考报名确认材料",
    "综合素质评价材料",
    "单招院校章程和分专业计划",
    "体检限制",
    "备注",
]

PATHWAY_PROFILE_SAMPLE_ROW = [
    "2026001",
    "张三",
    "1班",
    "山东",
    "普通类",
    "夏季高考",
    "物理,化学,生物",
    "",
    "",
    "",
    "是",
    "是",
    "否",
    "否",
    "",
    "是",
    "否",
    "否",
    "是",
    "否",
    "否",
    "否",
    "是",
    "",
    "",
    "无",
    "",
]

_HEADER_ALIASES = {
    "生源地省份": "生源地",
    "高考报名状态": "已完成高考报名",
    "春季高考专业类别": "春考专业类别",
    "春季高考类别": "春考专业类别",
    "是否接受专科": "接受专科",
    "是否接受民办院校": "接受民办院校",
    "是否接受中外合作": "接受中外合作",
    "是否接受省外院校": "接受省外院校",
    "是否接受提前批": "接受提前批",
    "是否接受定向服务": "接受定向服务",
    "是否接受面试体检政审": "接受面试体检政审",
}

_TEXT_FIELDS = {
    "生源地": "province",
    "选科组合": "subject_combination",
    "春考专业类别": "spring_exam_category",
    "艺术类别": "art_track",
    "体育类别": "sports_track",
    "备注": "note",
}

_BOOLEAN_FIELDS = {
    "已完成高考报名": "has_gaokao_registration",
    "普通高中应届": "is_fresh_graduate",
    "中职学生": "is_vocational_student",
    "社会人员": "is_social_candidate",
    "高中阶段学历或同等学力": "has_high_school_equivalent",
    "接受专科": "accept_junior_college",
    "接受民办院校": "accept_private_college",
    "接受中外合作": "accept_sino_foreign",
    "接受省外院校": "accept_outside_province",
    "接受提前批": "accept_early_batch",
    "接受定向服务": "accept_service_commitment",
    "接受面试体检政审": "accept_interview_or_physical_test",
}

_MATERIAL_FIELDS = {
    "高考报名确认材料": "gaokao_registration",
    "综合素质评价材料": "comprehensive_quality_evaluation",
    "单招院校章程和分专业计划": "single_exam_college_chapter_plan",
}

_CANDIDATE_TYPE_MAP = {
    "general": "general",
    "普通类": "general",
    "普通生": "general",
    "spring_exam": "spring_exam",
    "春季高考": "spring_exam",
    "independent_recruitment": "independent_recruitment",
    "高职单招": "independent_recruitment",
    "单招": "independent_recruitment",
    "comprehensive_evaluation": "comprehensive_evaluation",
    "高职综评": "comprehensive_evaluation",
    "综合评价": "comprehensive_evaluation",
    "art": "art",
    "艺术类": "art",
    "sports": "sports",
    "体育类": "sports",
}

_CANDIDATE_TYPE_LABELS = {value: key for key, value in _CANDIDATE_TYPE_MAP.items() if key.endswith("类") or key in {"普通生", "春季高考", "高职单招", "高职综评"}}
_CANDIDATE_TYPE_LABELS.update(
    {
        "general": "普通类",
        "spring_exam": "春季高考",
        "independent_recruitment": "高职单招",
        "comprehensive_evaluation": "高职综评",
        "art": "艺术类",
        "sports": "体育类",
    }
)

_EXAM_TYPE_MAP = {
    "summer_gaokao": "summer_gaokao",
    "夏季高考": "summer_gaokao",
    "spring_exam": "spring_exam",
    "春季高考": "spring_exam",
    "vocational_single_exam": "vocational_single_exam",
    "高职单招": "vocational_single_exam",
    "vocational_comprehensive": "vocational_comprehensive",
    "高职综评": "vocational_comprehensive",
    "sports_single_exam": "sports_single_exam",
    "体育单招": "sports_single_exam",
    "high_level_sports": "high_level_sports",
    "高水平运动队": "high_level_sports",
}

_EXAM_TYPE_LABELS = {
    "summer_gaokao": "夏季高考",
    "spring_exam": "春季高考",
    "vocational_single_exam": "高职单招",
    "vocational_comprehensive": "高职综评",
    "sports_single_exam": "体育单招",
    "high_level_sports": "高水平运动队",
}


@dataclass
class PathwayProfileImportPayload:
    student: Student
    province: str | None = None
    candidate_type: str | None = None
    exam_type: str | None = None
    text_updates: dict[str, str] = field(default_factory=dict)
    boolean_updates: dict[str, bool] = field(default_factory=dict)
    material_updates: dict[str, bool] = field(default_factory=dict)
    body_limitations_note: str | None = None


class StudentPathwayProfileImporter:
    expected_headers = PATHWAY_PROFILE_TEMPLATE_HEADERS
    allowed_headers = set(PATHWAY_PROFILE_TEMPLATE_HEADERS)

    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    def execute(self, *, filename: str | None, content: bytes) -> ImportResult:
        headers, rows = read_template_rows(content)
        normalized_headers = [self._normalize_header(header) for header in headers]
        self._validate_headers(normalized_headers)

        success_rows = 0
        failed_rows = 0
        created_rows = 0
        updated_rows = 0
        row_errors: list[RowError] = []

        for row_number, row_values in rows:
            normalized_row = {
                self._normalize_header(header): value
                for header, value in row_values.items()
                if self._normalize_header(header)
            }
            try:
                payload = self._parse_row(normalized_row)
                existing = self._get_existing_profile(payload.student.id, payload.province)
                if existing:
                    profile = existing
                    updated_rows += 1
                else:
                    profile = self._build_profile_from_student(payload.student, payload.province)
                    self.session.add(profile)
                    self.session.flush()
                    created_rows += 1
                self._apply(profile, payload)
                success_rows += 1
            except Exception as exc:
                failed_rows += 1
                row_errors.append(build_row_error(row_number=row_number, values=row_values, message=str(exc)))

        error_report_path = save_error_report(
            settings=self.settings,
            prefix="pathway_profile_import_errors",
            headers=self.expected_headers,
            errors=row_errors,
        )
        return ImportResult(
            status=resolve_import_status(
                total_rows=len(rows),
                success_rows=success_rows,
                failed_rows=failed_rows,
            ),
            total_rows=len(rows),
            success_rows=success_rows,
            failed_rows=failed_rows,
            skipped_rows=0,
            created_rows=created_rows,
            updated_rows=updated_rows,
            error_report_path=error_report_path,
            error_preview=build_error_preview(row_errors),
            notice_preview=[],
            message=f"升学画像导入完成，成功 {success_rows} 条，失败 {failed_rows} 条。",
        )

    @classmethod
    def _normalize_header(cls, header: str) -> str:
        text = str(header or "").strip()
        return _HEADER_ALIASES.get(text, text)

    def _validate_headers(self, headers: list[str]) -> None:
        meaningful_headers = [header for header in headers if header]
        if "学号" not in meaningful_headers:
            raise ValueError("升学画像导入模板表头不匹配：必须包含“学号”列。")
        unknown_headers = [header for header in meaningful_headers if header not in self.allowed_headers]
        if unknown_headers:
            raise ValueError(f"升学画像导入模板表头不匹配：无法识别“{unknown_headers[0]}”列。请先下载系统模板。")

    def _parse_row(self, row: dict[str, object]) -> PathwayProfileImportPayload:
        student_no = clean_text(row.get("学号"))
        name = clean_text(row.get("姓名"))
        if not student_no:
            raise ValueError("学号不能为空")
        student = get_student_by_no(self.session, student_no)
        if not student:
            raise ValueError(f"学生不存在: {student_no}")
        if name and name != student.name:
            raise ValueError(f"姓名不一致: 系统为{student.name}，导入为{name}")

        province = clean_text(row.get("生源地"))
        payload = PathwayProfileImportPayload(student=student, province=province)
        candidate_type = clean_text(row.get("考生类型"))
        if candidate_type:
            payload.candidate_type = self._map_value("考生类型", candidate_type, _CANDIDATE_TYPE_MAP)
        exam_type = clean_text(row.get("考试类型"))
        if exam_type:
            payload.exam_type = self._map_value("考试类型", exam_type, _EXAM_TYPE_MAP)

        for header, field_name in _TEXT_FIELDS.items():
            value = clean_text(row.get(header))
            if value:
                if field_name == "province":
                    payload.province = value
                else:
                    payload.text_updates[field_name] = value

        for header, field_name in _BOOLEAN_FIELDS.items():
            value = self._parse_optional_bool(header, row.get(header))
            if value is not None:
                payload.boolean_updates[field_name] = value

        for header, material_key in _MATERIAL_FIELDS.items():
            value = self._parse_optional_bool(header, row.get(header))
            if value is not None:
                payload.material_updates[material_key] = value

        body_limitations_note = clean_text(row.get("体检限制"))
        if body_limitations_note:
            payload.body_limitations_note = body_limitations_note
        return payload

    @staticmethod
    def _map_value(label: str, value: str, mapping: dict[str, str]) -> str:
        if value not in mapping:
            raise ValueError(f"{label} 无法识别: {value}")
        return mapping[value]

    @staticmethod
    def _parse_optional_bool(label: str, raw_value: object) -> bool | None:
        text = clean_text(raw_value)
        if not text:
            return None
        normalized = text.lower()
        if normalized in {"是", "y", "yes", "true", "1", "已确认", "接受", "符合"}:
            return True
        if normalized in {"否", "n", "no", "false", "0", "不符合", "不接受"}:
            return False
        raise ValueError(f"{label} 无法识别: {text}")

    def _get_existing_profile(self, student_id: int, province: str | None) -> StudentPathwayProfile | None:
        if province:
            return self.session.scalar(
                select(StudentPathwayProfile).where(
                    StudentPathwayProfile.student_id == student_id,
                    StudentPathwayProfile.province == province,
                )
            )
        default_profile = self.session.scalar(
            select(StudentPathwayProfile).where(
                StudentPathwayProfile.student_id == student_id,
                StudentPathwayProfile.province == "山东",
            )
        )
        if default_profile:
            return default_profile
        return self.session.scalar(select(StudentPathwayProfile).where(StudentPathwayProfile.student_id == student_id))

    @staticmethod
    def _build_profile_from_student(student: Student, province: str | None) -> StudentPathwayProfile:
        candidate_type = student.student_type or "general"
        if student.art_track:
            candidate_type = "art"
        return StudentPathwayProfile(
            student_id=student.id,
            province=province or student.origin_province or "山东",
            candidate_type=candidate_type,
            art_track=student.art_track,
            career_preferences_json={},
            region_preferences_json={},
            family_constraints_json={},
            known_body_limitations_json={},
            materials_json={},
            is_active=True,
        )

    @staticmethod
    def _apply(profile: StudentPathwayProfile, payload: PathwayProfileImportPayload) -> None:
        if payload.province:
            profile.province = payload.province
        if payload.candidate_type:
            profile.candidate_type = payload.candidate_type
        if payload.exam_type:
            profile.exam_type = payload.exam_type
        for field_name, value in payload.text_updates.items():
            setattr(profile, field_name, value)
        for field_name, value in payload.boolean_updates.items():
            setattr(profile, field_name, value)
        if payload.material_updates:
            materials = dict(profile.materials_json or {})
            materials.update(payload.material_updates)
            profile.materials_json = materials
        if payload.body_limitations_note:
            profile.known_body_limitations_json = {"note": payload.body_limitations_note}
        profile.is_active = True


def format_pathway_profile_bool(value: bool | None) -> str | None:
    if value is True:
        return "是"
    if value is False:
        return "否"
    return None


def format_candidate_type(value: str | None) -> str | None:
    return _CANDIDATE_TYPE_LABELS.get(value or "")


def format_exam_type(value: str | None) -> str | None:
    return _EXAM_TYPE_LABELS.get(value or "")
