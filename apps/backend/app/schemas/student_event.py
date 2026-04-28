from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class AttendanceRecordRead(ORMModel):
    id: int
    student_id: int
    student_no: str | None = None
    student_name: str | None = None
    grade_id: int | None = None
    grade_name: str | None = None
    class_id: int | None = None
    class_name: str | None = None
    record_date: date
    scope: str
    period_index: int
    status: str
    reason: str | None = None
    note: str | None = None
    source_batch_id: int | None = None
    created_at: datetime
    updated_at: datetime


class AttendanceRecordListResponse(BaseModel):
    total: int
    items: list[AttendanceRecordRead]


class BehaviorRecordRead(ORMModel):
    id: int
    student_id: int
    student_no: str | None = None
    student_name: str | None = None
    grade_id: int | None = None
    grade_name: str | None = None
    class_id: int | None = None
    class_name: str | None = None
    record_date: date
    category: str
    severity: str
    title: str
    description: str | None = None
    handler_name: str | None = None
    points_delta: float | None = None
    attachment_path: str | None = None
    source_batch_id: int | None = None
    created_at: datetime
    updated_at: datetime


class BehaviorRecordListResponse(BaseModel):
    total: int
    items: list[BehaviorRecordRead]


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


class AttendanceRiskSummary(BaseModel):
    imported: bool = False
    total_records: int = 0
    normal_count: int = 0
    late_count: int = 0
    early_leave_count: int = 0
    sick_leave_count: int = 0
    personal_leave_count: int = 0
    truancy_count: int = 0
    other_count: int = 0
    status_counts: dict[str, int] = Field(default_factory=dict)


class BehaviorRiskSummary(BaseModel):
    imported: bool = False
    total_records: int = 0
    positive_count: int = 0
    discipline_count: int = 0
    severe_count: int = 0
    category_counts: dict[str, int] = Field(default_factory=dict)
    severity_counts: dict[str, int] = Field(default_factory=dict)


class GrowthRiskSummary(BaseModel):
    record_count: int = 0
    latest_record_date: date | None = None


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
    attendance_summary: AttendanceRiskSummary
    behavior_summary: BehaviorRiskSummary
    growth_summary: GrowthRiskSummary


class AdviserDashboardOverview(BaseModel):
    student_count: int = 0
    score_sample_count: int = 0
    attendance_status: str = "未导入"
    behavior_status: str = "未导入"
    absence_risk_count: int = 0
    behavior_risk_count: int = 0
    follow_up_count: int = 0


class AdviserDashboardScoreSummary(BaseModel):
    imported: bool = False
    exam_id: int | None = None
    exam_name: str | None = None
    sample_count: int = 0
    average_total_score: float | None = None
    low_score_count: int = 0
    decline_count: int = 0


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
    attendance_summary: AttendanceRiskSummary
    behavior_summary: BehaviorRiskSummary
    risk_students: list[AdviserRiskStudentItem] = Field(default_factory=list)
    action_items: list[AdviserActionItem] = Field(default_factory=list)
    data_flags: list[str] = Field(default_factory=list)
