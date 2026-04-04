from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.exam import (
    ClassAnalyticsResponse,
    GradeAnalyticsResponse,
    StudentAnalyticsResponse,
    TeacherAnalyticsResponse,
)
from app.services import analytics as service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/students/{student_id}", response_model=StudentAnalyticsResponse)
def get_student_analytics(
    student_id: int,
    exam_id: int = Query(..., ge=1),
    session: Session = Depends(get_db_session),
) -> StudentAnalyticsResponse:
    return service.get_student_analytics(session, student_id, exam_id)


@router.get("/classes/{class_id}", response_model=ClassAnalyticsResponse)
def get_class_analytics(
    class_id: int,
    exam_id: int = Query(..., ge=1),
    session: Session = Depends(get_db_session),
) -> ClassAnalyticsResponse:
    return service.get_class_analytics(session, class_id, exam_id)


@router.get("/grades/{grade_id}", response_model=GradeAnalyticsResponse)
def get_grade_analytics(
    grade_id: int,
    exam_id: int = Query(..., ge=1),
    session: Session = Depends(get_db_session),
) -> GradeAnalyticsResponse:
    return service.get_grade_analytics(session, grade_id, exam_id)


@router.get("/teachers/{teacher_id}", response_model=TeacherAnalyticsResponse)
def get_teacher_analytics(
    teacher_id: int,
    exam_id: int = Query(..., ge=1),
    session: Session = Depends(get_db_session),
) -> TeacherAnalyticsResponse:
    return service.get_teacher_analytics(session, teacher_id, exam_id)
