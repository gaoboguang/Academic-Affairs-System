from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.importers.base import RowError, build_error_preview, build_row_error, read_template_rows, resolve_import_status, save_error_report
from app.models import AttendanceRecord, BehaviorRecord, Student
from app.schemas.common import ImportResult
from app.utils.parsers import clean_text, parse_date, parse_int


ATTENDANCE_STATUSES = {"正常", "迟到", "早退", "病假", "事假", "旷课", "其他"}
BEHAVIOR_CATEGORIES = {"表扬", "违纪", "谈话", "心理关注", "安全事件", "奖惩", "其他"}
BEHAVIOR_SEVERITIES = {"低", "中", "高", "严重"}


@dataclass
class AttendanceImportPayload:
    student: Student
    record_date: date
    scope: str
    period_index: int
    status: str
    reason: str | None
    note: str | None


@dataclass
class BehaviorImportPayload:
    student: Student
    record_date: date
    category: str
    severity: str
    title: str
    description: str | None
    handler_name: str | None
    points_delta: float | None
    attachment_path: str | None


class AttendanceImporter:
    expected_headers = ["学号", "姓名", "日期", "范围", "节次", "状态", "原因", "备注"]
    header_aliases = {
        "学生学号": "学号",
        "学生姓名": "姓名",
        "考勤日期": "日期",
        "考勤范围": "范围",
        "第几节": "节次",
        "考勤状态": "状态",
    }

    def __init__(self, session: Session, settings: Settings, *, source_batch_id: int | None = None) -> None:
        self.session = session
        self.settings = settings
        self.source_batch_id = source_batch_id
        self.student_by_no = {item.student_no: item for item in session.scalars(select(Student)).all()}

    def execute(self, *, filename: str | None, content: bytes) -> ImportResult:
        headers, rows = read_template_rows(content)
        normalized_headers = [self._normalize_header(header) for header in headers]
        if normalized_headers[: len(self.expected_headers)] != self.expected_headers:
            raise ValueError(_build_header_mismatch_message("考勤导入模板", headers, normalized_headers, self.expected_headers))

        success_rows = 0
        failed_rows = 0
        updated_rows = 0
        created_rows = 0
        row_errors: list[RowError] = []

        for row_number, row_values in rows:
            normalized_row = {
                self._normalize_header(header): value
                for header, value in row_values.items()
            }
            try:
                payload = self._parse_row(normalized_row)
                existing = self.session.scalar(
                    select(AttendanceRecord).where(
                        AttendanceRecord.student_id == payload.student.id,
                        AttendanceRecord.record_date == payload.record_date,
                        AttendanceRecord.scope == payload.scope,
                        AttendanceRecord.period_index == payload.period_index,
                    )
                )
                if existing:
                    self._apply(existing, payload)
                    updated_rows += 1
                else:
                    existing = AttendanceRecord(
                        student_id=payload.student.id,
                        record_date=payload.record_date,
                        scope=payload.scope,
                        period_index=payload.period_index,
                        status=payload.status,
                        reason=payload.reason,
                        note=payload.note,
                        source_batch_id=self.source_batch_id,
                    )
                    self.session.add(existing)
                    created_rows += 1
                success_rows += 1
            except Exception as exc:
                failed_rows += 1
                row_errors.append(build_row_error(row_number=row_number, values=row_values, message=str(exc)))

        error_report_path = save_error_report(
            settings=self.settings,
            prefix="attendance_import_errors",
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
            created_rows=created_rows,
            updated_rows=updated_rows,
            error_report_path=error_report_path,
            error_preview=build_error_preview(row_errors),
            notice_preview=_build_counter_notices(row_errors),
            message=f"考勤导入完成，成功 {success_rows} 条，失败 {failed_rows} 条，覆盖更新 {updated_rows} 条。",
        )

    @classmethod
    def _normalize_header(cls, header: str) -> str:
        return cls.header_aliases.get(header, header)

    def _parse_row(self, row: dict[str, Any]) -> AttendanceImportPayload:
        student = _resolve_student(self.student_by_no, row)
        record_date = parse_date(row.get("日期"))
        if not record_date:
            raise ValueError("日期不能为空")

        period_index = parse_int(row.get("节次")) or 0
        scope = _normalize_attendance_scope(clean_text(row.get("范围")), period_index)
        if scope == "period" and period_index <= 0:
            raise ValueError("节次不能为空")

        status = clean_text(row.get("状态")) or "正常"
        if status not in ATTENDANCE_STATUSES:
            raise ValueError(f"状态无法识别: {status}")

        return AttendanceImportPayload(
            student=student,
            record_date=record_date,
            scope=scope,
            period_index=period_index,
            status=status,
            reason=clean_text(row.get("原因")),
            note=clean_text(row.get("备注")),
        )

    def _apply(self, item: AttendanceRecord, payload: AttendanceImportPayload) -> None:
        item.student_id = payload.student.id
        item.record_date = payload.record_date
        item.scope = payload.scope
        item.period_index = payload.period_index
        item.status = payload.status
        item.reason = payload.reason
        item.note = payload.note
        item.source_batch_id = self.source_batch_id
        item.is_active = True


