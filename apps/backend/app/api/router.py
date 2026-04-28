from fastapi import APIRouter

from app.api.routes import (
    archives,
    analytics,
    base_data,
    dashboard,
    evaluation,
    exams,
    gaokao,
    health,
    planning,
    recommendations,
    reports,
    student_events,
    students,
    system,
    teachers,
    workload,
)

api_router = APIRouter()
api_router.include_router(dashboard.router)
api_router.include_router(base_data.router)
api_router.include_router(students.router)
api_router.include_router(teachers.router)
api_router.include_router(archives.router)
api_router.include_router(exams.router)
api_router.include_router(analytics.router)
api_router.include_router(evaluation.router)
api_router.include_router(gaokao.router)
api_router.include_router(recommendations.router)
api_router.include_router(planning.router)
api_router.include_router(reports.router)
api_router.include_router(workload.router)
api_router.include_router(student_events.attendance_router)
api_router.include_router(student_events.behavior_router)
api_router.include_router(system.router)
api_router.include_router(health.router)
