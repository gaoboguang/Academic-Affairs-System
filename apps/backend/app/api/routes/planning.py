from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.planning import (
    PlanningBulkCreateFromPathwayPayload,
    PlanningBulkCreateResult,
    PlanningGoalPayload,
    PlanningGoalRead,
    PlanningGoalUpdatePayload,
    PlanningNotePayload,
    PlanningNoteRead,
    PlanningTaskPayload,
    PlanningTaskRead,
    PlanningTaskUpdatePayload,
    StudentPlanningResponse,
)
from app.services import planning as service

router = APIRouter(prefix="/planning", tags=["planning"])


@router.get("/students/{student_id}", response_model=StudentPlanningResponse)
def get_student_planning(
    student_id: int,
    target_year: int | None = Query(default=None, ge=2020, le=2100),
    province: str = Query(default="山东"),
    session: Session = Depends(get_db_session),
) -> StudentPlanningResponse:
    return service.get_student_planning(session, student_id, target_year=target_year, province=province)


@router.post("/goals", response_model=PlanningGoalRead)
def create_goal(
    payload: PlanningGoalPayload,
    session: Session = Depends(get_db_session),
) -> PlanningGoalRead:
    return service.create_goal(session, payload)


@router.put("/goals/{goal_id}", response_model=PlanningGoalRead)
def update_goal(
    goal_id: int,
    payload: PlanningGoalUpdatePayload,
    session: Session = Depends(get_db_session),
) -> PlanningGoalRead:
    return service.update_goal(session, goal_id, payload)


@router.post("/tasks", response_model=PlanningTaskRead)
def create_task(
    payload: PlanningTaskPayload,
    session: Session = Depends(get_db_session),
) -> PlanningTaskRead:
    return service.create_task(session, payload)


@router.put("/tasks/{task_id}", response_model=PlanningTaskRead)
def update_task(
    task_id: int,
    payload: PlanningTaskUpdatePayload,
    session: Session = Depends(get_db_session),
) -> PlanningTaskRead:
    return service.update_task(session, task_id, payload)


@router.post("/tasks/bulk-create-from-pathway", response_model=PlanningBulkCreateResult)
def bulk_create_tasks_from_pathway(
    payload: PlanningBulkCreateFromPathwayPayload,
    session: Session = Depends(get_db_session),
) -> PlanningBulkCreateResult:
    return service.bulk_create_tasks_from_pathway(session, payload)


@router.post("/notes", response_model=PlanningNoteRead)
def create_note(
    payload: PlanningNotePayload,
    session: Session = Depends(get_db_session),
) -> PlanningNoteRead:
    return service.create_note(session, payload)
