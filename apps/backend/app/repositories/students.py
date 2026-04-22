from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import SchoolClass, Student, StudentAttachment, StudentCareerPreference


def build_student_query(
    *,
    student_no: str | None = None,
    name: str | None = None,
    grade_id: int | None = None,
    class_id: int | None = None,
    status: str | None = None,
    student_type: str | None = None,
    art_track: str | None = None,
) -> Select[tuple[Student]]:
    stmt = select(Student).options(
        joinedload(Student.current_grade),
        joinedload(Student.current_class),
        selectinload(Student.guardians),
    )
    if student_no:
        stmt = stmt.where(Student.student_no.contains(student_no))
    if name:
        stmt = stmt.where(Student.name.contains(name))
    if grade_id:
        stmt = stmt.where(Student.current_grade_id == grade_id)
    if class_id:
        stmt = stmt.where(Student.current_class_id == class_id)
    if status:
        stmt = stmt.where(Student.status == status)
    if student_type:
        stmt = stmt.where(Student.student_type == student_type)
    if art_track:
        stmt = stmt.where(Student.art_track == art_track)
    return stmt.order_by(Student.student_no)


def list_students(
    session: Session,
    *,
    page: int,
    page_size: int,
    **filters,
) -> tuple[Sequence[Student], int]:
    stmt = build_student_query(**filters)
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = session.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return items, total


def get_student(session: Session, student_id: int) -> Student | None:
    stmt = (
        select(Student)
        .options(
            joinedload(Student.current_grade),
            joinedload(Student.current_class),
            selectinload(Student.guardians),
            selectinload(Student.class_histories),
            selectinload(Student.attachments).joinedload(StudentAttachment.stored_file),
        )
        .where(Student.id == student_id)
    )
    return session.scalar(stmt)


def get_student_career_preference(session: Session, student_id: int) -> StudentCareerPreference | None:
    stmt = (
        select(StudentCareerPreference)
        .options(
            joinedload(StudentCareerPreference.primary_direction),
            joinedload(StudentCareerPreference.secondary_direction),
            joinedload(StudentCareerPreference.alternative_direction),
        )
        .where(StudentCareerPreference.student_id == student_id)
    )
    return session.scalar(stmt)


def get_student_by_no(session: Session, student_no: str) -> Student | None:
    return session.scalar(select(Student).where(Student.student_no == student_no))


def get_class_by_name(
    session: Session, class_name: str, grade_id: int | None = None
) -> SchoolClass | None:
    stmt = select(SchoolClass).where(SchoolClass.name == class_name)
    if grade_id:
        stmt = stmt.where(SchoolClass.grade_id == grade_id)
    return session.scalar(stmt)
