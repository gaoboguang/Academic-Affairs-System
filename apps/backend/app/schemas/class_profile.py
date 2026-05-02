from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel
from app.schemas.student import StudentRead
from app.schemas.teacher import TeachingAssignmentRead


class ClassHonorPayload(BaseModel):
    title: str
    honor_level: str | None = None
    awarded_on: date | None = None
    source: str | None = None
    note: str | None = None
    is_active: bool = True


class ClassHonorRead(ORMModel):
    id: int
    class_id: int
    title: str
    honor_level: str | None = None
    awarded_on: date | None = None
    source: str | None = None
    note: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ClassTeacherSummary(BaseModel):
    teacher_id: int
    teacher_name: str
    subject_id: int | None = None
    subject_name: str | None = None
    course_type: str | None = None
    weekly_periods_manual: int | None = None


class ClassScoreSummary(BaseModel):
    exam_id: int | None = None
    exam_name: str | None = None
    sample_count: int = 0
    average_score: float | None = None
    max_score: float | None = None
    min_score: float | None = None


class ClassRiskSummary(BaseModel):
    follow_up_count: int = 0
    urgent_count: int = 0
    attendance_risk_count: int = 0
    behavior_risk_count: int = 0


class ClassOverviewItem(BaseModel):
    class_id: int
    class_name: str
    grade_id: int
    grade_name: str | None = None
    class_type: str | None = None
    head_teacher_id: int | None = None
    head_teacher_name: str | None = None
    student_count: int = 0
    active_student_count: int = 0
    teacher_count: int = 0
    teacher_summary: list[ClassTeacherSummary] = Field(default_factory=list)
    honor_count: int = 0
    latest_honor: ClassHonorRead | None = None
    score_summary: ClassScoreSummary = Field(default_factory=ClassScoreSummary)
    risk_summary: ClassRiskSummary = Field(default_factory=ClassRiskSummary)
    teaching_complete: bool = False


class GradeOverviewGroup(BaseModel):
    grade_id: int
    grade_name: str
    class_count: int = 0
    student_count: int = 0
    active_student_count: int = 0
    head_teacher_coverage: float = 0.0
    teaching_complete_rate: float = 0.0
    latest_exam_sample_count: int = 0
    honor_count: int = 0
    classes: list[ClassOverviewItem] = Field(default_factory=list)


class ClassesOverviewResponse(BaseModel):
    semester_id: int | None = None
    semester_name: str | None = None
    exam_id: int | None = None
    exam_name: str | None = None
    grades: list[GradeOverviewGroup] = Field(default_factory=list)
    total_classes: int = 0
    total_students: int = 0
    total_honors: int = 0


class ClassProfileResponse(BaseModel):
    overview: ClassOverviewItem
    honors: list[ClassHonorRead] = Field(default_factory=list)
    students: list[StudentRead] = Field(default_factory=list)
    assignments: list[TeachingAssignmentRead] = Field(default_factory=list)


class GradeProfileResponse(BaseModel):
    grade: GradeOverviewGroup
    classes: list[ClassOverviewItem] = Field(default_factory=list)
