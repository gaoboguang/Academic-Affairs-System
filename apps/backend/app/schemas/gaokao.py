from __future__ import annotations

from pydantic import BaseModel, Field


class GaokaoTableStatRead(BaseModel):
    key: str
    label: str
    record_total: int = 0
    covered_total: int | None = None
    coverage_rate: float | None = None
    latest_updated_at: str | None = None
    latest_batch_label: str | None = None
    status: str = "empty"
    notes: list[str] = Field(default_factory=list)


class GaokaoDataOverviewRead(BaseModel):
    source_mode: str
    data_version: str | None = None
    generated_at: str | None = None
    school_total: int = 0
    recruit_site_covered: int = 0
    recruit_site_coverage_rate: float | None = None
    chapter_url_covered: int = 0
    chapter_url_coverage_rate: float | None = None
    fallback_url_covered: int = 0
    duplicate_group_total: int | None = None
    same_name_cross_site_group_total: int | None = None
    recent_batch_label: str | None = None
    last_updated_at: str | None = None
    notes: list[str] = Field(default_factory=list)
    core_tables: list[GaokaoTableStatRead] = Field(default_factory=list)


class GaokaoDataHealthTableRead(BaseModel):
    key: str
    label: str
    count: int = 0
    status: str = "empty"
    explanation: str | None = None
    notes: list[str] = Field(default_factory=list)


class GaokaoDataHealthTypeRead(BaseModel):
    key: str
    label: str | None = None
    count: int = 0


class GaokaoDataHealthYearBreakdownRead(BaseModel):
    year: int
    total: int = 0
    student_types: list[GaokaoDataHealthTypeRead] = Field(default_factory=list)
    batches: list[GaokaoDataHealthTypeRead] = Field(default_factory=list)
    status: str = "empty"


class GaokaoDataHealthCoverageRead(BaseModel):
    key: str
    label: str
    status: str = "empty"
    total: int = 0
    years: list[int] = Field(default_factory=list)
    missing_years: list[int] = Field(default_factory=list)
    readiness: str = "unknown"
    readiness_label: str | None = None
    risk_level: str = "normal"
    explanation: str | None = None
    notes: list[str] = Field(default_factory=list)
    student_types: list[GaokaoDataHealthTypeRead] = Field(default_factory=list)
    batch_distribution: list[GaokaoDataHealthTypeRead] = Field(default_factory=list)
    year_breakdown: list[GaokaoDataHealthYearBreakdownRead] = Field(default_factory=list)


class GaokaoDataAuditItemRead(BaseModel):
    key: str
    label: str
    status: str = "empty"
    created: int = 0
    updated: int = 0
    duplicates: int = 0
    conflicts: int = 0
    pending_review: int = 0
    notes: list[str] = Field(default_factory=list)


class GaokaoDataFieldExplanationRead(BaseModel):
    field: str
    label: str
    explanation: str


class GaokaoDataDeliveryAssessmentRead(BaseModel):
    status: str
    label: str
    summary: str
    pass_items: list[str] = Field(default_factory=list)
    warning_items: list[str] = Field(default_factory=list)
    blocking_items: list[str] = Field(default_factory=list)


class GaokaoDataSpecialTypeRiskRead(BaseModel):
    key: str
    label: str
    readiness: str
    readiness_label: str
    risk_level: str
    plan_count: int = 0
    raw_plan_count: int = 0
    admission_count: int = 0
    raw_admission_count: int = 0
    score_line_count: int = 0
    volunteer_rule_count: int = 0
    special_rule_count: int = 0
    fallback_modes: list[str] = Field(default_factory=list)
    fallback_labels: list[str] = Field(default_factory=list)
    explanation: str
    notes: list[str] = Field(default_factory=list)


class GaokaoDataHealthRead(BaseModel):
    db_path: str
    exists: bool
    generated_at: str
    schema_version: str | None = None
    province: str = "山东"
    expected_years: list[int] = Field(default_factory=list)
    field_explanations: list[GaokaoDataFieldExplanationRead] = Field(default_factory=list)
    delivery_assessment: GaokaoDataDeliveryAssessmentRead | None = None
    tables: list[GaokaoDataHealthTableRead] = Field(default_factory=list)
    coverage: list[GaokaoDataHealthCoverageRead] = Field(default_factory=list)
    special_type_risks: list[GaokaoDataSpecialTypeRiskRead] = Field(default_factory=list)
    audit_summary: list[GaokaoDataAuditItemRead] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    summary: str


class GaokaoImportBatchRead(BaseModel):
    id: str
    batch_name: str
    source_type: str
    source_filename: str | None = None
    status: str
    started_at: str | None = None
    finished_at: str | None = None
    record_total: int | None = None
    notes: list[str] = Field(default_factory=list)


