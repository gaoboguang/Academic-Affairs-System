from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Exam, SchoolClass, ScoreClassMapping, ScoreExamStudentContext, ScoreRecord, Student
from app.utils.parsers import clean_text


@dataclass
class ScoreContextInput:
    student: Student
    source_class_name: str | None = None
    source_student_no: str | None = None
    source_exam_no: str | None = None
    source_total_score: float | None = None
    source_class_rank: int | None = None
    source_school_rank: int | None = None
    source_grade_rank: int | None = None
    source_row_number: int | None = None
    raw_meta_json: dict[str, Any] | None = None
    note: str | None = None


def parse_score_note(note: str | None) -> dict[str, str]:
    text = clean_text(note)
    if not text:
        return {}
    result: dict[str, str] = {}
    for segment in text.split(";"):
        if ":" not in segment and "：" not in segment:
            continue
        key, value = segment.replace("：", ":", 1).split(":", 1)
        key = clean_text(key)
        value = clean_text(value)
        if key and value:
            result[key] = value
    return result


def safe_float(value: Any) -> float | None:
    text = clean_text(value)
    if text is None:
        return None
    try:
        return round(float(text), 2)
    except (TypeError, ValueError):
        return None


def safe_int(value: Any) -> int | None:
    text = clean_text(value)
    if text is None:
        return None
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return None


def load_exam_context_map(session: Session, exam_id: int) -> dict[int, ScoreExamStudentContext]:
    return {
        item.student_id: item
        for item in session.scalars(
            select(ScoreExamStudentContext)
            .options(joinedload(ScoreExamStudentContext.mapped_class))
            .where(
                ScoreExamStudentContext.exam_id == exam_id,
                ScoreExamStudentContext.is_active.is_(True),
            )
        ).all()
    }


def effective_class_id(student: Student | None, context: ScoreExamStudentContext | None) -> int | None:
    if context and context.mapped_class_id is not None:
        return context.mapped_class_id
    return student.current_class_id if student else None


def effective_class_name(student: Student | None, context: ScoreExamStudentContext | None) -> str | None:
    if context and context.mapped_class:
        return context.mapped_class.name
    if context and context.source_class_name:
        return context.source_class_name
    if student and student.current_class:
        return student.current_class.name
    return None


def ranking_class_key(student: Student | None, context: ScoreExamStudentContext | None) -> str | None:
    if context and context.source_class_name:
        return f"source:{context.source_class_name}"
    class_id = effective_class_id(student, context)
    if class_id is not None:
        return f"class:{class_id}"
    return None


def ensure_exam_student_contexts(session: Session, exam: Exam) -> dict[int, ScoreExamStudentContext]:
    existing_contexts = load_exam_context_map(session, exam.id)
    records = session.scalars(
        select(ScoreRecord)
        .options(
            joinedload(ScoreRecord.student).joinedload(Student.current_class),
            joinedload(ScoreRecord.student).joinedload(Student.current_grade),
        )
        .where(ScoreRecord.exam_id == exam.id, ScoreRecord.is_active.is_(True))
        .order_by(ScoreRecord.student_id.asc(), ScoreRecord.id.asc())
    ).all()

    first_record_by_student: dict[int, ScoreRecord] = {}
    for record in records:
        if record.student is None:
            continue
        first_record_by_student.setdefault(record.student_id, record)

    for record in first_record_by_student.values():
        if record.student is None:
            continue
        meta = parse_score_note(record.note)
        existing_context = existing_contexts.get(record.student_id)
        source_total_score = safe_float(meta.get("源总分") or meta.get("总分"))
        source_class_rank = safe_int(meta.get("源班级名次") or meta.get("班级名次") or meta.get("班名次"))
        source_school_rank = safe_int(
            meta.get("源学校名次") or meta.get("学校名次") or meta.get("年级名次") or meta.get("校名次")
        )
        source_grade_rank = safe_int(meta.get("源年级名次") or meta.get("年级名次"))
        source_class_name = (
            meta.get("源班级")
            or meta.get("班级")
            or (existing_context.source_class_name if existing_context else None)
            or (record.student.current_class.name if record.student.current_class else None)
        )
        payload = ScoreContextInput(
            student=record.student,
            source_class_name=source_class_name,
            source_student_no=meta.get("源学籍号") or meta.get("源学号") or meta.get("新教育号") or (existing_context.source_student_no if existing_context else None),
            source_exam_no=meta.get("考生号") or meta.get("考号") or meta.get("准考证号") or (existing_context.source_exam_no if existing_context else None),
            source_total_score=source_total_score if source_total_score is not None else (existing_context.source_total_score if existing_context else None),
            source_class_rank=source_class_rank if source_class_rank is not None else (existing_context.source_class_rank if existing_context else None),
            source_school_rank=source_school_rank if source_school_rank is not None else (existing_context.source_school_rank if existing_context else None),
            source_grade_rank=source_grade_rank if source_grade_rank is not None else (existing_context.source_grade_rank if existing_context else None),
            raw_meta_json=meta or (existing_context.raw_meta_json if existing_context else None),
            note=record.note or (existing_context.note if existing_context else None),
        )
        upsert_exam_student_context(session, exam, payload)

    session.flush()
    return load_exam_context_map(session, exam.id)


