from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel
from app.schemas.gaokao_pathway import StudentPathwayEvaluationRead, StudentPathwayProfileRead


class PlanningStudentRead(BaseModel):
    id: int
    student_no: str
    name: str
    grade_name: str | None = None
    class_name: str | None = None


class PlanningGoalPayload(BaseModel):
    student_id: int
    target_year: int = 2026
    pathway_code: str
    pathway_name: str
    target_college: str | None = None
    target_major: str | None = None
    target_score: float | None = None
    target_rank: int | None = None
    backup_pathways: str | None = None
    status: str = "in_progress"
    priority: str = "medium"
    note: str | None = None
    is_active: bool = True


class PlanningGoalUpdatePayload(BaseModel):
    target_year: int | None = None
    pathway_code: str | None = None
    pathway_name: str | None = None
    target_college: str | None = None
    target_major: str | None = None
    target_score: float | None = None
    target_rank: int | None = None
    backup_pathways: str | None = None
    status: str | None = None
    priority: str | None = None
    note: str | None = None
    is_active: bool | None = None


class PlanningGoalRead(ORMModel):
    id: int
    student_id: int
    target_year: int
    pathway_code: str
    pathway_name: str
    target_college: str | None = None
    target_major: str | None = None
    target_score: float | None = None
    target_rank: int | None = None
    backup_pathways: str | None = None
    status: str
    status_label: str
    priority: str
    priority_label: str
    note: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_active: bool


class PlanningTaskPayload(BaseModel):
    student_id: int
    goal_id: int | None = None
    source_type: str = "manual"
    source_ref_id: str | None = None
    task_type: str = "other"
    title: str
    description: str | None = None
    status: str = "not_started"
    priority: str = "medium"
    due_date: date | None = None
    related_route: str | None = None
    is_active: bool = True


class PlanningTaskUpdatePayload(BaseModel):
    goal_id: int | None = None
    source_type: str | None = None
    source_ref_id: str | None = None
    task_type: str | None = None
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    due_date: date | None = None
    related_route: str | None = None
    is_active: bool | None = None


class PlanningTaskRead(ORMModel):
    id: int | None = None
    student_id: int
    goal_id: int | None = None
    source_type: str
    source_ref_id: str | None = None
    task_type: str
    task_type_label: str
    title: str
    description: str | None = None
    status: str
    status_label: str
    priority: str
    priority_label: str
    due_date: date | None = None
    completed_at: datetime | None = None
    related_route: str | None = None
    is_overdue: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_active: bool


class PlanningNotePayload(BaseModel):
    student_id: int
    goal_id: int | None = None
    task_id: int | None = None
    note_type: str = "review"
    content: str
    is_active: bool = True


class PlanningNoteRead(ORMModel):
    id: int
    student_id: int
    goal_id: int | None = None
    task_id: int | None = None
    note_type: str
    note_type_label: str
    content: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_active: bool


class StudentPlanningSummary(BaseModel):
    open_task_count: int = 0
    completed_task_count: int = 0
    overdue_task_count: int = 0
    due_soon_task_count: int = 0
    material_gap_task_count: int = 0
    no_goal: bool = False
    has_pathway_profile: bool = False
    has_pathway_evaluations: bool = False


class StudentPlanningResponse(BaseModel):
    student: PlanningStudentRead
    goals: list[PlanningGoalRead] = Field(default_factory=list)
    tasks: list[PlanningTaskRead] = Field(default_factory=list)
    notes: list[PlanningNoteRead] = Field(default_factory=list)
    pathway_profile: StudentPathwayProfileRead | None = None
    pathway_evaluations: list[StudentPathwayEvaluationRead] = Field(default_factory=list)
    suggested_tasks: list[PlanningTaskRead] = Field(default_factory=list)
    summary: StudentPlanningSummary


class PlanningBulkCreateFromPathwayPayload(BaseModel):
    student_id: int
    target_year: int = 2026
    province: str = "山东"
    pathway_ids: list[int] = Field(default_factory=list)
    include_material_gaps: bool = True
    include_review_tasks: bool = True
    due_date: date | None = None


class PlanningBulkCreateResult(BaseModel):
    created_count: int
    skipped_count: int
    tasks: list[PlanningTaskRead] = Field(default_factory=list)
    notices: list[str] = Field(default_factory=list)


class DashboardPlanningSummary(BaseModel):
    open_task_count: int = 0
    overdue_task_count: int = 0
    due_soon_task_count: int = 0
    students_with_goal_count: int = 0
    students_without_goal_count: int = 0
    volunteer_draft_without_review_count: int = 0
    material_gap_without_due_count: int = 0
