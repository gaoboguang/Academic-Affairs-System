from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.system import DataQualityIssueRead
from app.schemas.planning import DashboardPlanningSummary


class DashboardImportJob(BaseModel):
    id: int
    job_type: str
    source_filename: str | None = None
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None


class DashboardRecentExamSummary(BaseModel):
    exam_id: int
    exam_name: str
    exam_date: date
    participant_count: int
    average_score: float | None = None
    excellent_rate: float | None = None


class DashboardBackupSummary(BaseModel):
    backup_name: str
    created_at: datetime | None = None
    status: str | None = None
    file_size: int | None = None


class DashboardDataHealthSummary(BaseModel):
    status: str
    label: str
    summary: str
    p0_gap_count: int = 0
    warning_count: int = 0
    blocking_count: int = 0
    gaps: list[str] = Field(default_factory=list)


class DashboardSummary(BaseModel):
    student_total: int
    teacher_total: int
    exam_total: int
    score_record_total: int
    grade_total: int
    class_total: int
    recent_imports: list[DashboardImportJob]
    latest_backup_time: str | None = None
    latest_backup: DashboardBackupSummary | None = None
    recent_exam: DashboardRecentExamSummary | None = None
    data_health: DashboardDataHealthSummary | None = None
    data_quality_issues: list[DataQualityIssueRead] = Field(default_factory=list)
    planning_summary: DashboardPlanningSummary | None = None
