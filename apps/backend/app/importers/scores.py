from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.score_contexts import ScoreContextInput, safe_float, safe_int, upsert_exam_student_context
from app.core.config import Settings
from app.importers.base import (
    RowError,
    build_error_preview,
    build_row_error,
    read_template_rows,
    resolve_import_status,
    save_error_report,
)
from app.importers.score_layouts import ScoreImportMapping, ScoreLayoutAdapter
from app.models import Exam, ExamSubject, ScoreImportBatch, ScoreRecord, Student, Subject
from app.schemas.common import ImportResult
from app.utils.parsers import clean_text


@dataclass
class ScoreImportPayload:
    student: Student
    student_id: int
    student_name: str
    subject_id: int
    score: float | None
    original_score: float | None
    converted_score: float | None
    score_value_type: str
    score_status: str
    raw_text: str | None
    note: str | None
    source_class_name: str | None = None
    source_student_no: str | None = None
    source_exam_no: str | None = None
    source_total_score: float | None = None
    source_class_rank: int | None = None
    source_school_rank: int | None = None
    source_grade_rank: int | None = None
    source_row_number: int | None = None
    raw_meta_json: dict | None = None


class ScoreImporter:
    expected_headers = [
        "考试名称",
        "学号",
        "姓名",
        "班级",
        "科目",
        "分数",
        "缺考标记",
        "备注",
    ]

    def __init__(
        self,
        session: Session,
        settings: Settings,
        exam: Exam,
        *,
        allowed_class_ids: set[int] | None = None,
    ) -> None:
        self.session = session
        self.settings = settings
        self.exam = exam
        self.allowed_class_ids = allowed_class_ids
        self.student_map = {
            item.student_no: item
            for item in session.scalars(select(Student)).all()
        }
        self.subject_map = {}
        self.exam_subject_map: dict[int, ExamSubject] = {}
        self.last_detection_summary: dict | None = None
        for item in session.scalars(
            select(ExamSubject).where(ExamSubject.exam_id == exam.id, ExamSubject.is_active.is_(True))
        ).all():
            self.exam_subject_map[item.subject_id] = item
            subject = session.get(Subject, item.subject_id)
            if subject:
                for alias in _build_subject_aliases(subject):
                    self.subject_map[alias] = subject

    def execute(
        self,
        *,
        filename: str | None,
        content: bytes,
        strategy: str,
        batch: ScoreImportBatch,
        mapping: ScoreImportMapping | None = None,
    ) -> ImportResult:
        self.last_detection_summary = None
        if mapping is None:
            headers, rows = read_template_rows(content)
            if headers[: len(self.expected_headers)] != self.expected_headers:
                raise ValueError("成绩导入模板表头不匹配，请先下载系统模板。")
            self.last_detection_summary = {
                "layout_type": "standard",
                "source_row_count": len(rows),
                "normalized_record_count": len(rows),
            }
        else:
            headers, rows, self.last_detection_summary = ScoreLayoutAdapter(self.session, self.exam).normalize_content(
                filename=filename,
                content=content,
                mapping=mapping,
            )

        success_rows = 0
        failed_rows = 0
        skipped_rows = 0
        created_rows = 0
        updated_rows = 0
        row_errors: list[RowError] = []
        seen_keys: set[tuple[int, int]] = set()
        quality_counts = {
            "absent": 0,
            "invalid_score": 0,
            "duplicate": 0,
            "unmatched_student": 0,
            "unmatched_subject": 0,
            "identity_conflict": 0,
        }

        for row_number, row_values in rows:
            try:
                payload = self._parse_row(row_values, row_number=row_number)
                if payload.score_status == "absent":
                    quality_counts["absent"] += 1
                dedupe_key = (payload.student_id, payload.subject_id)
                if dedupe_key in seen_keys:
                    raise ValueError("同一学生同一科目在导入文件中重复出现")
                seen_keys.add(dedupe_key)

                existing = self.session.scalar(
                    select(ScoreRecord).where(
                        ScoreRecord.exam_id == self.exam.id,
                        ScoreRecord.student_id == payload.student_id,
                        ScoreRecord.subject_id == payload.subject_id,
                    )
                )
                if existing:
                    if strategy == "skip_existing":
                        self._upsert_context(payload)
                        skipped_rows += 1
                        continue
                    self._apply(existing, payload, batch.id)
                    updated_rows += 1
                else:
                    record = ScoreRecord(
                        exam_id=self.exam.id,
                        student_id=payload.student_id,
                        subject_id=payload.subject_id,
                    )
                    self.session.add(record)
                    self.session.flush()
                    self._apply(record, payload, batch.id)
                    created_rows += 1

                self._upsert_context(payload)
                success_rows += 1
            except Exception as exc:
                failed_rows += 1
                _record_score_quality_issue(quality_counts, str(exc))
                row_errors.append(build_row_error(row_number=row_number, values=row_values, message=str(exc)))

        error_report_path = save_error_report(
            settings=self.settings,
            prefix="score_import_errors",
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
            notice_preview=_build_score_quality_notice(quality_counts),
            message=f"成绩导入完成，成功 {success_rows} 条，失败 {failed_rows} 条。",
        )

    def _parse_row(self, row: dict[str, object], *, row_number: int | None = None) -> ScoreImportPayload:
        exam_name = clean_text(row.get("考试名称"))
        if exam_name and exam_name != self.exam.name:
            raise ValueError(f"考试名称不匹配: {exam_name}")

        student_no = clean_text(row.get("学号"))
        student_name = clean_text(row.get("姓名"))
        class_name = clean_text(row.get("班级"))
        subject_text = clean_text(row.get("科目"))
        score_text = clean_text(row.get("分数"))
        original_score_text = clean_text(row.get("原始分"))
        converted_score_text = clean_text(row.get("赋分"))
        score_value_type = _normalize_score_value_type(clean_text(row.get("成绩口径")))
        absent_flag = clean_text(row.get("缺考标记"))
        note = clean_text(row.get("备注"))

        if not student_no:
            raise ValueError("学号不能为空")
        if not student_name:
            raise ValueError("姓名不能为空")
        if not subject_text:
            raise ValueError("科目不能为空")

        student = self.student_map.get(student_no)
        if student is None:
            raise ValueError(f"学号不存在: {student_no}")
        if student.name != student_name:
            raise ValueError(f"学号与姓名不匹配: {student_no}")
        if self.allowed_class_ids is not None and student.current_class_id not in self.allowed_class_ids:
            raise ValueError("无权导入该学生成绩")
        subject = self.subject_map.get(subject_text)
        if subject is None or subject.id not in self.exam_subject_map:
            raise ValueError(f"考试未配置科目: {subject_text}")

        exam_subject = self.exam_subject_map[subject.id]
        if absent_flag:
            return ScoreImportPayload(
                student=student,
                student_id=student.id,
                student_name=student.name,
                subject_id=subject.id,
                score=None,
                original_score=None,
                converted_score=None,
                score_value_type=score_value_type,
                score_status="absent",
                raw_text=absent_flag,
                note=note,
                **self._parse_context_fields(row, student, class_name, row_number),
            )

        original_score = _parse_optional_score(original_score_text, field_name="原始分")
        converted_score = _parse_optional_score(converted_score_text, field_name="赋分")
        score_value = _select_display_score(
            score_text=score_text,
            original_score=original_score,
            converted_score=converted_score,
            score_value_type=score_value_type,
        )
        if score_value is None:
            raise ValueError("分数不能为空")
        _validate_score_value(score_value, exam_subject.full_score, field_name="分数")
        if original_score is not None:
            _validate_score_value(original_score, exam_subject.full_score, field_name="原始分")
        if converted_score is not None:
            _validate_score_value(converted_score, exam_subject.full_score, field_name="赋分")
        if score_value_type == "converted" and converted_score is None:
            converted_score = score_value
        elif score_value_type != "converted" and original_score is None:
            original_score = score_value
        if converted_score is not None:
            score_value_type = "converted"
        else:
            score_value_type = "original"

        return ScoreImportPayload(
            student=student,
            student_id=student.id,
            student_name=student.name,
            subject_id=subject.id,
            score=round(score_value, 2),
            original_score=round(original_score, 2) if original_score is not None else None,
            converted_score=round(converted_score, 2) if converted_score is not None else None,
            score_value_type=score_value_type,
            score_status="normal",
            raw_text=score_text,
            note=note,
            **self._parse_context_fields(row, student, class_name, row_number),
        )

    def _apply(self, record: ScoreRecord, payload: ScoreImportPayload, batch_id: int) -> None:
        record.score = payload.score
        record.original_score = payload.original_score
        record.converted_score = payload.converted_score
        record.score_value_type = payload.score_value_type
        record.score_status = payload.score_status
        record.raw_text = payload.raw_text
        record.import_batch_id = batch_id
        record.note = payload.note

    def _parse_context_fields(
        self,
        row: dict[str, object],
        student: Student,
        class_name: str | None,
        row_number: int | None,
    ) -> dict:
        source_class_name = clean_text(row.get("源班级")) or class_name
        source_student_no = (
            clean_text(row.get("源学籍号"))
            or clean_text(row.get("源学号"))
            or clean_text(row.get("新教育号"))
        )
        source_exam_no = (
            clean_text(row.get("考生号"))
            or clean_text(row.get("源考号"))
            or clean_text(row.get("准考证号"))
        )
        source_total_score = safe_float(row.get("源总分") or row.get("总分"))
        source_class_rank = safe_int(row.get("源班级名次") or row.get("班级名次") or row.get("班名次"))
        source_school_rank = safe_int(
            row.get("源学校名次") or row.get("学校名次") or row.get("校名次") or row.get("年级名次")
        )
        source_grade_rank = safe_int(row.get("源年级名次") or row.get("年级名次"))
        raw_meta_json = {
            key: value
            for key, value in {
                "源班级": source_class_name,
                "源学籍号": source_student_no,
                "考生号": source_exam_no,
                "源总分": source_total_score,
                "源班级名次": source_class_rank,
                "源学校名次": source_school_rank,
            }.items()
            if value not in (None, "")
        }
        if class_name and student.current_class and student.current_class.name != class_name:
            raw_meta_json["当前班级"] = student.current_class.name
        return {
            "source_class_name": source_class_name,
            "source_student_no": source_student_no,
            "source_exam_no": source_exam_no,
            "source_total_score": source_total_score,
            "source_class_rank": source_class_rank,
            "source_school_rank": source_school_rank,
            "source_grade_rank": source_grade_rank,
            "source_row_number": row_number,
            "raw_meta_json": raw_meta_json or None,
        }

    def _upsert_context(self, payload: ScoreImportPayload) -> None:
        upsert_exam_student_context(
            self.session,
            self.exam,
            ScoreContextInput(
                student=payload.student,
                source_class_name=payload.source_class_name,
                source_student_no=payload.source_student_no,
                source_exam_no=payload.source_exam_no,
                source_total_score=payload.source_total_score,
                source_class_rank=payload.source_class_rank,
                source_school_rank=payload.source_school_rank,
                source_grade_rank=payload.source_grade_rank,
                source_row_number=payload.source_row_number,
                raw_meta_json=payload.raw_meta_json,
                note=payload.note,
            ),
        )