class BehaviorImporter:
    expected_headers = ["学号", "姓名", "日期", "类型", "严重度", "标题", "说明", "处理人", "分值变化", "附件路径"]
    header_aliases = {
        "学生学号": "学号",
        "学生姓名": "姓名",
        "行为日期": "日期",
        "行为类型": "类型",
        "事件标题": "标题",
        "事件说明": "说明",
        "处理教师": "处理人",
        "分数变化": "分值变化",
    }

    def __init__(self, session: Session, settings: Settings, *, source_batch_id: int | None = None) -> None:
        self.session = session
        self.settings = settings
        self.source_batch_id = source_batch_id
        self.student_by_no = {item.student_no: item for item in session.scalars(select(Student)).all()}

    def execute(self, *, filename: str | None, content: bytes) -> ImportResult:
        headers, rows = read_template_rows(content)
        normalized_headers = [self._normalize_header(header) for header in headers]
        if normalized_headers[: len(self.expected_headers)] != self.expected_headers:
            raise ValueError(_build_header_mismatch_message("行为导入模板", headers, normalized_headers, self.expected_headers))

        success_rows = 0
        failed_rows = 0
        skipped_rows = 0
        row_errors: list[RowError] = []
        duplicate_counter: Counter[str] = Counter()
        seen_keys: set[tuple[int, date, str, str]] = set()

        for row_number, row_values in rows:
            normalized_row = {
                self._normalize_header(header): value
                for header, value in row_values.items()
            }
            try:
                payload = self._parse_row(normalized_row)
                key = (payload.student.id, payload.record_date, payload.category, payload.title)
                if key in seen_keys:
                    duplicate_counter[f"{payload.student.name}/{payload.record_date}/{payload.category}/{payload.title}"] += 1
                    skipped_rows += 1
                    continue
                seen_keys.add(key)
                self.session.add(
                    BehaviorRecord(
                        student_id=payload.student.id,
                        record_date=payload.record_date,
                        category=payload.category,
                        severity=payload.severity,
                        title=payload.title,
                        description=payload.description,
                        handler_name=payload.handler_name,
                        points_delta=payload.points_delta,
                        attachment_path=payload.attachment_path,
                        source_batch_id=self.source_batch_id,
                    )
                )
                success_rows += 1
            except Exception as exc:
                failed_rows += 1
                row_errors.append(build_row_error(row_number=row_number, values=row_values, message=str(exc)))

        error_report_path = save_error_report(
            settings=self.settings,
            prefix="behavior_import_errors",
            headers=self.expected_headers,
            errors=row_errors,
        )
        notices = _build_counter_notices(row_errors)
        if duplicate_counter:
            preview = "，".join(f"{key}（{count + 1} 行）" for key, count in duplicate_counter.most_common(3))
            notices.append(f"同一文件内重复行为已跳过：{preview}。")
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
            created_rows=success_rows,
            error_report_path=error_report_path,
            error_preview=build_error_preview(row_errors),
            notice_preview=notices,
            message=f"行为导入完成，新增 {success_rows} 条，跳过重复 {skipped_rows} 条，失败 {failed_rows} 条。",
        )

    @classmethod
    def _normalize_header(cls, header: str) -> str:
        return cls.header_aliases.get(header, header)

    def _parse_row(self, row: dict[str, Any]) -> BehaviorImportPayload:
        student = _resolve_student(self.student_by_no, row)
        record_date = parse_date(row.get("日期"))
        if not record_date:
            raise ValueError("日期不能为空")

        category = clean_text(row.get("类型")) or "其他"
        if category not in BEHAVIOR_CATEGORIES:
            raise ValueError(f"类型无法识别: {category}")

        severity = _normalize_behavior_severity(clean_text(row.get("严重度")))
        title = clean_text(row.get("标题"))
        if not title:
            raise ValueError("标题不能为空")

        points_delta = _parse_float(row.get("分值变化"))
        return BehaviorImportPayload(
            student=student,
            record_date=record_date,
            category=category,
            severity=severity,
            title=title,
            description=clean_text(row.get("说明")),
            handler_name=clean_text(row.get("处理人")),
            points_delta=points_delta,
            attachment_path=clean_text(row.get("附件路径")),
        )


