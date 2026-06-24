from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.class_profile import (
    ClassHonorPayload,
    ClassHonorRead,
    ClassProfileResponse,
    ClassesOverviewResponse,
    GradeProfileResponse,
)
from app.services import class_profiles as service

router = APIRouter(tags=["class-profiles"])


@router.get("/classes/overview", response_model=ClassesOverviewResponse)
def get_classes_overview(
    grade_id: int | None = Query(default=None),
    semester_id: int | None = Query(default=None),
    exam_id: int | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> ClassesOverviewResponse:
    return service.get_classes_overview(
        session,
        grade_id=grade_id,
        semester_id=semester_id,
        exam_id=exam_id,
    )


@router.get("/classes/{class_id}/profile", response_model=ClassProfileResponse)
def get_class_profile(
    class_id: int,
    semester_id: int | None = Query(default=None),
    exam_id: int | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> ClassProfileResponse:
    return service.get_class_profile(session, class_id, semester_id=semester_id, exam_id=exam_id)


@router.get("/grades/{grade_id}/profile", response_model=GradeProfileResponse)
def get_grade_profile(
    grade_id: int,
    semester_id: int | None = Query(default=None),
    exam_id: int | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> GradeProfileResponse:
    return service.get_grade_profile(session, grade_id, semester_id=semester_id, exam_id=exam_id)


@router.get("/classes/{class_id}/honors", response_model=list[ClassHonorRead])
def list_class_honors(
    class_id: int,
    session: Session = Depends(get_db_session),
) -> list[ClassHonorRead]:
    return service.list_class_honors(session, class_id)


@router.post("/classes/{class_id}/honors", response_model=ClassHonorRead)
def create_class_honor(
    class_id: int,
    payload: ClassHonorPayload,
    session: Session = Depends(get_db_session),
) -> ClassHonorRead:
    return service.create_class_honor(session, class_id, payload)


@router.put("/classes/{class_id}/honors/{honor_id}", response_model=ClassHonorRead)
def update_class_honor(
    class_id: int,
    honor_id: int,
    payload: ClassHonorPayload,
    session: Session = Depends(get_db_session),
) -> ClassHonorRead:
    return service.update_class_honor(session, class_id, honor_id, payload)


@router.delete("/classes/{class_id}/honors/{honor_id}")
def delete_class_honor(
    class_id: int,
    honor_id: int,
    session: Session = Depends(get_db_session),
) -> dict[str, str]:
    return service.delete_class_honor(session, class_id, honor_id)
