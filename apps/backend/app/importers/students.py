from __future__ import annotations

from collections import Counter
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
    origin_province: str | None
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
        "生源地省份",
        "联系电话",
        "家庭住址",
        "备注",
    ]
    header_aliases = {
        "省学籍辅号": "学号",
        "现住地址": "家庭住址",
    }

    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        grades = session.scalars(select(Grade)).all()
        self.grade_map = {grade.name: grade for grade in grades}
        self.grade_name_by_id = {grade.id: grade.name for grade in grades}
        self.class_map = {
            (school_class.grade_id, school_class.name): school_class
            for school_class in session.scalars(select(SchoolClass)).all()
        }
        self.student_status_map = self._build_dict_lookup("student_status")
        self.student_type_map = self._build_dict_lookup("student_type")
        self.art_track_map = self._build_dict_lookup("art_track")
        self.created_class_keys: set[tuple[int, str]] = set()

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
        normalized_headers = [self._normalize_header(header) for header in headers]
        if normalized_headers[: len(self.expected_headers)] != self.expected_headers:
            raise ValueError(self._build_header_mismatch_message(headers, normalized_headers))
        self.created_class_keys.clear()

        success_rows = 0
        failed_rows = 0
        skipped_rows = 0
        row_errors: list[RowError] = []

        for row_number, row_values in rows:
            normalized_row = {
                self._normalize_header(header): value
                for header, value in row_values.items()
            }
            try:
                payload = self._parse_row(normalized_row)
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
            error_preview=self._build_error_preview(row_errors),
            notice_preview=self._build_notice_preview(row_errors),
            message=self._build_result_message(success_rows, failed_rows),
        )

    @classmethod
    def _normalize_header(cls, header: str) -> str:
        return cls.header_aliases.get(header, header)

    def _build_header_mismatch_message(
        self,
        headers: list[str],
        normalized_headers: list[str],
    ) -> str:
        mismatches: list[str] = []
        for index, expected in enumerate(self.expected_headers):
            actual = headers[index] if index < len(headers) else ""
            actual_normalized = normalized_headers[index] if index < len(normalized_headers) else ""
            if actual_normalized == expected:
                continue
            actual_display = actual or "空"
            mismatches.append(f"第 {index + 1} 列应为“{expected}”，实际为“{actual_display}”")
            if len(mismatches) >= 4:
                break
        detail = "；".join(mismatches) if mismatches else "表头顺序或字段不符合模板要求"
        return f"学生导入模板表头不匹配：{detail}。请先下载系统模板。"

    @staticmethod
    def _build_error_preview(row_errors: list[RowError]) -> list[str]:
        return [f"第 {item.row_number} 行：{item.message}" for item in row_errors[:3]]

    def _build_notice_preview(self, row_errors: list[RowError]) -> list[str]:
        notices: list[str] = []

        created_class_notice = self._build_created_class_notice()
        if created_class_notice:
            notices.append(created_class_notice)

        missing_grade_counter: Counter[str] = Counter()
        dict_issue_counters = {
            "学生状态": Counter[str](),
            "学生类别": Counter[str](),
            "艺体方向": Counter[str](),
        }

        for item in row_errors:
            if item.message.startswith("年级不存在: "):
                missing_grade_counter[item.message.removeprefix("年级不存在: ")] += 1
                continue

            for label, counter in dict_issue_counters.items():
                prefix = f"{label} 无法识别: "
                if item.message.startswith(prefix):
                    counter[item.message.removeprefix(prefix)] += 1
                    break

        if missing_grade_counter:
            notices.append(self._format_counter_notice("未匹配年级", missing_grade_counter))

        for label, counter in dict_issue_counters.items():
            if counter:
                notices.append(self._format_counter_notice(f"{label}待核对", counter))

        return notices

    def _build_created_class_notice(self) -> str | None:
        if not self.created_class_keys:
            return None

        entries = [
            f"{self.grade_name_by_id.get(grade_id, f'年级 {grade_id}')} / {class_name}"
            for grade_id, class_name in sorted(
                self.created_class_keys,
                key=lambda item: (self.grade_name_by_id.get(item[0], ""), item[1]),
            )
        ]
        preview = "，".join(entries[:3])
        if len(entries) > 3:
            return f"已自动创建班级：{preview} 等 {len(entries)} 个班级。"
        return f"已自动创建班级：{preview}。"

    @staticmethod
    def _format_counter_notice(title: str, counter: Counter[str]) -> str:
        ranked = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
        preview = "，".join(f"{value}（{count} 行）" for value, count in ranked[:3])
        if len(ranked) > 3:
            return f"{title}：{preview} 等 {len(ranked)} 项。"
        return f"{title}：{preview}。"

    def _build_result_message(self, success_rows: int, failed_rows: int) -> str:
        message = f"学生导入完成，成功 {success_rows} 条，失败 {failed_rows} 条。"
        if self.created_class_keys:
            message += f"已自动创建班级 {len(self.created_class_keys)} 个。"
        return message

    def _parse_row(self, row: dict[str, object]) -> StudentImportPayload:
        student_no = clean_text(row.get("学号"))
        name = clean_text(row.get("姓名"))
        if not student_no:
            raise ValueError("学号不能为空")
        if not name:
            raise ValueError("姓名不能为空")

        grade_name = clean_text(row.get("年级"))
        grade = self.grade_map.get(grade_name) if grade_name else None
        if grade_name and grade is None:
            raise ValueError(f"年级不存在: {grade_name}")

        class_name = clean_text(row.get("班级"))
        school_class = None
        if class_name:
            school_class = self._resolve_class(grade, class_name)
            if school_class is None:
                raise ValueError(f"班级不存在: {class_name}")
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
            origin_province=clean_text(row.get("生源地省份")),
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

    def _resolve_class(self, grade: Grade | None, class_name: str) -> SchoolClass | None:
        if grade:
            key = (grade.id, class_name)
            school_class = self.class_map.get(key)
            if school_class is not None:
                return school_class
            school_class = SchoolClass(
                grade_id=grade.id,
                name=class_name,
                class_type="normal",
                student_count=0,
            )
            self.session.add(school_class)
            self.session.flush()
            self.class_map[key] = school_class
            self.created_class_keys.add(key)
            return school_class
        return get_class_by_name(
            self.session,
            class_name=class_name,
            grade_id=grade.id if grade else None,
        )

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
        student.origin_province = payload.origin_province
        student.phone = payload.phone
        student.address = payload.address
        student.note = payload.note
