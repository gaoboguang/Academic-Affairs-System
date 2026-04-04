from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.importers.base import RowError, read_template_rows, save_error_report
from app.models import Exam, ExamSubject, ScoreImportBatch, ScoreRecord, Student, Subject
from app.schemas.common import ImportResult
from app.utils.parsers import clean_text


@dataclass
class ScoreImportPayload:
    student_id: int
    student_name: str
    subject_id: int
    score: float | None
    score_status: str
    raw_text: str | None
    note: str | None


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

    def __init__(self, session: Session, settings: Settings, exam: Exam) -> None:
        self.session = session
        self.settings = settings
        self.exam = exam
        self.student_map = {
            item.student_no: item
            for item in session.scalars(select(Student)).all()
        }
        self.subject_map = {}
        self.exam_subject_map: dict[int, ExamSubject] = {}
        for item in session.scalars(
            select(ExamSubject).where(ExamSubject.exam_id == exam.id, ExamSubject.is_active.is_(True))
        ).all():
            self.exam_subject_map[item.subject_id] = item
            subject = session.get(Subject, item.subject_id)
            if subject:
                self.subject_map[subject.code] = subject
                self.subject_map[subject.name] = subject

    def execute(
        self,
        *,
        filename: str | None,
        content: bytes,
        strategy: str,
        batch: ScoreImportBatch,
    ) -> ImportResult:
        headers, rows = read_template_rows(content)
        if headers[: len(self.expected_headers)] != self.expected_headers:
            raise ValueError("成绩导入模板表头不匹配，请先下载系统模板。")

        success_rows = 0
        failed_rows = 0
        skipped_rows = 0
        row_errors: list[RowError] = []
        seen_keys: set[tuple[int, int]] = set()

        for row_number, row_values in rows:
            try:
                payload = self._parse_row(row_values)
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
                        skipped_rows += 1
                        continue
                    self._apply(existing, payload, batch.id)
                else:
                    record = ScoreRecord(
                        exam_id=self.exam.id,
                        student_id=payload.student_id,
                        subject_id=payload.subject_id,
                    )
                    self.session.add(record)
                    self.session.flush()
                    self._apply(record, payload, batch.id)

                success_rows += 1
            except Exception as exc:
                failed_rows += 1
                row_errors.append(RowError(row_number=row_number, values=row_values, message=str(exc)))

        error_report_path = save_error_report(
            settings=self.settings,
            prefix="score_import_errors",
            headers=self.expected_headers,
            errors=row_errors,
        )
        return ImportResult(
            total_rows=len(rows),
            success_rows=success_rows,
            failed_rows=failed_rows,
            skipped_rows=skipped_rows,
            error_report_path=error_report_path,
            message=f"成绩导入完成，成功 {success_rows} 条，失败 {failed_rows} 条。",
        )

    def _parse_row(self, row: dict[str, object]) -> ScoreImportPayload:
        exam_name = clean_text(row.get("考试名称"))
        if exam_name and exam_name != self.exam.name:
            raise ValueError(f"考试名称不匹配: {exam_name}")

        student_no = clean_text(row.get("学号"))
        student_name = clean_text(row.get("姓名"))
        class_name = clean_text(row.get("班级"))
        subject_text = clean_text(row.get("科目"))
        score_text = clean_text(row.get("分数"))
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
        if class_name and student.current_class and student.current_class.name != class_name:
            raise ValueError(f"学生当前班级不匹配: {student_no}")

        subject = self.subject_map.get(subject_text)
        if subject is None or subject.id not in self.exam_subject_map:
            raise ValueError(f"考试未配置科目: {subject_text}")

        exam_subject = self.exam_subject_map[subject.id]
        if absent_flag:
            return ScoreImportPayload(
                student_id=student.id,
                student_name=student.name,
                subject_id=subject.id,
                score=None,
                score_status="absent",
                raw_text=absent_flag,
                note=note,
            )

        if score_text is None:
            raise ValueError("分数不能为空")
        try:
            score_value = float(score_text)
        except ValueError as exc:
            raise ValueError(f"分数格式错误: {score_text}") from exc
        if score_value < 0:
            raise ValueError("分数不能为负数")
        if score_value > exam_subject.full_score:
            raise ValueError(f"分数超过满分 {exam_subject.full_score}")

        return ScoreImportPayload(
            student_id=student.id,
            student_name=student.name,
            subject_id=subject.id,
            score=round(score_value, 2),
            score_status="normal",
            raw_text=score_text,
            note=note,
        )

    def _apply(self, record: ScoreRecord, payload: ScoreImportPayload, batch_id: int) -> None:
        record.score = payload.score
        record.score_status = payload.score_status
        record.raw_text = payload.raw_text
        record.import_batch_id = batch_id
        record.note = payload.note

