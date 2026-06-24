from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.exam import (
    ClassAnalyticsResponse,
    ClassPanoramaResponse,
    ExamAnalyzableStudentListResponse,
    ExamScoreReportResponse,
    GradeAnalyticsResponse,
    GradePanoramaResponse,
    StudentAnalyticsResponse,
    TeacherAnalyticsResponse,
    TeacherPanoramaResponse,
)
from app.schemas.knowledge import ClassKnowledgeBriefingResponse, ClassKnowledgeHeatmapResponse
from app.schemas.student_followup import AdviserDashboardResponse, StudentRiskResponse
from app.services import analytics as service
from app.services import student_followup as student_followup_service

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
    return student_followup_service.get_adviser_dashboard(
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
    return student_followup_service.get_student_risk(
        session,
        student_id,
        exam_id=exam_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/exams/{exam_id}/students", response_model=ExamAnalyzableStudentListResponse)
def list_exam_analyzable_students(
    exam_id: int,
    session: Session = Depends(get_db_session),
) -> ExamAnalyzableStudentListResponse:
    return service.list_exam_analyzable_students(session, exam_id)


@router.get("/exams/{exam_id}/score-report", response_model=ExamScoreReportResponse)
def get_exam_score_report(
    exam_id: int,
    class_id: int | None = Query(default=None, ge=1),
    keyword: str | None = Query(default=None, max_length=64),
    sort_by: str = Query(default="grade_rank", pattern="^(grade_rank|class_rank|total_score|student_no)$"),
    sort_order: str = Query(default="asc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_db_session),
) -> ExamScoreReportResponse:
    return service.get_exam_score_report(
        session,
        exam_id,
        class_id=class_id,
        keyword=keyword,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
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


@router.get("/classes/{class_id}/knowledge-briefing", response_model=ClassKnowledgeBriefingResponse)
def get_class_knowledge_briefing(
    class_id: int,
    exam_id: int = Query(..., ge=1),
    subject_id: int | None = Query(default=None, ge=1),
    session: Session = Depends(get_db_session),
) -> ClassKnowledgeBriefingResponse:
    return service.get_class_knowledge_briefing(session, class_id, exam_id, subject_id=subject_id)


@router.get("/classes/{class_id}/knowledge-heatmap", response_model=ClassKnowledgeHeatmapResponse)
def get_class_knowledge_heatmap(
    class_id: int,
    exam_id: int = Query(..., ge=1),
    subject_id: int | None = Query(default=None, ge=1),
    session: Session = Depends(get_db_session),
) -> ClassKnowledgeHeatmapResponse:
    return service.get_class_knowledge_heatmap(session, class_id, exam_id, subject_id=subject_id)


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
