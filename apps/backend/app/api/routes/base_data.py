from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
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
from app.services import base_data as service

router = APIRouter(prefix="/base", tags=["base-data"])


@router.get("/academic-years", response_model=list[AcademicYearRead])
def list_academic_years(session: Session = Depends(get_db_session)) -> list[AcademicYearRead]:
    return service.list_academic_years(session)


@router.post("/academic-years", response_model=AcademicYearRead)
def create_academic_year(
    payload: AcademicYearPayload, session: Session = Depends(get_db_session)
) -> AcademicYearRead:
    return service.create_academic_year(session, payload)


@router.put("/academic-years/{year_id}", response_model=AcademicYearRead)
def update_academic_year(
    year_id: int,
    payload: AcademicYearPayload,
    session: Session = Depends(get_db_session),
) -> AcademicYearRead:
    return service.update_academic_year(session, year_id, payload)


@router.get("/semesters", response_model=list[SemesterRead])
def list_semesters(session: Session = Depends(get_db_session)) -> list[SemesterRead]:
    return service.list_semesters(session)


@router.post("/semesters", response_model=SemesterRead)
def create_semester(payload: SemesterPayload, session: Session = Depends(get_db_session)) -> SemesterRead:
    return service.create_semester(session, payload)


@router.put("/semesters/{semester_id}", response_model=SemesterRead)
def update_semester(
    semester_id: int,
    payload: SemesterPayload,
    session: Session = Depends(get_db_session),
) -> SemesterRead:
    return service.update_semester(session, semester_id, payload)


@router.get("/grades", response_model=list[GradeRead])
def list_grades(session: Session = Depends(get_db_session)) -> list[GradeRead]:
    return service.list_grades(session)


@router.post("/grades", response_model=GradeRead)
def create_grade(payload: GradePayload, session: Session = Depends(get_db_session)) -> GradeRead:
    return service.create_grade(session, payload)


@router.put("/grades/{grade_id}", response_model=GradeRead)
def update_grade(
    grade_id: int,
    payload: GradePayload,
    session: Session = Depends(get_db_session),
) -> GradeRead:
    return service.update_grade(session, grade_id, payload)


@router.get("/classes", response_model=list[ClassRead])
def list_classes(
    grade_id: int | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[ClassRead]:
    return service.list_classes(session, grade_id=grade_id)


@router.post("/classes", response_model=ClassRead)
def create_class(payload: ClassPayload, session: Session = Depends(get_db_session)) -> ClassRead:
    return service.create_class(session, payload)


@router.put("/classes/{class_id}", response_model=ClassRead)
def update_class(
    class_id: int,
    payload: ClassPayload,
    session: Session = Depends(get_db_session),
) -> ClassRead:
    return service.update_class(session, class_id, payload)


@router.get("/subjects", response_model=list[SubjectRead])
def list_subjects(session: Session = Depends(get_db_session)) -> list[SubjectRead]:
    return service.list_subjects(session)


@router.post("/subjects", response_model=SubjectRead)
def create_subject(payload: SubjectPayload, session: Session = Depends(get_db_session)) -> SubjectRead:
    return service.create_subject(session, payload)


@router.put("/subjects/{subject_id}", response_model=SubjectRead)
def update_subject(
    subject_id: int,
    payload: SubjectPayload,
    session: Session = Depends(get_db_session),
) -> SubjectRead:
    return service.update_subject(session, subject_id, payload)


@router.get("/dict-types", response_model=list[DictTypeRead])
def list_dict_types(session: Session = Depends(get_db_session)) -> list[DictTypeRead]:
    return service.list_dict_types(session)


@router.post("/dict-types", response_model=DictTypeRead)
def create_dict_type(
    payload: DictTypePayload, session: Session = Depends(get_db_session)
) -> DictTypeRead:
    return service.create_dict_type(session, payload)


@router.put("/dict-types/{dict_type_id}", response_model=DictTypeRead)
def update_dict_type(
    dict_type_id: int,
    payload: DictTypePayload,
    session: Session = Depends(get_db_session),
) -> DictTypeRead:
    return service.update_dict_type(session, dict_type_id, payload)


@router.get("/dict-types/{dict_code}/items", response_model=list[DictItemRead])
def list_dict_items(
    dict_code: str,
    session: Session = Depends(get_db_session),
) -> list[DictItemRead]:
    return service.list_dict_items(session, dict_code)


@router.post("/dict-types/{dict_code}/items", response_model=DictItemRead)
def create_dict_item(
    dict_code: str,
    payload: DictItemPayload,
    session: Session = Depends(get_db_session),
) -> DictItemRead:
    return service.create_dict_item(session, dict_code, payload)


@router.put("/dict-items/{dict_item_id}", response_model=DictItemRead)
def update_dict_item(
    dict_item_id: int,
    payload: DictItemPayload,
    session: Session = Depends(get_db_session),
) -> DictItemRead:
    return service.update_dict_item(session, dict_item_id, payload)


@router.get("/config-items", response_model=list[ConfigItemRead])
def list_config_items(session: Session = Depends(get_db_session)) -> list[ConfigItemRead]:
    return service.list_config_items(session)

