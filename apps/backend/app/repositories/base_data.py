from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import AcademicYear, ConfigItem, DictItem, DictType, Grade, SchoolClass, Semester, Subject


def list_academic_years(session: Session) -> Sequence[AcademicYear]:
    return session.scalars(select(AcademicYear).order_by(AcademicYear.start_date.desc())).all()


def list_semesters(session: Session) -> Sequence[Semester]:
    stmt = (
        select(Semester)
        .options(joinedload(Semester.academic_year))
        .order_by(Semester.start_date.desc())
    )
    return session.scalars(stmt).all()


def list_grades(session: Session) -> Sequence[Grade]:
    return session.scalars(select(Grade).order_by(Grade.sort_order, Grade.id)).all()


def list_classes(session: Session, grade_id: int | None = None) -> Sequence[SchoolClass]:
    stmt = select(SchoolClass).options(joinedload(SchoolClass.grade), joinedload(SchoolClass.head_teacher))
    if grade_id:
        stmt = stmt.where(SchoolClass.grade_id == grade_id)
    stmt = stmt.order_by(SchoolClass.grade_id, SchoolClass.name)
    return session.scalars(stmt).all()


def list_subjects(session: Session) -> Sequence[Subject]:
    return session.scalars(select(Subject).order_by(Subject.sort_order, Subject.id)).all()


def list_dict_types(session: Session) -> Sequence[DictType]:
    return session.scalars(select(DictType).order_by(DictType.code)).all()


def list_dict_items(session: Session, dict_code: str) -> Sequence[DictItem]:
    stmt = (
        select(DictItem)
        .join(DictType, DictItem.dict_type_id == DictType.id)
        .where(DictType.code == dict_code)
        .order_by(DictItem.sort_order, DictItem.id)
    )
    return session.scalars(stmt).all()


def get_dict_type_by_code(session: Session, dict_code: str) -> DictType | None:
    return session.scalar(select(DictType).where(DictType.code == dict_code))


def list_config_items(session: Session) -> Sequence[ConfigItem]:
    return session.scalars(
        select(ConfigItem).order_by(ConfigItem.config_group, ConfigItem.config_key)
    ).all()