def _resolve_student(student_by_no: dict[str, Student], row: dict[str, Any]) -> Student:
    student_no = clean_text(row.get("学号"))
    if not student_no:
        raise ValueError("学号不能为空")
    student = student_by_no.get(student_no)
    if not student:
        raise ValueError(f"学号不存在: {student_no}")
    row_name = clean_text(row.get("姓名"))
    if row_name and row_name != student.name:
        raise ValueError(f"姓名不匹配: {row_name}")
    return student


def _normalize_attendance_scope(value: str | None, period_index: int) -> str:
    if not value:
        return "period" if period_index > 0 else "day"
    mapping = {
        "日": "day",
        "全天": "day",
        "天": "day",
        "day": "day",
        "节次": "period",
        "课节": "period",
        "第几节": "period",
        "period": "period",
    }
    normalized = mapping.get(value)
    if not normalized:
        raise ValueError(f"范围无法识别: {value}")
    return normalized


def _normalize_behavior_severity(value: str | None) -> str:
    if not value:
        return "中"
    mapping = {
        "轻微": "低",
        "低": "低",
        "一般": "中",
        "中": "中",
        "中等": "中",
        "较重": "高",
        "高": "高",
        "严重": "严重",
        "重大": "严重",
    }
    normalized = mapping.get(value)
    if not normalized or normalized not in BEHAVIOR_SEVERITIES:
        raise ValueError(f"严重度无法识别: {value}")
    return normalized


def _parse_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    return float(text)


def _build_header_mismatch_message(
    template_name: str,
    headers: list[str],
    normalized_headers: list[str],
    expected_headers: list[str],
) -> str:
    mismatches: list[str] = []
    for index, expected in enumerate(expected_headers):
        actual = headers[index] if index < len(headers) else ""
        actual_normalized = normalized_headers[index] if index < len(normalized_headers) else ""
        if actual_normalized == expected:
            continue
        mismatches.append(f"第 {index + 1} 列应为“{expected}”，实际为“{actual or '空'}”")
        if len(mismatches) >= 4:
            break
    detail = "；".join(mismatches) if mismatches else "表头顺序或字段不符合模板要求"
    return f"{template_name}表头不匹配：{detail}。请先下载系统模板。"


def _build_counter_notices(row_errors: list[RowError]) -> list[str]:
    counters: dict[str, Counter[str]] = {
        "学号待核对": Counter(),
        "状态待核对": Counter(),
        "类型待核对": Counter(),
        "严重度待核对": Counter(),
    }
    for item in row_errors:
        for label, prefix in [
            ("学号待核对", "学号不存在: "),
            ("状态待核对", "状态无法识别: "),
            ("类型待核对", "类型无法识别: "),
            ("严重度待核对", "严重度无法识别: "),
        ]:
            if item.message.startswith(prefix):
                counters[label][item.message.removeprefix(prefix)] += 1

    notices: list[str] = []
    for label, counter in counters.items():
        if not counter:
            continue
        preview = "，".join(f"{value}（{count} 行）" for value, count in counter.most_common(3))
        notices.append(f"{label}：{preview}。")
    return notices
