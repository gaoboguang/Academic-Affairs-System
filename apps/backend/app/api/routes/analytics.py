from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.exam import (
    ClassAnalyticsResponse,
    ClassPanoramaResponse,
    GradeAnalyticsResponse,
    GradePanoramaResponse,
    StudentAnalyticsResponse,
    TeacherAnalyticsResponse,
    TeacherPanoramaResponse,
)
from app.schemas.student_event import AdviserDashboardResponse, StudentRiskResponse
from app.services import analytics as service
from app.services import student_events as student_event_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/adviser-dashboard", response_model=AdviserDashboardResponse)
def get_adviser_dashboard(
    grade_id: int | None = None,
    class_id: int | None = None,
    exam_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    session: Session = Depends(get_db_session),
) -> AdviserDashboardResponse:
    return student_event_service.get_adviser_dashboard(
        session,
        grade_id=grade_id,
        class_id=class_id,
        exam_id=exam_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/student-risk/{student_id}", response_model=StudentRiskResponse)
def get_student_risk(
    student_id: int,
    exam_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    session: Session = Depends(get_db_session),
) -> StudentRiskResponse:
    return student_event_service.get_student_risk(
        session,
        student_id,
        exam_id=exam_id,
        start_date=start_date,
        end_date=end_date,
    )


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


@router.get("/classes/{class_id}/panorama", response_model=ClassPanoramaResponse)
def get_class_panorama(
    class_id: int,
    academic_year_ids: list[int] | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> ClassPanoramaResponse:
    return service.get_class_panorama(session, class_id, academic_year_ids=academic_year_ids)


@router.get("/grades/{grade_id}", response_model=GradeAnalyticsResponse)
def get_grade_analytics(
    grade_id: int,
    exam_id: int = Query(..., ge=1),
    session: Session = Depends(get_db_session),
) -> GradeAnalyticsResponse:
    return service.get_grade_analytics(session, grade_id, exam_id)


@router.get("/grades/{grade_id}/panorama", response_model=GradePanoramaResponse)
def get_grade_panorama(
    grade_id: int,
    academic_year_ids: list[int] | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> GradePanoramaResponse:
    return service.get_grade_panorama(session, grade_id, academic_year_ids=academic_year_ids)


@router.get("/teachers/{teacher_id}", response_model=TeacherAnalyticsResponse)
def get_teacher_analytics(
    teacher_id: int,
    exam_id: int = Query(..., ge=1),
    session: Session = Depends(get_db_session),
) -> TeacherAnalyticsResponse:
    return service.get_teacher_analytics(session, teacher_id, exam_id)


@router.get("/teachers/{teacher_id}/panorama", response_model=TeacherPanoramaResponse)
def get_teacher_panorama(
    teacher_id: int,
    academic_year_ids: list[int] | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> TeacherPanoramaResponse:
    return service.get_teacher_panorama(session, teacher_id, academic_year_ids=academic_year_ids)
