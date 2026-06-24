from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.knowledge import (
    rebuild_score_knowledge_snapshots,
    replace_question_knowledge_points,
    upsert_question,
)
from app.core.config import Settings
from app.importers.base import (
    RowError,
    build_error_preview,
    build_row_error,
    read_template_rows,
    resolve_import_status,
    save_error_report,
)
from app.models import Exam, ExamSubject, ScoreQuestionImportBatch, ScoreQuestionRecord, Student, Subject
from app.schemas.common import ImportResult
from app.services import knowledge_base
from app.utils.parsers import clean_text


@dataclass
class ScoreQuestionPayload:
    student_id: int
    subject_id: int
    question_id: int
    score: float | None
    score_status: str
    raw_text: str | None
    error_tags: list[dict[str, object]]
    error_note: str | None
    note: str | None


class ScoreQuestionImporter:
    expected_headers = [
        "考试名称",
        "学号",
        "姓名",
        "科目",
        "题号",
        "题目满分",
        "学生得分",
        "知识点",
        "题型",
        "能力层级",
        "错因标签",
        "错因备注",
        "备注",
    ]

    def __init__(self, session: Session, settings: Settings, exam: Exam) -> None:
        self.session = session
        self.settings = settings
        self.exam = exam
        self.student_map = {item.student_no: item for item in session.scalars(select(Student)).all()}
        self.subject_map: dict[str, Subject] = {}
        self.exam_subject_map: dict[int, ExamSubject] = {}
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
        content: bytes,
        batch: ScoreQuestionImportBatch,
        strategy: str = "overwrite",
    ) -> tuple[ImportResult, int]:
        headers, rows = read_template_rows(content)
        required_headers = self.expected_headers[:10]
        if headers[: len(required_headers)] != required_headers:
            raise ValueError("题分明细导入模板表头不匹配，请使用系统题分明细模板。")

        success_rows = 0
        failed_rows = 0
        skipped_rows = 0
        created_rows = 0
        updated_rows = 0
        row_errors: list[RowError] = []
        seen_keys: set[tuple[int, int]] = set()
        quality_counts = {
            "duplicate": 0,
            "unmatched_student": 0,
            "unmatched_subject": 0,
            "invalid_score": 0,
            "small_sample": 0,
            "error_tag": 0,
        }

        for row_number, row_values in rows:
            try:
                payload = self._parse_row(row_values, row_number=row_number)
                dedupe_key = (payload.student_id, payload.question_id)
                if dedupe_key in seen_keys:
                    raise ValueError("同一学生同一题号在导入文件中重复出现")
                seen_keys.add(dedupe_key)

                existing = self.session.scalar(
                    select(ScoreQuestionRecord).where(
                        ScoreQuestionRecord.exam_id == self.exam.id,
                        ScoreQuestionRecord.student_id == payload.student_id,
                        ScoreQuestionRecord.question_id == payload.question_id,
                    )
                )
                if existing:
                    if strategy == "skip_existing":
                        skipped_rows += 1
                        continue
                    self._apply(existing, payload, batch.id)
                    updated_rows += 1
                else:
                    record = ScoreQuestionRecord(
                        exam_id=self.exam.id,
                        student_id=payload.student_id,
                        subject_id=payload.subject_id,
                        question_id=payload.question_id,
                    )
                    self.session.add(record)
                    self.session.flush()
                    self._apply(record, payload, batch.id)
                    created_rows += 1
                success_rows += 1
            except Exception as exc:
                failed_rows += 1
                _record_question_quality_issue(quality_counts, str(exc))
                row_errors.append(build_row_error(row_number=row_number, values=row_values, message=str(exc)))

        error_report_path = save_error_report(
            settings=self.settings,
            prefix="score_question_import_errors",
            headers=headers,
            errors=row_errors,
        )
        snapshot_count = rebuild_score_knowledge_snapshots(self.session, self.exam.id) if success_rows else 0
        return (
            ImportResult(
                status=resolve_import_status(total_rows=len(rows), success_rows=success_rows, failed_rows=failed_rows),
                total_rows=len(rows),
                success_rows=success_rows,
                failed_rows=failed_rows,
                skipped_rows=skipped_rows,
                created_rows=created_rows,
                updated_rows=updated_rows,
                error_report_path=error_report_path,
                error_preview=build_error_preview(row_errors),
                notice_preview=_build_question_quality_notice(quality_counts, snapshot_count),
                message=f"题分明细导入完成，成功 {success_rows} 行，失败 {failed_rows} 行。",
            ),
            snapshot_count,
        )

    def _parse_row(self, row: dict[str, object], *, row_number: int) -> ScoreQuestionPayload:
        exam_name = clean_text(row.get("考试名称"))
        if exam_name and exam_name != self.exam.name:
            raise ValueError(f"考试名称不匹配: {exam_name}")

        student_no = clean_text(row.get("学号"))
        student_name = clean_text(row.get("姓名"))
        subject_text = clean_text(row.get("科目"))
        question_no = clean_text(row.get("题号"))
        full_score_text = clean_text(row.get("题目满分"))
        score_text = clean_text(row.get("学生得分"))
        knowledge_text = clean_text(row.get("知识点"))
        question_type = clean_text(row.get("题型"))
        ability_level = clean_text(row.get("能力层级"))
        error_tag_text = clean_text(row.get("错因标签"))
        error_note = clean_text(row.get("错因备注"))
        note = clean_text(row.get("备注"))

        if not student_no:
            raise ValueError("学号不能为空")
        if not student_name:
            raise ValueError("姓名不能为空")
        if not subject_text:
            raise ValueError("科目不能为空")
        if not question_no:
            raise ValueError("题号不能为空")
        if not full_score_text:
            raise ValueError("题目满分不能为空")
        if not knowledge_text:
            raise ValueError("知识点不能为空")

        student = self.student_map.get(student_no)
        if student is None:
            raise ValueError(f"学号不存在: {student_no}")
        if student.name != student_name:
            raise ValueError(f"学号与姓名不匹配: {student_no}")
        subject = self.subject_map.get(subject_text)
        if subject is None or subject.id not in self.exam_subject_map:
            raise ValueError(f"考试未配置科目: {subject_text}")

        full_score = _parse_score(full_score_text, field_name="题目满分")
        if full_score <= 0:
            raise ValueError("题目满分必须大于 0")
        score = _parse_optional_question_score(score_text, field_name="学生得分")
        if score is not None and (score < 0 or score > full_score):
            raise ValueError(f"学生得分必须在 0 到 {full_score:g} 之间")

        question = upsert_question(
            self.session,
            exam_id=self.exam.id,
            subject_id=subject.id,
            question_no=question_no,
            full_score=round(full_score, 4),
            question_type=question_type,
            ability_level=ability_level,
            sort_order=row_number,
        )
        knowledge_points = [
            knowledge_base.resolve_knowledge_point(self.session, subject.id, name)
            for name in _split_knowledge_points(knowledge_text)
        ]
        if not knowledge_points:
            raise ValueError("知识点不能为空")
        replace_question_knowledge_points(self.session, question.id, knowledge_points)
        error_tags = knowledge_base.ensure_error_tags_by_names(
            self.session,
            knowledge_base.split_error_tags(error_tag_text),
        )

        return ScoreQuestionPayload(
            student_id=student.id,
            subject_id=subject.id,
            question_id=question.id,
            score=round(score, 4) if score is not None else None,
            score_status="normal" if score is not None else "absent",
            raw_text=score_text,
            error_tags=error_tags,
            error_note=error_note,
            note=note,
        )

    def _apply(self, record: ScoreQuestionRecord, payload: ScoreQuestionPayload, batch_id: int) -> None:
        record.subject_id = payload.subject_id
        record.question_id = payload.question_id
        record.score = payload.score
        record.score_status = payload.score_status
        record.raw_text = payload.raw_text
        record.error_tags_json = payload.error_tags
        record.error_note = payload.error_note
        record.import_batch_id = batch_id
        record.note = payload.note
        record.is_active = True


