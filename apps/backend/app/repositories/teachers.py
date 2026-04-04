from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Teacher, TeachingAssignment


def build_teacher_query(
    *,
    teacher_no: str | None = None,
    name: str | None = None,
    subject_id: int | None = None,
    title_code: str | None = None,
    is_head_teacher: bool | None = None,
) -> Select[tuple[Teacher]]:
    stmt = select(Teacher).options(joinedload(Teacher.subject))
    if teacher_no:
        stmt = stmt.where(Teacher.teacher_no.contains(teacher_no))
    if name:
        stmt = stmt.where(Teacher.name.contains(name))
    if subject_id:
        stmt = stmt.where(Teacher.subject_id == subject_id)
    if title_code:
        stmt = stmt.where(Teacher.title_code == title_code)
    if is_head_teacher is not None:
        stmt = stmt.where(Teacher.is_head_teacher == is_head_teacher)
    return stmt.order_by(Teacher.teacher_no)


def list_teachers(
    session: Session,
    *,
    page: int,
    page_size: int,
    **filters,
) -> tuple[Sequence[Teacher], int]:
    stmt = build_teacher_query(**filters)
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = session.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return items, total


def get_teacher(session: Session, teacher_id: int) -> Teacher | None:
    stmt = select(Teacher).options(joinedload(Teacher.subject)).where(Teacher.id == teacher_id)
    return session.scalar(stmt)


def get_teacher_by_no(session: Session, teacher_no: str) -> Teacher | None:
    return session.scalar(select(Teacher).where(Teacher.teacher_no == teacher_no))


def list_teaching_assignments(session: Session) -> Sequence[TeachingAssignment]:
    stmt = (
        select(TeachingAssignment)
        .options(
            joinedload(TeachingAssignment.teacher),
            joinedload(TeachingAssignment.semester),
            joinedload(TeachingAssignment.grade),
            joinedload(TeachingAssignment.school_class),
            joinedload(TeachingAssignment.subject),
        )
        .order_by(TeachingAssignment.id.desc())
    )
    return session.scalars(stmt).all()

