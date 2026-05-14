from __future__ import annotations

from dataclasses import dataclass
from datetime import date

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
from app.models import DictItem, DictType, Subject, Teacher
from app.repositories.teachers import get_teacher_by_no
from app.schemas.common import ImportResult
from app.utils.parsers import clean_text, parse_bool, parse_date


@dataclass
class TeacherImportPayload:
    teacher_no: str
    name: str
    gender: str | None
    subject_id: int | None
    phone: str | None
    title_code: str | None
    position_code: str | None
    is_head_teacher: bool
    employment_status: str | None
    entry_date: date | None
    note: str | None


class TeacherImporter:
    expected_headers = [
        "工号",
        "姓名",
        "性别",
        "学科",
        "联系方式",
        "职称",
        "岗位",
        "是否班主任",
        "任教状态",
        "入职日期",
        "备注",
    ]

    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.subject_map = {}
        for subject in session.scalars(select(Subject)).all():
            self.subject_map[subject.code] = subject
            self.subject_map[subject.name] = subject
        self.title_map = self._build_dict_lookup("teacher_title")
        self.position_map = self._build_dict_lookup("teacher_position")
        self.status_map = self._build_dict_lookup("teacher_status")

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
            raise ValueError("教师导入模板表头不匹配，请先下载系统模板。")

        success_rows = 0
        failed_rows = 0
        skipped_rows = 0
        created_rows = 0
        updated_rows = 0
        row_errors: list[RowError] = []

        for row_number, row_values in rows:
            savepoint = self.session.begin_nested()
            try:
                payload = self._parse_row(row_values)
                existing = get_teacher_by_no(self.session, payload.teacher_no)
                if existing:
                    if strategy == "create":
                        raise ValueError(f"工号 {payload.teacher_no} 已存在")
                    if strategy == "skip_existing":
                        savepoint.rollback()
                        skipped_rows += 1
                        continue
                    self._apply(existing, payload)
                    updated_rows += 1
                else:
                    teacher = Teacher(teacher_no=payload.teacher_no, name=payload.name)
                    self.session.add(teacher)
                    self.session.flush()
                    self._apply(teacher, payload)
                    created_rows += 1
                savepoint.commit()
                success_rows += 1
            except Exception as exc:
                if savepoint.is_active:
                    savepoint.rollback()
                failed_rows += 1
                row_errors.append(build_row_error(row_number=row_number, values=row_values, message=str(exc)))

        error_report_path = save_error_report(
            settings=self.settings,
            prefix="teacher_import_errors",
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
            skipped_rows=skipped_rows,
            created_rows=created_rows,
            updated_rows=updated_rows,
            error_report_path=error_report_path,
            error_preview=build_error_preview(row_errors),
            message=f"教师导入完成，成功 {success_rows} 条，失败 {failed_rows} 条。",
        )

    def _parse_row(self, row: dict[str, object]) -> TeacherImportPayload:
        teacher_no = clean_text(row.get("工号"))
        name = clean_text(row.get("姓名"))
        if not teacher_no:
            raise ValueError("工号不能为空")
        if not name:
            raise ValueError("姓名不能为空")

        subject_text = clean_text(row.get("学科"))
        subject = self.subject_map.get(subject_text) if subject_text else None
        if subject_text and subject is None:
            raise ValueError(f"学科不存在: {subject_text}")

        return TeacherImportPayload(
            teacher_no=teacher_no,
            name=name,
            gender=clean_text(row.get("性别")),
            subject_id=subject.id if subject else None,
            phone=clean_text(row.get("联系方式")),
            title_code=self._map_dict_value("职称", row.get("职称"), self.title_map),
            position_code=self._map_dict_value("岗位", row.get("岗位"), self.position_map),
            is_head_teacher=parse_bool(row.get("是否班主任")) or False,
            employment_status=self._map_dict_value("任教状态", row.get("任教状态"), self.status_map),
            entry_date=parse_date(row.get("入职日期")),
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

    def _apply(self, teacher: Teacher, payload: TeacherImportPayload) -> None:
        teacher.teacher_no = payload.teacher_no
        teacher.name = payload.name
        teacher.gender = payload.gender
        teacher.subject_id = payload.subject_id
        teacher.phone = payload.phone
        teacher.title_code = payload.title_code
        teacher.position_code = payload.position_code
        teacher.is_head_teacher = payload.is_head_teacher
        teacher.employment_status = payload.employment_status
        teacher.entry_date = payload.entry_date
        teacher.note = payload.note
