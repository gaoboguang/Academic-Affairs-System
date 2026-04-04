from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import AcademicYear, ConfigItem, DictItem, DictType, Grade, SchoolClass, Semester, Subject, Teacher
from app.repositories import base_data as repo
from app.schemas.base_data import (
    AcademicYearPayload,
    AcademicYearRead,
    ClassPayload,
    ClassRead,
    ConfigItemRead,
    DictItemPayload,
    DictItemRead,
    DictTypePayload,
    DictTypeRead,
    GradePayload,
    GradeRead,
    SemesterPayload,
    SemesterRead,
    SubjectPayload,
    SubjectRead,
)


def _not_found(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


def _flush_or_400(session: Session) -> None:
    try:
        session.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=400, detail="数据存在重复或约束冲突。") from exc


def _reset_current_flag(session: Session, model: type[Any], exclude_id: int | None = None) -> None:
    rows = session.scalars(select(model).where(model.is_current.is_(True))).all()  # type: ignore[attr-defined]
    for row in rows:
        if exclude_id and row.id == exclude_id:
            continue
        row.is_current = False


def _serialize_academic_year(item: AcademicYear) -> AcademicYearRead:
    return AcademicYearRead.model_validate(item)


def _serialize_semester(item: Semester) -> SemesterRead:
    return SemesterRead(
        id=item.id,
        academic_year_id=item.academic_year_id,
        academic_year_name=item.academic_year.name if item.academic_year else None,
        name=item.name,
        start_date=item.start_date,
        end_date=item.end_date,
        week_count=item.week_count,
        is_current=item.is_current,
        is_active=item.is_active,
    )


def _serialize_grade(item: Grade) -> GradeRead:
    return GradeRead.model_validate(item)


def _serialize_class(item: SchoolClass) -> ClassRead:
    return ClassRead(
        id=item.id,
        grade_id=item.grade_id,
        grade_name=item.grade.name if item.grade else None,
        name=item.name,
        class_type=item.class_type,
        head_teacher_id=item.head_teacher_id,
        head_teacher_name=item.head_teacher.name if item.head_teacher else None,
        student_count=item.student_count,
        is_active=item.is_active,
    )


def _serialize_subject(item: Subject) -> SubjectRead:
    return SubjectRead.model_validate(item)


def _serialize_dict_type(item: DictType) -> DictTypeRead:
    return DictTypeRead.model_validate(item)


def _serialize_dict_item(item: DictItem) -> DictItemRead:
    return DictItemRead.model_validate(item)


def list_academic_years(session: Session) -> list[AcademicYearRead]:
    return [_serialize_academic_year(item) for item in repo.list_academic_years(session)]


def create_academic_year(session: Session, payload: AcademicYearPayload) -> AcademicYearRead:
    if payload.is_current:
        _reset_current_flag(session, AcademicYear)
    item = AcademicYear(**payload.model_dump())
    session.add(item)
    _flush_or_400(session)
    return _serialize_academic_year(item)


def update_academic_year(session: Session, year_id: int, payload: AcademicYearPayload) -> AcademicYearRead:
    item = session.get(AcademicYear, year_id)
    if not item:
        raise _not_found("学年不存在")
    if payload.is_current:
        _reset_current_flag(session, AcademicYear, exclude_id=year_id)
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    _flush_or_400(session)
    return _serialize_academic_year(item)


def list_semesters(session: Session) -> list[SemesterRead]:
    return [_serialize_semester(item) for item in repo.list_semesters(session)]


def create_semester(session: Session, payload: SemesterPayload) -> SemesterRead:
    if not session.get(AcademicYear, payload.academic_year_id):
        raise _not_found("所属学年不存在")
    if payload.is_current:
        _reset_current_flag(session, Semester)
    item = Semester(**payload.model_dump())
    session.add(item)
    _flush_or_400(session)
    session.refresh(item)
    return _serialize_semester(item)


def update_semester(session: Session, semester_id: int, payload: SemesterPayload) -> SemesterRead:
    item = session.get(Semester, semester_id)
    if not item:
        raise _not_found("学期不存在")
    if not session.get(AcademicYear, payload.academic_year_id):
        raise _not_found("所属学年不存在")
    if payload.is_current:
        _reset_current_flag(session, Semester, exclude_id=semester_id)
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    _flush_or_400(session)
    session.refresh(item)
    return _serialize_semester(item)


