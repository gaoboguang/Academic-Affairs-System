from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class TeacherPayload(BaseModel):
    teacher_no: str
    name: str
    gender: str | None = None
    subject_id: int | None = None
    phone: str | None = None
    title_code: str | None = None
    position_code: str | None = None
    is_head_teacher: bool = False
    employment_status: str | None = None
    entry_date: date | None = None
    note: str | None = None
    is_active: bool = True


class TeacherRead(ORMModel):
    id: int
    teacher_no: str
    name: str
    gender: str | None = None
    subject_id: int | None = None
    subject_name: str | None = None
    phone: str | None = None
    title_code: str | None = None
    position_code: str | None = None
    is_head_teacher: bool
    employment_status: str | None = None
    entry_date: date | None = None
    note: str | None = None
    is_active: bool


class TeacherListResponse(BaseModel):
    items: list[TeacherRead]
    total: int
    page: int
    page_size: int


class TeachingAssignmentPayload(BaseModel):
    teacher_id: int
    semester_id: int
    grade_id: int | None = None
    class_id: int | None = None
    subject_id: int | None = None
    course_type: str | None = None
    weekly_periods_manual: int | None = None
    is_active: bool = True


class TeachingAssignmentRead(ORMModel):
    id: int
    teacher_id: int
    teacher_name: str | None = None
    semester_id: int
    semester_name: str | None = None
    grade_id: int | None = None
    grade_name: str | None = None
    class_id: int | None = None
    class_name: str | None = None
    subject_id: int | None = None
    subject_name: str | None = None
    course_type: str | None = None
    weekly_periods_manual: int | None = None
    is_active: bool


class TeacherTitleHistoryPayload(BaseModel):
    title_code: str
    start_date: date | None = None
    end_date: date | None = None
    note: str | None = None
    is_active: bool = True


class TeacherTitleHistoryRead(ORMModel):
    id: int
    teacher_id: int
    title_code: str
    start_date: date | None = None
    end_date: date | None = None
    note: str | None = None
    is_active: bool


class TeacherExamTrendItem(BaseModel):
    exam_id: int
    exam_name: str
    exam_date: date
    semester_name: str | None = None
    overall_average: float | None = None
    excellent_rate: float | None = None
    pass_rate: float | None = None
    peer_average: float | None = None
    peer_gap: float | None = None
    class_count: int = 0


class TeacherPeerComparisonItem(BaseModel):
    teacher_id: int
    teacher_name: str
    subject_name: str | None = None
    overall_average: float | None = None
    excellent_rate: float | None = None
    pass_rate: float | None = None
    assignment_count: int = 0
    rank: int = 0


class TeacherProfileRead(BaseModel):
    teacher: TeacherRead
    title_histories: list[TeacherTitleHistoryRead] = Field(default_factory=list)
    assignments: list[TeachingAssignmentRead] = Field(default_factory=list)
    recent_exam_trends: list[TeacherExamTrendItem] = Field(default_factory=list)
    peer_comparisons: list[TeacherPeerComparisonItem] = Field(default_factory=list)
