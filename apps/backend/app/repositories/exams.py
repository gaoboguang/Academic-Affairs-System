from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Exam, ExamSubject, ScoreImportBatch, ScoreRecord, ScoreSubjectSnapshot, ScoreTotalSnapshot, Semester, Student


def build_exam_query(name: str | None = None, semester_id: int | None = None) -> Select[tuple[Exam]]:
    stmt = select(Exam).options(
        joinedload(Exam.semester).joinedload(Semester.academic_year),
        joinedload(Exam.subjects),
    )
    if name:
        stmt = stmt.where(Exam.name.contains(name))
    if semester_id:
        stmt = stmt.where(Exam.semester_id == semester_id)
    return stmt.order_by(Exam.exam_date.desc(), Exam.id.desc())


def list_exams(
    session: Session,
    *,
    page: int,
    page_size: int,
    name: str | None = None,
    semester_id: int | None = None,
) -> tuple[Sequence[Exam], int]:
    stmt = build_exam_query(name=name, semester_id=semester_id)
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = session.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).unique().all()
    return items, total


def get_exam(session: Session, exam_id: int) -> Exam | None:
    stmt = (
        select(Exam)
        .options(
            joinedload(Exam.semester).joinedload(Semester.academic_year),
            joinedload(Exam.subjects).joinedload(ExamSubject.subject),
        )
        .where(Exam.id == exam_id)
    )
    return session.scalar(stmt)


def list_exam_subjects(session: Session, exam_id: int) -> Sequence[ExamSubject]:
    stmt = (
        select(ExamSubject)
        .options(joinedload(ExamSubject.subject))
        .where(ExamSubject.exam_id == exam_id, ExamSubject.is_active.is_(True))
        .order_by(ExamSubject.sort_order, ExamSubject.id)
    )
    return session.scalars(stmt).all()


def get_previous_trend_exam(session: Session, exam: Exam) -> Exam | None:
    stmt = (
        select(Exam)
        .where(
            Exam.is_trend_enabled.is_(True),
            Exam.exam_date < exam.exam_date,
        )
        .order_by(Exam.exam_date.desc(), Exam.id.desc())
    )
    return session.scalar(stmt)


def get_score_records_for_exam(session: Session, exam_id: int) -> Sequence[ScoreRecord]:
    stmt = (
        select(ScoreRecord)
        .options(
            joinedload(ScoreRecord.student).joinedload(Student.current_class),
            joinedload(ScoreRecord.student).joinedload(Student.current_grade),
            joinedload(ScoreRecord.subject),
        )
        .where(ScoreRecord.exam_id == exam_id)
    )
    return session.scalars(stmt).all()


def get_total_snapshots_for_exam(session: Session, exam_id: int) -> Sequence[ScoreTotalSnapshot]:
    stmt = (
        select(ScoreTotalSnapshot)
        .options(joinedload(ScoreTotalSnapshot.student))
        .where(ScoreTotalSnapshot.exam_id == exam_id)
    )
    return session.scalars(stmt).all()


def get_subject_snapshots_for_exam(session: Session, exam_id: int) -> Sequence[ScoreSubjectSnapshot]:
    stmt = (
        select(ScoreSubjectSnapshot)
        .options(joinedload(ScoreSubjectSnapshot.student), joinedload(ScoreSubjectSnapshot.subject))
        .where(ScoreSubjectSnapshot.exam_id == exam_id)
    )
    return session.scalars(stmt).all()


def get_subject_snapshot_students_for_exam(session: Session, exam_id: int) -> Sequence[Student]:
    stmt = (
        select(Student)
        .join(ScoreSubjectSnapshot, ScoreSubjectSnapshot.student_id == Student.id)
        .where(ScoreSubjectSnapshot.exam_id == exam_id)
        .distinct()
    )
    return session.scalars(stmt).all()


def get_subject_ids_for_exam_students(
    session: Session,
    exam_id: int,
    student_ids: Sequence[int],
) -> Sequence[int]:
    if not student_ids:
        return []
    stmt = (
        select(ScoreSubjectSnapshot.subject_id)
        .where(
            ScoreSubjectSnapshot.exam_id == exam_id,
            ScoreSubjectSnapshot.student_id.in_(student_ids),
            ScoreSubjectSnapshot.score.is_not(None),
        )
        .distinct()
    )
    return session.scalars(stmt).all()


def get_subject_snapshots_for_exam_students(
    session: Session,
    exam_id: int,
    student_ids: Sequence[int],
) -> Sequence[ScoreSubjectSnapshot]:
    if not student_ids:
        return []
    stmt = (
        select(ScoreSubjectSnapshot)
        .options(joinedload(ScoreSubjectSnapshot.student), joinedload(ScoreSubjectSnapshot.subject))
        .where(
            ScoreSubjectSnapshot.exam_id == exam_id,
            ScoreSubjectSnapshot.student_id.in_(student_ids),
        )
    )
    return session.scalars(stmt).all()


def list_score_batches(session: Session, exam_id: int) -> Sequence[ScoreImportBatch]:
    stmt = (
        select(ScoreImportBatch)
        .where(ScoreImportBatch.exam_id == exam_id)
        .order_by(ScoreImportBatch.import_time.desc(), ScoreImportBatch.id.desc())
    )
    return session.scalars(stmt).all()
