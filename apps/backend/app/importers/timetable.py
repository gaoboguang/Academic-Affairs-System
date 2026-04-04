from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.importers.base import RowError, read_template_rows, save_error_report
from app.models import DictItem, DictType, SchoolClass, Semester, Subject, Teacher, TimetableBatch, TimetableEntry
from app.schemas.common import ImportResult
from app.utils.parsers import clean_text, parse_int


@dataclass
class ParsedWeekRule:
    rule: str
    weeks: list[int] | None


@dataclass
class TimetableParsedRow:
    weekday: int
    period_no: int
    teacher_id: int | None
    class_id: int | None
    subject_id: int | None
    course_type: str | None
    week_rule: str
    week_list_json: list[int] | None
    note: str | None
    mapping_status: str
    raw_teacher_name: str | None
    raw_class_name: str | None
    raw_subject_name: str | None
    raw_course_type: str | None


class TimetableImporter:
    expected_headers = ["学期", "星期", "节次", "教师", "班级", "学科", "课程类型", "周次规则", "备注"]

    def __init__(self, session: Session, settings: Settings, semester: Semester) -> None:
        self.session = session
        self.settings = settings
        self.semester = semester
        self.semester_labels = {
            semester.name,
            f"{semester.academic_year.name} {semester.name}" if semester.academic_year else semester.name,
        }
        self.teacher_map = self._build_teacher_map()
        self.class_map = self._build_class_map()
        self.subject_map = self._build_subject_map()
        self.course_type_map = self._build_dict_lookup("course_type")

    def _build_teacher_map(self) -> dict[str, int]:
        mapping: dict[str, int] = {}
        for item in self.session.scalars(select(Teacher).where(Teacher.is_active.is_(True))).all():
            mapping[item.name] = item.id
            mapping[item.teacher_no] = item.id
        return mapping

    def _build_class_map(self) -> dict[str, int | None]:
        grouped: dict[str, list[int]] = {}
        for item in self.session.scalars(select(SchoolClass).where(SchoolClass.is_active.is_(True))).all():
            grouped.setdefault(item.name, []).append(item.id)
        mapping: dict[str, int | None] = {}
        for key, ids in grouped.items():
            mapping[key] = ids[0] if len(ids) == 1 else None
        return mapping

    def _build_subject_map(self) -> dict[str, int]:
        mapping: dict[str, int] = {}
        for item in self.session.scalars(select(Subject).where(Subject.is_active.is_(True))).all():
            mapping[item.name] = item.id
            mapping[item.code] = item.id
        return mapping

    def _build_dict_lookup(self, dict_code: str) -> dict[str, str]:
        stmt = (
            select(DictItem)
            .join(DictType, DictItem.dict_type_id == DictType.id)
            .where(DictType.code == dict_code, DictItem.is_active.is_(True))
        )
        mapping: dict[str, str] = {}
        for item in self.session.scalars(stmt).all():
            mapping[item.name] = item.code
            mapping[item.code] = item.code
        return mapping

    def execute(self, *, filename: str | None, content: bytes, batch: TimetableBatch) -> tuple[ImportResult, int]:
        headers, rows = read_template_rows(content)
        if headers[: len(self.expected_headers)] != self.expected_headers:
            raise ValueError("课表导入模板表头不匹配，请先下载系统模板。")

        success_rows = 0
        failed_rows = 0
        unresolved_rows = 0
        row_errors: list[RowError] = []

        for row_number, values in rows:
            try:
                parsed = self._parse_row(values)
                if parsed.mapping_status != "matched":
                    unresolved_rows += 1
                self.session.add(
                    TimetableEntry(
                        batch_id=batch.id,
                        semester_id=self.semester.id,
                        weekday=parsed.weekday,
                        period_no=parsed.period_no,
                        teacher_id=parsed.teacher_id,
                        class_id=parsed.class_id,
                        subject_id=parsed.subject_id,
                        course_type=parsed.course_type,
                        week_rule=parsed.week_rule,
                        week_list_json=parsed.week_list_json,
                        note=parsed.note,
                        mapping_status=parsed.mapping_status,
                        raw_teacher_name=parsed.raw_teacher_name,
                        raw_class_name=parsed.raw_class_name,
                        raw_subject_name=parsed.raw_subject_name,
                        raw_course_type=parsed.raw_course_type,
                    )
                )
                success_rows += 1
            except Exception as exc:
                failed_rows += 1
                row_errors.append(RowError(row_number=row_number, values=values, message=str(exc)))

        error_report_path = save_error_report(
            settings=self.settings,
            prefix="timetable_import_errors",
            headers=self.expected_headers,
            errors=row_errors,
        )
        return (
            ImportResult(
                total_rows=len(rows),
                success_rows=success_rows,
                failed_rows=failed_rows,
                skipped_rows=0,
                error_report_path=error_report_path,
                message=f"课表导入完成，成功 {success_rows} 条，失败 {failed_rows} 条。",
            ),
            unresolved_rows,
        )

    def _parse_row(self, row: dict[str, object]) -> TimetableParsedRow:
        semester_label = clean_text(row.get("学期"))
        if semester_label and semester_label not in self.semester_labels:
            raise ValueError(f"学期不匹配: {semester_label}")

        weekday = parse_int(row.get("星期"))
        period_no = parse_int(row.get("节次"))
        if weekday is None or weekday < 1 or weekday > 7:
            raise ValueError("星期必须为 1-7")
        if period_no is None or period_no < 1:
            raise ValueError("节次必须为正整数")

        teacher_name = clean_text(row.get("教师"))
        class_name = clean_text(row.get("班级"))
        subject_name = clean_text(row.get("学科"))
        course_type_text = clean_text(row.get("课程类型"))
        note = clean_text(row.get("备注"))
        week_rule_raw = clean_text(row.get("周次规则")) or "全周"

        parsed_week_rule = self._parse_week_rule(week_rule_raw)
        teacher_id = self.teacher_map.get(teacher_name) if teacher_name else None
        class_id = self.class_map.get(class_name) if class_name else None
        subject_id = self.subject_map.get(subject_name) if subject_name else None
        course_type = self.course_type_map.get(course_type_text) if course_type_text else None

        unresolved = []
        if teacher_name and teacher_id is None:
            unresolved.append("teacher")
        if class_name and class_id is None:
            unresolved.append("class")
        if subject_name and subject_id is None:
            unresolved.append("subject")
        if course_type_text and course_type is None:
            unresolved.append("course_type")

        return TimetableParsedRow(
            weekday=weekday,
            period_no=period_no,
            teacher_id=teacher_id,
            class_id=class_id,
            subject_id=subject_id,
            course_type=course_type,
            week_rule=parsed_week_rule.rule,
            week_list_json=parsed_week_rule.weeks,
            note=note,
            mapping_status="matched" if not unresolved else "unresolved",
            raw_teacher_name=teacher_name,
            raw_class_name=class_name,
            raw_subject_name=subject_name,
            raw_course_type=course_type_text,
        )

    def _parse_week_rule(self, raw_value: str) -> ParsedWeekRule:
        normalized = raw_value.replace("，", ",").replace(" ", "")
        if normalized in {"全周", "all", "ALL"}:
            return ParsedWeekRule(rule="all", weeks=None)
        if normalized in {"单周", "odd"}:
            return ParsedWeekRule(rule="odd", weeks=None)
        if normalized in {"双周", "even"}:
            return ParsedWeekRule(rule="even", weeks=None)
        weeks_text = normalized
        if ":" in normalized:
            _, weeks_text = normalized.split(":", 1)
        weeks = [parse_int(item) for item in weeks_text.split(",") if item]
        if not weeks or any(week is None or week < 1 for week in weeks):
            raise ValueError(f"周次规则无法识别: {raw_value}")
        return ParsedWeekRule(rule="custom", weeks=[int(week) for week in weeks if week is not None])

