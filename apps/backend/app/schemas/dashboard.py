from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.system import DataQualityIssueRead


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


class DashboardSummary(BaseModel):
    student_total: int
    teacher_total: int
    grade_total: int
    class_total: int
    recent_imports: list[DashboardImportJob]
    latest_backup_time: str | None = None
    recent_exam: DashboardRecentExamSummary | None = None
    data_quality_issues: list[DataQualityIssueRead] = Field(default_factory=list)
