from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.importers.base import RowError, read_template_rows, save_error_report
from app.models import DictItem, DictType, Grade, SchoolClass, Student
from app.repositories.students import get_class_by_name, get_student_by_no
from app.schemas.common import ImportResult
from app.utils.parsers import clean_text, parse_date, parse_int


@dataclass
class StudentImportPayload:
    student_no: str
    name: str
    gender: str | None
    birth_date: date | None
    admission_year: int | None
    current_grade_id: int | None
    current_class_id: int | None
    status: str | None
    student_type: str | None
    art_track: str | None
    phone: str | None
    address: str | None
    note: str | None


class StudentImporter:
    expected_headers = [
        "学号",
        "姓名",
        "性别",
        "出生日期",
        "入学年份",
        "年级",
        "班级",
        "学生状态",
        "学生类别",
        "艺体方向",
        "联系电话",
        "家庭住址",
        "备注",
    ]

    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.grade_map = {
            grade.name: grade for grade in session.scalars(select(Grade)).all()
        }
        self.student_status_map = self._build_dict_lookup("student_status")
        self.student_type_map = self._build_dict_lookup("student_type")
        self.art_track_map = self._build_dict_lookup("art_track")

    def _build_dict_lookup(self, dict_code: str) -> dict[str, str]:
        stmt = (
            select(DictItem)
            .join(DictType, DictItem.dict_type_id == DictType.id)
            .where(DictType.code == dict_code)
        )
        items = self.session.scalars(stmt).all()
        lookup: dict[str, str] = {}
        for item in items:
            lookup[item.code] = item.code
            lookup[item.name] = item.code
        return lookup

    def execute(self, *, filename: str | None, content: bytes, strategy: str) -> ImportResult:
        headers, rows = read_template_rows(content)
        if headers[: len(self.expected_headers)] != self.expected_headers:
            raise ValueError("学生导入模板表头不匹配，请先下载系统模板。")

        success_rows = 0
        failed_rows = 0
        skipped_rows = 0
        row_errors: list[RowError] = []

        for row_number, row_values in rows:
            try:
                payload = self._parse_row(row_values)
                existing = get_student_by_no(self.session, payload.student_no)

                if existing:
                    if strategy == "create":
                        raise ValueError(f"学号 {payload.student_no} 已存在")
                    if strategy == "skip_existing":
                        skipped_rows += 1
                        continue
                    self._apply(existing, payload)
                else:
                    student = Student(student_no=payload.student_no, name=payload.name)
                    self.session.add(student)
                    self.session.flush()
                    self._apply(student, payload)

                success_rows += 1
            except Exception as exc:
                failed_rows += 1
                row_errors.append(RowError(row_number=row_number, values=row_values, message=str(exc)))

        error_report_path = save_error_report(
            settings=self.settings,
            prefix="student_import_errors",
            headers=self.expected_headers,
            errors=row_errors,
        )
        return ImportResult(
            total_rows=len(rows),
            success_rows=success_rows,
            failed_rows=failed_rows,
            skipped_rows=skipped_rows,
            error_report_path=error_report_path,
            message=f"学生导入完成，成功 {success_rows} 条，失败 {failed_rows} 条。",
        )

    def _parse_row(self, row: dict[str, object]) -> StudentImportPayload:
        student_no = clean_text(row.get("学号"))
        name = clean_text(row.get("姓名"))
        if not student_no:
            raise ValueError("学号不能为空")
        if not name:
            raise ValueError("姓名不能为空")

        grade_name = clean_text(row.get("年级"))
        class_name = clean_text(row.get("班级"))
        grade = self.grade_map.get(grade_name) if grade_name else None
        school_class = None
        if class_name:
            school_class = get_class_by_name(
                self.session,
                class_name=class_name,
                grade_id=grade.id if grade else None,
            )
            if school_class is None:
                raise ValueError(f"班级不存在: {class_name}")
        if grade_name and grade is None:
            raise ValueError(f"年级不存在: {grade_name}")
        if grade and school_class and school_class.grade_id != grade.id:
            raise ValueError("班级与年级不匹配")

        return StudentImportPayload(
            student_no=student_no,
            name=name,
            gender=clean_text(row.get("性别")),
            birth_date=parse_date(row.get("出生日期")),
            admission_year=parse_int(row.get("入学年份")),
            current_grade_id=grade.id if grade else (school_class.grade_id if school_class else None),
            current_class_id=school_class.id if school_class else None,
            status=self._map_dict_value("学生状态", row.get("学生状态"), self.student_status_map),
            student_type=self._map_dict_value("学生类别", row.get("学生类别"), self.student_type_map),
            art_track=self._map_dict_value("艺体方向", row.get("艺体方向"), self.art_track_map),
            phone=clean_text(row.get("联系电话")),
            address=clean_text(row.get("家庭住址")),
            note=clean_text(row.get("备注")),
        )

    def _map_dict_value(
        self,
        label: str,
        raw_value: object,
        mapping: dict[str, str],
    ) -> str | None:
        text = clean_text(raw_value)
        if not text:
            return None
        if text not in mapping:
            raise ValueError(f"{label} 无法识别: {text}")
        return mapping[text]

    def _apply(self, student: Student, payload: StudentImportPayload) -> None:
        student.student_no = payload.student_no
        student.name = payload.name
        student.gender = payload.gender
        student.birth_date = payload.birth_date
        student.admission_year = payload.admission_year
        student.current_grade_id = payload.current_grade_id
        student.current_class_id = payload.current_class_id
        student.status = payload.status
        student.student_type = payload.student_type
        student.art_track = payload.art_track
        student.phone = payload.phone
        student.address = payload.address
        student.note = payload.note