def _record_score_quality_issue(counts: dict[str, int], message: str) -> None:
    if "同一学生同一科目" in message:
        counts["duplicate"] += 1
    if "学号不存在" in message:
        counts["unmatched_student"] += 1
    if "学号与姓名不匹配" in message or "学生当前班级不匹配" in message:
        counts["identity_conflict"] += 1
    if "考试未配置科目" in message:
        counts["unmatched_subject"] += 1
    if "格式错误" in message or "不能为负数" in message or "超过满分" in message:
        counts["invalid_score"] += 1


def _normalize_score_value_type(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    if normalized in {"converted", "afterconversion", "赋分", "赋分后", "等级分", "等级成绩"}:
        return "converted"
    return "original"


def _parse_optional_score(value: str | None, *, field_name: str) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{field_name}格式错误: {value}") from exc


def _select_display_score(
    *,
    score_text: str | None,
    original_score: float | None,
    converted_score: float | None,
    score_value_type: str,
) -> float | None:
    if converted_score is not None:
        return converted_score
    if score_text is not None:
        try:
            score_value = float(score_text)
        except ValueError as exc:
            raise ValueError(f"分数格式错误: {score_text}") from exc
        return score_value
    if score_value_type == "converted" and converted_score is not None:
        return converted_score
    return original_score


def _validate_score_value(value: float, full_score: float, *, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name}不能为负数")
    if value > full_score:
        raise ValueError(f"{field_name}超过满分 {full_score}")


def _build_score_quality_notice(counts: dict[str, int]) -> list[str]:
    summary = (
        "成绩导入质量摘要："
        f"缺考 {counts['absent']} 行，"
        f"非法分数 {counts['invalid_score']} 行，"
        f"重复成绩 {counts['duplicate']} 行，"
        f"未匹配学生 {counts['unmatched_student']} 行，"
        f"未匹配科目 {counts['unmatched_subject']} 行。"
    )
    notices = [summary]
    if counts["identity_conflict"]:
        notices.append(f"身份或班级不一致 {counts['identity_conflict']} 行，请优先核对学号、姓名和当前班级。")
    if counts["unmatched_student"]:
        notices.append("存在未匹配学生，请先在学生中心维护学生主档，或修正 Excel 中的学号。")
    if counts["unmatched_subject"]:
        notices.append("存在未匹配科目，请先在考试科目配置中勾选对应科目。")
    if counts["invalid_score"]:
        notices.append("存在非法分数，请核对分数是否为数字、非负数且不超过该科满分。")
    return notices


def _build_subject_aliases(subject: Subject) -> set[str]:
    aliases = {subject.code, subject.name}
    extras = {
        "politics": {"思想政治", "道法", "道德与法治"},
        "english": {"外语", "英语听说"},
        "biology": {"生物学"},
    }
    aliases.update(extras.get(subject.code, set()))
    return {alias for alias in aliases if alias}