def list_grades(session: Session) -> list[GradeRead]:
    return [_serialize_grade(item) for item in repo.list_grades(session)]


def create_grade(session: Session, payload: GradePayload) -> GradeRead:
    item = Grade(**payload.model_dump())
    session.add(item)
    _flush_or_400(session)
    return _serialize_grade(item)


def update_grade(session: Session, grade_id: int, payload: GradePayload) -> GradeRead:
    item = session.get(Grade, grade_id)
    if not item:
        raise _not_found("年级不存在")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    _flush_or_400(session)
    return _serialize_grade(item)


def list_classes(session: Session, grade_id: int | None = None) -> list[ClassRead]:
    return [_serialize_class(item) for item in repo.list_classes(session, grade_id=grade_id)]


def create_class(session: Session, payload: ClassPayload) -> ClassRead:
    if not session.get(Grade, payload.grade_id):
        raise _not_found("所属年级不存在")
    if payload.head_teacher_id and not session.get(Teacher, payload.head_teacher_id):
        raise _not_found("班主任教师不存在")
    item = SchoolClass(**payload.model_dump())
    session.add(item)
    _flush_or_400(session)
    session.refresh(item)
    return _serialize_class(item)


def update_class(session: Session, class_id: int, payload: ClassPayload) -> ClassRead:
    item = session.get(SchoolClass, class_id)
    if not item:
        raise _not_found("班级不存在")
    if not session.get(Grade, payload.grade_id):
        raise _not_found("所属年级不存在")
    if payload.head_teacher_id and not session.get(Teacher, payload.head_teacher_id):
        raise _not_found("班主任教师不存在")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    _flush_or_400(session)
    session.refresh(item)
    return _serialize_class(item)


def list_subjects(session: Session) -> list[SubjectRead]:
    return [_serialize_subject(item) for item in repo.list_subjects(session)]


def create_subject(session: Session, payload: SubjectPayload) -> SubjectRead:
    item = Subject(**payload.model_dump())
    session.add(item)
    _flush_or_400(session)
    return _serialize_subject(item)


def update_subject(session: Session, subject_id: int, payload: SubjectPayload) -> SubjectRead:
    item = session.get(Subject, subject_id)
    if not item:
        raise _not_found("学科不存在")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    _flush_or_400(session)
    return _serialize_subject(item)


def list_dict_types(session: Session) -> list[DictTypeRead]:
    return [_serialize_dict_type(item) for item in repo.list_dict_types(session)]


def create_dict_type(session: Session, payload: DictTypePayload) -> DictTypeRead:
    item = DictType(**payload.model_dump())
    session.add(item)
    _flush_or_400(session)
    return _serialize_dict_type(item)


def update_dict_type(session: Session, dict_type_id: int, payload: DictTypePayload) -> DictTypeRead:
    item = session.get(DictType, dict_type_id)
    if not item:
        raise _not_found("字典类型不存在")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    _flush_or_400(session)
    return _serialize_dict_type(item)


def list_dict_items(session: Session, dict_code: str) -> list[DictItemRead]:
    return [_serialize_dict_item(item) for item in repo.list_dict_items(session, dict_code)]


def create_dict_item(session: Session, dict_code: str, payload: DictItemPayload) -> DictItemRead:
    dict_type = repo.get_dict_type_by_code(session, dict_code)
    if not dict_type:
        raise _not_found("字典类型不存在")
    item = DictItem(dict_type_id=dict_type.id, **payload.model_dump())
    session.add(item)
    _flush_or_400(session)
    return _serialize_dict_item(item)


def update_dict_item(session: Session, dict_item_id: int, payload: DictItemPayload) -> DictItemRead:
    item = session.get(DictItem, dict_item_id)
    if not item:
        raise _not_found("字典项不存在")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    _flush_or_400(session)
    return _serialize_dict_item(item)


def list_config_items(session: Session) -> list[ConfigItemRead]:
    return [ConfigItemRead.model_validate(item) for item in repo.list_config_items(session)]

