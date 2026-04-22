from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class StudentGuardianPayload(BaseModel):
    name: str
    relation: str
    phone: str | None = None
    work_unit: str | None = None
    is_primary: bool = False


class StudentGuardianRead(ORMModel):
    id: int
    name: str
    relation: str
    phone: str | None = None
    work_unit: str | None = None
    is_primary: bool


class StudentPayload(BaseModel):
    student_no: str
    name: str
    gender: str | None = None
    birth_date: date | None = None
    id_number: str | None = None
    admission_year: int | None = None
    current_grade_id: int | None = None
    current_class_id: int | None = None
    status: str | None = None
    student_type: str | None = None
    art_track: str | None = None
    origin_province: str | None = None
    phone: str | None = None
    address: str | None = None
    note: str | None = None
    guardians: list[StudentGuardianPayload] = []
    is_active: bool = True


class StudentRead(ORMModel):
    id: int
    student_no: str
    name: str
    gender: str | None = None
    birth_date: date | None = None
    id_number: str | None = None
    admission_year: int | None = None
    current_grade_id: int | None = None
    current_grade_name: str | None = None
    current_class_id: int | None = None
    current_class_name: str | None = None
    status: str | None = None
    student_type: str | None = None
    art_track: str | None = None
    origin_province: str | None = None
    phone: str | None = None
    address: str | None = None
    note: str | None = None
    is_active: bool
    guardians: list[StudentGuardianRead] = []


class StudentCareerPreferencePayload(BaseModel):
    primary_direction_id: int | None = None
    secondary_direction_id: int | None = None
    alternative_direction_id: int | None = None
    priority_focuses_json: list[str] = Field(default_factory=list)
    preferred_industries_json: list[str] = Field(default_factory=list)
    preferred_job_types_json: list[str] = Field(default_factory=list)
    target_employment_cities_json: list[str] = Field(default_factory=list)
    accepts_postgraduate: bool = False
    accepts_public_service: bool = False
    accepts_certificate: bool = False
    accepts_long_training: bool = False


class StudentCareerPreferenceRead(ORMModel):
    id: int
    student_id: int
    primary_direction_id: int | None = None
    primary_direction_name: str | None = None
    secondary_direction_id: int | None = None
    secondary_direction_name: str | None = None
    alternative_direction_id: int | None = None
    alternative_direction_name: str | None = None
    priority_focuses_json: list[str] = Field(default_factory=list)
    preferred_industries_json: list[str] = Field(default_factory=list)
    preferred_job_types_json: list[str] = Field(default_factory=list)
    target_employment_cities_json: list[str] = Field(default_factory=list)
    accepts_postgraduate: bool
    accepts_public_service: bool
    accepts_certificate: bool
    accepts_long_training: bool
    created_at: datetime
    updated_at: datetime
    is_active: bool


class StudentListResponse(BaseModel):
    items: list[StudentRead]
    total: int
    page: int
    page_size: int


class StudentClassHistoryRead(BaseModel):
    id: int
    grade_id: int | None = None
    grade_name: str | None = None
    class_id: int | None = None
    class_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    reason: str | None = None


class StudentExamTrendItem(BaseModel):
    exam_id: int
    exam_name: str
    exam_date: date
    total_score: float
    class_rank: int | None = None
    grade_rank: int | None = None
    class_percentile: float | None = None
    grade_percentile: float | None = None


class StudentGrowthRecordSummary(BaseModel):
    id: int
    occurred_on: date
    record_type: str
    title: str
    owner_name: str | None = None
    attachment_count: int = 0


class StudentRecommendationSummary(BaseModel):
    scheme_id: int
    scheme_name: str
    exam_id: int
    generated_at: str
    result_count: int
    challenge_count: int
    steady_count: int
    safe_count: int


class StudentAttachmentPayload(BaseModel):
    stored_file_id: int
    attachment_type: str | None = None
    title: str | None = None
    note: str | None = None
    is_active: bool = True


class StudentAttachmentSummary(BaseModel):
    id: int | None = None
    stored_file_id: int | None = None
    file_id: int
    original_filename: str
    category: str
    attachment_type: str | None = None
    title: str | None = None
    note: str | None = None
    source_title: str | None = None
    source_type: str | None = None
    created_at: str
    download_url: str | None = None


class StudentPerformanceSummary(BaseModel):
    latest_exam_id: int | None = None
    latest_exam_name: str | None = None
    latest_exam_date: date | None = None
    latest_total_score: float | None = None
    latest_class_rank: int | None = None
    latest_grade_rank: int | None = None
    exam_count: int = 0
    strength_subjects: list[str] = Field(default_factory=list)
    weakness_subjects: list[str] = Field(default_factory=list)


class StudentProfileRead(BaseModel):
    student: StudentRead
    class_histories: list[StudentClassHistoryRead] = Field(default_factory=list)
    performance_summary: StudentPerformanceSummary
    exam_trends: list[StudentExamTrendItem] = Field(default_factory=list)
    recent_growth_records: list[StudentGrowthRecordSummary] = Field(default_factory=list)
    recommendation_history: list[StudentRecommendationSummary] = Field(default_factory=list)
    attachments: list[StudentAttachmentSummary] = Field(default_factory=list)