def upsert_exam_student_context(
    session: Session,
    exam: Exam,
    payload: ScoreContextInput,
) -> ScoreExamStudentContext:
    source_class_name = clean_text(payload.source_class_name)
    mapped_class_id, mapping_status = resolve_mapped_class_id(
        session,
        exam,
        source_class_name,
        fallback_class_id=payload.student.current_class_id,
    )
    context = session.scalar(
        select(ScoreExamStudentContext).where(
            ScoreExamStudentContext.exam_id == exam.id,
            ScoreExamStudentContext.student_id == payload.student.id,
        )
    )
    if context is None:
        context = ScoreExamStudentContext(
            exam_id=exam.id,
            student_id=payload.student.id,
        )
        session.add(context)

    context.source_class_name = source_class_name or context.source_class_name
    context.mapped_class_id = mapped_class_id
    context.source_student_no = clean_text(payload.source_student_no) or context.source_student_no
    context.source_exam_no = clean_text(payload.source_exam_no) or context.source_exam_no
    context.source_total_score = payload.source_total_score if payload.source_total_score is not None else context.source_total_score
    context.source_class_rank = payload.source_class_rank if payload.source_class_rank is not None else context.source_class_rank
    context.source_school_rank = payload.source_school_rank if payload.source_school_rank is not None else context.source_school_rank
    context.source_grade_rank = payload.source_grade_rank if payload.source_grade_rank is not None else context.source_grade_rank
    context.source_row_number = payload.source_row_number if payload.source_row_number is not None else context.source_row_number
    context.mapping_status = mapping_status
    context.raw_meta_json = _merge_meta(context.raw_meta_json, payload.raw_meta_json)
    context.note = clean_text(payload.note) or context.note
    context.is_active = True
    if source_class_name:
        upsert_score_class_mapping(session, exam, source_class_name, mapped_class_id, mapping_status)
    return context


def upsert_score_class_mapping(
    session: Session,
    exam: Exam,
    source_class_name: str,
    mapped_class_id: int | None,
    mapping_status: str,
    note: str | None = None,
) -> ScoreClassMapping:
    clean_source_class_name = clean_text(source_class_name) or source_class_name
    item = next(
        (
            pending
            for pending in session.new
            if isinstance(pending, ScoreClassMapping)
            and pending.exam_id == exam.id
            and pending.source_class_name == clean_source_class_name
        ),
        None,
    )
    if item is None:
        item = session.scalar(
            select(ScoreClassMapping).where(
                ScoreClassMapping.exam_id == exam.id,
                ScoreClassMapping.source_class_name == clean_source_class_name,
            )
        )
    if item is None:
        item = ScoreClassMapping(
            exam_id=exam.id,
            source_class_name=clean_source_class_name,
        )
        session.add(item)
    item.mapped_class_id = mapped_class_id
    item.mapping_status = mapping_status
    item.note = clean_text(note) or item.note
    item.is_active = True
    return item


def resolve_mapped_class_id(
    session: Session,
    exam: Exam,
    source_class_name: str | None,
    fallback_class_id: int | None = None,
) -> tuple[int | None, str]:
    source = clean_text(source_class_name)
    if source:
        existing = session.scalar(
            select(ScoreClassMapping).where(
                ScoreClassMapping.exam_id == exam.id,
                ScoreClassMapping.source_class_name == source,
                ScoreClassMapping.is_active.is_(True),
            )
        )
        if existing:
            return existing.mapped_class_id, existing.mapping_status

        classes = session.scalars(select(SchoolClass).where(SchoolClass.is_active.is_(True))).all()
        exact = [item for item in classes if item.name == source]
        if exact:
            return _prefer_scoped_class(exact, exam), "exact"

        suffix = _source_class_suffix(source)
        if suffix:
            candidates = [item for item in classes if _source_class_suffix(item.name) == suffix]
            if candidates:
                return _prefer_scoped_class(candidates, exam), "auto_mapped"

        return None, "unmapped"

    if fallback_class_id is not None:
        return fallback_class_id, "current_class_fallback"
    return None, "unmapped"


def _source_class_suffix(value: str) -> str | None:
    digits = "".join(ch for ch in value if ch.isdigit())
    if not digits:
        return None
    if len(digits) >= 2:
        return digits[-2:]
    return digits.zfill(2)


def _prefer_scoped_class(classes: list[SchoolClass], exam: Exam) -> int:
    scope = set(exam.grade_scope_json or [])
    if scope:
        scoped = [item for item in classes if item.grade_id in scope]
        if len(scoped) == 1:
            return scoped[0].id
        if scoped:
            return sorted(scoped, key=lambda item: item.id)[0].id
    return sorted(classes, key=lambda item: item.id)[0].id


def _merge_meta(existing: dict | None, incoming: dict[str, Any] | None) -> dict | None:
    if not existing and not incoming:
        return None
    merged = dict(existing or {})
    for key, value in (incoming or {}).items():
        if value not in (None, ""):
            merged[key] = value
    return merged