class GaokaoCollegeOptionRead(BaseModel):
    college_id: int
    college_name: str | None = None
    college_code: str | None = None
    province: str | None = None
    review_status: str | None = None
    source_mode: str


class GaokaoReviewBucketRead(BaseModel):
    code: str
    title: str
    count: int | None = None
    description: str


class GaokaoReviewQuickFilterRead(BaseModel):
    code: str
    title: str
    count: int = 0
    description: str


class GaokaoReviewGroupComparisonFieldRead(BaseModel):
    key: str
    title: str
    status: str = "same"
    distinct_total: int = 0
    missing_total: int = 0
    sample_values: list[str] = Field(default_factory=list)
    summary: str


class GaokaoReviewGroupMemberRead(BaseModel):
    college_id: int | None = None
    college_name: str | None = None
    college_code: str | None = None
    review_status: str | None = None
    province: str | None = None
    official_site: str | None = None
    recruit_site: str | None = None
    chapter_url: str | None = None
    fallback_url: str | None = None
    effective_chapter_url: str | None = None
    source_title: str | None = None
    source_url: str | None = None
    updated_at: str | None = None
    priority_code: str | None = None
    priority_label: str | None = None
    priority_score: int = 0
    priority_reasons: list[str] = Field(default_factory=list)


class GaokaoReviewGroupRead(BaseModel):
    key: str
    title: str
    group_type: str | None = None
    item_count: int
    members: list[str] = Field(default_factory=list)
    member_items: list[GaokaoReviewGroupMemberRead] = Field(default_factory=list)
    comparison_fields: list[GaokaoReviewGroupComparisonFieldRead] = Field(default_factory=list)
    conflict_highlights: list[str] = Field(default_factory=list)
    note: str | None = None
    priority_code: str | None = None
    priority_label: str | None = None
    priority_score: int = 0
    priority_reasons: list[str] = Field(default_factory=list)
    suggested_action: str | None = None
    high_priority_member_total: int = 0
    unresolved_total: int = 0
    missing_chapter_total: int = 0
    missing_recruit_site_total: int = 0


class GaokaoReviewItemRead(BaseModel):
    college_id: int | None = None
    college_name: str | None = None
    college_code: str | None = None
    province: str | None = None
    duplicate_group_key: str | None = None
    same_name_group_key: str | None = None
    review_status: str | None = None
    retrieval_status: str | None = None
    official_site: str | None = None
    recruit_site: str | None = None
    chapter_url: str | None = None
    fallback_url: str | None = None
    source_url: str | None = None
    source_title: str | None = None
    updated_at: str | None = None
    priority_code: str | None = None
    priority_label: str | None = None
    priority_score: int = 0
    priority_reasons: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class GaokaoReviewSummaryRead(BaseModel):
    source_available: bool
    source_mode: str
    active_filter: str = "all"
    active_focus: str = "all"
    active_sort: str = "priority_desc"
    active_keyword: str | None = None
    matched_total: int | None = None
    queue_total: int = 0
    chapter_url_covered: int = 0
    chapter_url_coverage_rate: float | None = None
    duplicate_group_total: int | None = None
    same_name_cross_site_group_total: int | None = None
    counts: list[GaokaoReviewBucketRead] = Field(default_factory=list)
    quick_filters: list[GaokaoReviewQuickFilterRead] = Field(default_factory=list)
    items: list[GaokaoReviewItemRead] = Field(default_factory=list)
    priority_groups: list[GaokaoReviewGroupRead] = Field(default_factory=list)
    duplicate_groups: list[GaokaoReviewGroupRead] = Field(default_factory=list)
    same_name_groups: list[GaokaoReviewGroupRead] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class GaokaoCollegeEvidenceRead(BaseModel):
    source_available: bool
    source_mode: str
    college_id: int
    college_name: str | None = None
    college_code: str | None = None
    province: str | None = None
    official_site: str | None = None
    recruit_site: str | None = None
    chapter_url: str | None = None
    fallback_url: str | None = None
    source_url: str | None = None
    source_title: str | None = None
    review_status: str | None = None
    retrieval_status: str | None = None
    updated_at: str | None = None
    message: str | None = None
    notes: list[str] = Field(default_factory=list)


class GaokaoShandongMonitorRead(BaseModel):
    province: str
    source_mode: str
    data_version: str | None = None
    generated_at: str | None = None
    ready_section_total: int = 0
    gap_section_total: int = 0
    priority_notes: list[str] = Field(default_factory=list)
    sections: list[GaokaoTableStatRead] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