def _parse_score(value: str, *, field_name: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{field_name}格式错误: {value}") from exc


def _parse_optional_question_score(value: str | None, *, field_name: str) -> float | None:
    if value in (None, ""):
        return None
    return _parse_score(value, field_name=field_name)


def _split_knowledge_points(value: str) -> list[str]:
    parts = re.split(r"[,，、;/；]+", value)
    return [part.strip() for part in parts if part.strip()]


def _record_question_quality_issue(counts: dict[str, int], message: str) -> None:
    if "重复" in message:
        counts["duplicate"] += 1
    if "学号不存在" in message:
        counts["unmatched_student"] += 1
    if "考试未配置科目" in message:
        counts["unmatched_subject"] += 1
    if "格式错误" in message or "必须" in message or "之间" in message:
        counts["invalid_score"] += 1


def _build_question_quality_notice(counts: dict[str, int], snapshot_count: int) -> list[str]:
    notices = [
        "题分明细导入质量摘要："
        f"重复题分 {counts['duplicate']} 行，"
        f"未匹配学生 {counts['unmatched_student']} 行，"
        f"未匹配科目 {counts['unmatched_subject']} 行，"
        f"非法题分 {counts['invalid_score']} 行，"
        f"重建知识点诊断 {snapshot_count} 条。"
    ]
    if counts["unmatched_student"]:
        notices.append("存在未匹配学生，请先在学生中心维护学生主档，或修正题分表中的学号。")
    if counts["unmatched_subject"]:
        notices.append("存在未匹配科目，请先在考试科目配置中维护对应科目。")
    if counts["invalid_score"]:
        notices.append("存在非法题分，请核对题目满分和学生得分是否为有效数字。")
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
