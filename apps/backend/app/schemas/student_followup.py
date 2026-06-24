from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class ScoreRiskSummary(BaseModel):
    imported: bool = False
    exam_id: int | None = None
    exam_name: str | None = None
    sample_count: int = 0
    total_score: float | None = None
    class_rank: int | None = None
    grade_rank: int | None = None
    previous_total_score: float | None = None
    total_score_delta: float | None = None
    low_score: bool = False
    decline_risk: bool = False


class GrowthFollowupSummary(BaseModel):
    record_count: int = 0
    latest_record_date: date | None = None


class PlanningFollowupSummary(BaseModel):
    open_task_count: int = 0
    overdue_task_count: int = 0
    due_soon_task_count: int = 0
    high_priority_open_count: int = 0
    no_goal: bool = False
    next_due_date: date | None = None


class StudentRiskResponse(BaseModel):
    student_id: int
    student_no: str | None = None
    student_name: str
    grade_id: int | None = None
    grade_name: str | None = None
    class_id: int | None = None
    class_name: str | None = None
    risk_level: str
    risk_label: str
    reasons: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    data_flags: list[str] = Field(default_factory=list)
    score_summary: ScoreRiskSummary
    growth_summary: GrowthFollowupSummary
    planning_summary: PlanningFollowupSummary


class AdviserDashboardOverview(BaseModel):
    student_count: int = 0
    score_sample_count: int = 0
    growth_record_count: int = 0
    open_task_count: int = 0
    overdue_task_count: int = 0
    follow_up_count: int = 0


class AdviserDashboardScoreSummary(BaseModel):
    imported: bool = False
    exam_id: int | None = None
    exam_name: str | None = None
    sample_count: int = 0
    average_total_score: float | None = None
    low_score_count: int = 0
    decline_count: int = 0


class AdviserDashboardGrowthSummary(BaseModel):
    total_records: int = 0
    students_with_records_count: int = 0
    latest_record_date: date | None = None


class AdviserDashboardPlanningSummary(BaseModel):
    open_task_count: int = 0
    overdue_task_count: int = 0
    due_soon_task_count: int = 0
    high_priority_open_count: int = 0
    students_without_goal_count: int = 0


class AdviserRiskStudentItem(BaseModel):
    student_id: int
    student_no: str | None = None
    student_name: str
    class_id: int | None = None
    class_name: str | None = None
    risk_level: str
    risk_label: str
    primary_reason: str
    reasons: list[str] = Field(default_factory=list)
    suggested_action: str


class AdviserActionItem(BaseModel):
    action_type: str
    title: str
    count: int
    student_ids: list[int] = Field(default_factory=list)
    target_route: str | None = None


class AdviserDashboardResponse(BaseModel):
    grade_id: int | None = None
    grade_name: str | None = None
    class_id: int | None = None
    class_name: str | None = None
    exam_id: int | None = None
    exam_name: str | None = None
    start_date: date
    end_date: date
    overview: AdviserDashboardOverview
    score_summary: AdviserDashboardScoreSummary
    growth_summary: AdviserDashboardGrowthSummary
    planning_summary: AdviserDashboardPlanningSummary
    risk_students: list[AdviserRiskStudentItem] = Field(default_factory=list)
    action_items: list[AdviserActionItem] = Field(default_factory=list)
    data_flags: list[str] = Field(default_factory=list)
