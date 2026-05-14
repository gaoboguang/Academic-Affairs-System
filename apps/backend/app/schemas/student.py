from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

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


class StudentBulkDeleteBaseRequest(BaseModel):
    student_ids: list[int] = Field(min_length=1, max_length=1000)
    mode: Literal["soft_delete"] = "soft_delete"
    reason: str = Field(min_length=1, max_length=255)
    operator_name: str | None = Field(default=None, max_length=80)

    @field_validator("student_ids")
    @classmethod
    def validate_student_ids(cls, value: list[int]) -> list[int]:
        normalized: list[int] = []
        seen: set[int] = set()
        for student_id in value:
            if student_id <= 0:
                raise ValueError("学生 ID 必须为正整数")
            if student_id in seen:
                continue
            seen.add(student_id)
            normalized.append(student_id)
        if not normalized:
            raise ValueError("请至少选择 1 名学生")
        return normalized

    @field_validator("reason", "operator_name")
    @classmethod
    def trim_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("文本不能为空")
        return normalized


class StudentBulkDeletePreviewRequest(StudentBulkDeleteBaseRequest):
    pass


class StudentBulkDeleteExecuteRequest(StudentBulkDeleteBaseRequest):
    confirm_token: str = Field(min_length=16, max_length=128)
    confirm_text: str = Field(min_length=1, max_length=80)

    @field_validator("confirm_token", "confirm_text")
    @classmethod
    def trim_confirm_fields(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("确认信息不能为空")
        return normalized


class StudentBulkDeleteAssociationSummary(BaseModel):
    score_count: int = 0
    score_snapshot_count: int = 0
    growth_record_count: int = 0
    attachment_count: int = 0
    class_history_count: int = 0
    recommendation_count: int = 0
    volunteer_draft_count: int = 0
    gaokao_score_projection_count: int = 0
    pathway_profile_count: int = 0
    pathway_evaluation_count: int = 0


class StudentBulkDeletePreviewItem(BaseModel):
    student_id: int
    student_no: str | None = None
    student_name: str | None = None
    current_class_id: int | None = None
    current_class_name: str | None = None
    status: Literal["deletable", "blocked"]
    reason: str | None = None
    message: str
    association_counts: StudentBulkDeleteAssociationSummary = Field(
        default_factory=StudentBulkDeleteAssociationSummary
    )


class StudentBulkDeletePreviewResponse(BaseModel):
    total: int
    deletable_count: int
    blocked_count: int
    mode: Literal["soft_delete"]
    required_confirm_text: str
    confirm_token: str
    items: list[StudentBulkDeletePreviewItem] = Field(default_factory=list)
    warnings: list[StudentBulkDeletePreviewItem] = Field(default_factory=list)
    blocked: list[StudentBulkDeletePreviewItem] = Field(default_factory=list)


class StudentBulkDeleteExecuteItem(BaseModel):
    student_id: int
    student_no: str | None = None
    student_name: str | None = None
    status: Literal["success", "blocked", "failed"]
    message: str
    error_message: str | None = None
    before_snapshot_json: dict | None = None
    after_snapshot_json: dict | None = None
    association_counts: StudentBulkDeleteAssociationSummary = Field(
        default_factory=StudentBulkDeleteAssociationSummary
    )


class StudentBulkDeleteExecuteResponse(BaseModel):
    total: int
    success_count: int
    failed_count: int
    blocked_count: int
    status: Literal["success", "partially_failed", "failed"]
    mode: Literal["soft_delete"]
    message: str
    audit_log_id: int | None = None
    items: list[StudentBulkDeleteExecuteItem] = Field(default_factory=list)
    success_items: list[StudentBulkDeleteExecuteItem] = Field(default_factory=list)
    failed_items: list[StudentBulkDeleteExecuteItem] = Field(default_factory=list)
    blocked: list[StudentBulkDeleteExecuteItem] = Field(default_factory=list)


class StudentClassTransferBaseRequest(BaseModel):
    student_ids: list[int] = Field(min_length=1, max_length=1000)
    target_class_id: int
    effective_on: date
    reason: str = Field(min_length=1, max_length=255)
    note: str | None = Field(default=None, max_length=1000)
    operator_name: str | None = Field(default=None, max_length=80)
    allow_cross_grade: bool = False

    @field_validator("student_ids")
    @classmethod
    def validate_student_ids(cls, value: list[int]) -> list[int]:
        normalized: list[int] = []
        seen: set[int] = set()
        for student_id in value:
            if student_id <= 0:
                raise ValueError("学生 ID 必须为正整数")
            if student_id in seen:
                continue
            seen.add(student_id)
            normalized.append(student_id)
        if not normalized:
            raise ValueError("请至少选择 1 名学生")
        return normalized

    @field_validator("target_class_id")
    @classmethod
    def validate_target_class_id(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("目标班级 ID 必须为正整数")
        return value

    @field_validator("reason")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("文本不能为空")
        return normalized

    @field_validator("note", "operator_name")
    @classmethod
    def trim_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class StudentClassTransferPreviewRequest(StudentClassTransferBaseRequest):
    pass


class StudentClassTransferExecuteRequest(StudentClassTransferBaseRequest):
    confirm_token: str = Field(min_length=16, max_length=128)
    confirm_text: str = Field(min_length=1, max_length=80)

    @field_validator("confirm_token", "confirm_text")
    @classmethod
    def trim_confirm_fields(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("确认信息不能为空")
        return normalized


class StudentClassTransferPreviewItem(BaseModel):
    student_id: int
    student_no: str | None = None
    student_name: str | None = None
    from_grade_id: int | None = None
    from_grade_name: str | None = None
    from_class_id: int | None = None
    from_class_name: str | None = None
    to_grade_id: int | None = None
    to_grade_name: str | None = None
    to_class_id: int | None = None
    to_class_name: str | None = None
    status: Literal["transferable", "blocked"]
    reason: str | None = None
    message: str
    warnings: list[str] = Field(default_factory=list)


class StudentClassTransferPreviewResponse(BaseModel):
    total: int
    transferable_count: int
    blocked_count: int
    target_class_id: int
    target_class_name: str
    target_grade_id: int | None = None
    target_grade_name: str | None = None
    effective_on: date
    required_confirm_text: str
    confirm_token: str
    items: list[StudentClassTransferPreviewItem] = Field(default_factory=list)
    warnings: list[StudentClassTransferPreviewItem] = Field(default_factory=list)
    blocked: list[StudentClassTransferPreviewItem] = Field(default_factory=list)


class StudentClassTransferExecuteItem(BaseModel):
    student_id: int
    batch_item_id: int | None = None
    student_no: str | None = None
    student_name: str | None = None
    from_grade_id: int | None = None
    from_grade_name: str | None = None
    from_class_id: int | None = None
    from_class_name: str | None = None
    to_grade_id: int | None = None
    to_grade_name: str | None = None
    to_class_id: int | None = None
    to_class_name: str | None = None
    status: Literal["success", "blocked", "failed"]
    message: str
    error_message: str | None = None
    before_snapshot_json: dict | None = None
    after_snapshot_json: dict | None = None


class StudentClassTransferExecuteResponse(BaseModel):
    total: int
    success_count: int
    failed_count: int
    blocked_count: int
    status: Literal["success", "partially_failed", "failed"]
    message: str
    batch_id: int | None = None
    audit_log_id: int | None = None
    items: list[StudentClassTransferExecuteItem] = Field(default_factory=list)
    success_items: list[StudentClassTransferExecuteItem] = Field(default_factory=list)
    failed_items: list[StudentClassTransferExecuteItem] = Field(default_factory=list)
    blocked: list[StudentClassTransferExecuteItem] = Field(default_factory=list)


class StudentClassTransferHistoryItem(BaseModel):
    event_type: Literal["class_transfer"] = "class_transfer"
    title: str
    summary: str
    batch_id: int
    item_id: int
    student_id: int
    student_no: str | None = None
    student_name: str | None = None
    from_grade_id: int | None = None
    from_grade_name: str | None = None
    from_class_id: int | None = None
    from_class_name: str | None = None
    to_grade_id: int | None = None
    to_grade_name: str | None = None
    to_class_id: int | None = None
    to_class_name: str | None = None
    effective_on: date
    reason: str
    note: str | None = None
    operator_name: str | None = None
    status: str
    error_message: str | None = None
    created_at: datetime


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
    score_value_type: str = "original"
    score_value_label: str = "原始分"
    class_rank: int | None = None
    grade_rank: int | None = None
    class_percentile: float | None = None
    grade_percentile: float | None = None
    subjects: list["StudentExamSubjectItem"] = Field(default_factory=list)


class StudentExamSubjectItem(BaseModel):
    subject_id: int
    subject_name: str
    score: float | None = None
    score_value_type: str = "original"
    score_value_label: str = "原始分"
    class_rank: int | None = None
    grade_rank: int | None = None


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
    watch_count: int = 0


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
    latest_score_value_type: str | None = None
    latest_score_value_label: str | None = None
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
