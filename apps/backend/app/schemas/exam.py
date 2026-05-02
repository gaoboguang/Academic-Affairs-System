from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ImportResult, ORMModel


class ExamPayload(BaseModel):
    name: str
    exam_type: str
    exam_date: date
    semester_id: int
    grade_scope_json: list[int] = Field(default_factory=list)
    is_trend_enabled: bool = True
    status: str = "draft"
    note: str | None = None
    is_active: bool = True


class ExamRead(ORMModel):
    id: int
    name: str
    exam_type: str
    exam_date: date
    semester_id: int
    semester_name: str | None = None
    grade_scope_json: list[int] | None = None
    grade_scope_names: list[str] = Field(default_factory=list)
    is_trend_enabled: bool
    status: str
    note: str | None = None
    is_active: bool
    subject_count: int = 0


class ExamSubjectPayload(BaseModel):
    subject_id: int
    full_score: float
    is_in_total: bool = True
    excellent_line: float | None = None
    pass_line: float | None = None
    sort_order: int = 0
    is_active: bool = True


class ExamSubjectRead(ORMModel):
    id: int
    exam_id: int
    subject_id: int
    subject_name: str | None = None
    full_score: float
    is_in_total: bool
    excellent_line: float | None = None
    pass_line: float | None = None
    sort_order: int
    is_active: bool


class ExamListResponse(BaseModel):
    items: list[ExamRead]
    total: int
    page: int
    page_size: int


class ScoreImportResponse(ImportResult):
    batch_id: int
    profile_id: int | None = None
    detection_summary: dict[str, Any] | None = None


class ScoreImportMappingPayload(BaseModel):
    layout_type: str
    sheet_name: str | None = None
    header_row: int = 1
    field_mapping: dict[str, str] = Field(default_factory=dict)
    subject_mapping: dict[str, str] = Field(default_factory=dict)
    subject_score_types: dict[str, str] = Field(default_factory=dict)
    ignored_columns: list[str] = Field(default_factory=list)
    metadata_mapping: dict[str, str] = Field(default_factory=dict)


class ScoreImportPreviewResponse(BaseModel):
    source_filename: str | None = None
    sheet_name: str | None = None
    header_row: int
    layout_type: str
    confidence: float
    messages: list[str] = Field(default_factory=list)
    columns: list[dict[str, Any]] = Field(default_factory=list)
    sample_rows: list[dict[str, Any]] = Field(default_factory=list)
    normalized_preview: list[dict[str, Any]] = Field(default_factory=list)
    mapping: ScoreImportMappingPayload
    import_ready: bool
    source_row_count: int
    detected_record_count: int


class ScoreImportProfileRead(ORMModel):
    id: int
    name: str
    layout_type: str
    sheet_name: str | None = None
    header_row: int
    field_mapping_json: dict[str, str] = Field(default_factory=dict)
    subject_mapping_json: dict[str, str] = Field(default_factory=dict)
    subject_score_type_json: dict[str, str] = Field(default_factory=dict)
    ignored_columns_json: list[str] = Field(default_factory=list)
    metadata_mapping_json: dict[str, str] = Field(default_factory=dict)
    description: str | None = None
    is_active: bool


class ScoreClassMappingPayload(BaseModel):
    source_class_name: str
    mapped_class_id: int | None = None
    mapping_status: str = "mapped"
    note: str | None = None


class ScoreClassMappingRead(ORMModel):
    id: int
    exam_id: int
    source_class_name: str
    mapped_class_id: int | None = None
    mapped_class_name: str | None = None
    mapping_status: str
    note: str | None = None
    student_count: int = 0


class ScoreTargetLinePayload(BaseModel):
    name: str
    line_type: str
    score_value: float | None = None
    rank_value: int | None = None
    near_margin_score: float | None = None
    near_margin_rank: int | None = None
    sort_order: int = 0
    note: str | None = None
    is_active: bool = True


class ScoreTargetLineRead(ORMModel):
    id: int
    exam_id: int
    name: str
    line_type: str
    score_value: float | None = None
    rank_value: int | None = None
    near_margin_score: float | None = None
    near_margin_rank: int | None = None
    sort_order: int
    note: str | None = None
    is_active: bool


class ScoreRankDiffItem(BaseModel):
    student_id: int
    student_name: str
    source_class_name: str | None = None
    mapped_class_name: str | None = None
    total_score: float | None = None
    system_class_rank: int | None = None
    source_class_rank: int | None = None
    class_rank_delta: int | None = None
    system_school_rank: int | None = None
    source_school_rank: int | None = None
    school_rank_delta: int | None = None


class ScoreRankAuditResponse(BaseModel):
    exam_id: int
    exam_name: str
    rank_scope_label: str = "校内名次（本次有效导入样本）"
    total_students: int = 0
    context_count: int = 0
    mapped_context_count: int = 0
    unmapped_context_count: int = 0
    mapping_rate: float = 0.0
    source_class_count: int = 0
    mapped_class_count: int = 0
    source_rank_count: int = 0
    rank_diff_count: int = 0
    max_abs_class_rank_delta: int | None = None
    max_abs_school_rank_delta: int | None = None
    warnings: list[str] = Field(default_factory=list)
    class_mappings: list[ScoreClassMappingRead] = Field(default_factory=list)
    rank_diffs: list[ScoreRankDiffItem] = Field(default_factory=list)


class ScoreRebuildResponse(BaseModel):
    message: str
    audit: ScoreRankAuditResponse


class StudentTargetLineGap(BaseModel):
    line_id: int
    line_name: str
    line_type: str
    threshold_label: str
    threshold_score: float | None = None
    reached: bool
    gap_score: float | None = None
    gap_rank: int | None = None
    status: str = "unknown"


class StudentSubjectEffectiveTarget(BaseModel):
    line_id: int
    line_name: str
    target_score: float
    actual_score: float | None = None
    gap_score: float | None = None
    basis: str = "年级均分贡献"


class StudentSubjectAnalytics(BaseModel):
    subject_id: int
    subject_name: str
    score: float | None = None
    original_score: float | None = None
    converted_score: float | None = None
    score_value_type: str = "original"
    score_value_label: str = "原始分"
    score_status: str
    class_rank: int | None = None
    grade_rank: int | None = None
    class_percentile: float | None = None
    grade_percentile: float | None = None
    excellent_flag: bool = False
    pass_flag: bool = False
    score_delta: float | None = None
    rank_delta: int | None = None
    z_score: float | None = None
    t_score: float | None = None
    rank_deviation: int | None = None
    peer_average_score: float | None = None
    peer_average_delta: float | None = None
    peer_sample_count: int = 0
    peer_sample_note: str | None = None
    trend_rank_stddev: float | None = None
    trend_exam_count: int = 0
    effective_score_targets: list[StudentSubjectEffectiveTarget] = Field(default_factory=list)
    primary_effective_line_name: str | None = None
    primary_effective_score: float | None = None
    primary_effective_score_gap: float | None = None
    diagnosis: str = "正常"
    diagnosis_tags: list[str] = Field(default_factory=list)


class StudentTotalTrendPoint(BaseModel):
    exam_id: int
    exam_name: str
    exam_date: date
    total_score: float | None = None
    class_rank: int | None = None
    grade_rank: int | None = None
    grade_percentile: float | None = None


class StudentSubjectTrendPoint(BaseModel):
    exam_id: int
    exam_name: str
    exam_date: date
    score: float | None = None
    grade_rank: int | None = None
    grade_percentile: float | None = None


class StudentSubjectTrendSeries(BaseModel):
    subject_id: int
    subject_name: str
    points: list[StudentSubjectTrendPoint] = Field(default_factory=list)


class StudentActionSuggestion(BaseModel):
    category: str
    title: str
    summary: str
    subject_names: list[str] = Field(default_factory=list)
    priority: int = 0


class StudentAnalyticsResponse(BaseModel):
    exam_id: int
    exam_name: str
    student_id: int
    student_name: str
    total_score: float
    score_value_type: str = "original"
    score_value_label: str = "原始分"
    class_rank: int | None = None
    grade_rank: int | None = None
    class_percentile: float | None = None
    grade_percentile: float | None = None
    previous_exam_id: int | None = None
    previous_exam_name: str | None = None
    total_score_delta: float | None = None
    class_rank_delta: int | None = None
    grade_rank_delta: int | None = None
    overview_sentence: str = ""
    target_line_gaps: list[StudentTargetLineGap] = Field(default_factory=list)
    trend_points: list[StudentTotalTrendPoint] = Field(default_factory=list)
    subject_trends: list[StudentSubjectTrendSeries] = Field(default_factory=list)
    action_suggestions: list[StudentActionSuggestion] = Field(default_factory=list)
    subjects: list[StudentSubjectAnalytics]


class SubjectAggregateItem(BaseModel):
    subject_id: int
    subject_name: str
    average_score: float
    median_score: float
    max_score: float
    min_score: float
    standard_deviation: float
    excellent_rate: float
    pass_rate: float
    valid_count: int


class ClassAnalyticsResponse(BaseModel):
    exam_id: int
    exam_name: str
    class_id: int
    class_name: str
    student_count: int
    total_average: float
    total_median: float
    total_max: float
    total_min: float
    total_standard_deviation: float
    grade_average: float | None = None
    subject_breakdown: list[SubjectAggregateItem]


class TeacherAssignmentAnalytics(BaseModel):
    assignment_id: int
    class_id: int | None = None
    class_name: str | None = None
    subject_id: int | None = None
    subject_name: str | None = None
    average_score: float
    excellent_rate: float
    pass_rate: float
    valid_count: int


class TeacherAnalyticsResponse(BaseModel):
    exam_id: int
    exam_name: str
    teacher_id: int
    teacher_name: str
    overall_average: float | None = None
    assignment_breakdown: list[TeacherAssignmentAnalytics]


class GradeClassAnalyticsItem(BaseModel):
    class_id: int | None = None
    class_name: str
    student_count: int
    average_score: float
    median_score: float
    max_score: float
    min_score: float
    excellent_rate: float | None = None
    target_line_counts: dict[str, int] = Field(default_factory=dict)
    target_line_rates: dict[str, float] = Field(default_factory=dict)


class GradeSubjectAnalyticsItem(BaseModel):
    subject_id: int
    subject_name: str
    valid_count: int
    average_score: float
    excellent_rate: float
    pass_rate: float
    contribution_rate: float | None = None


class GradeDistributionItem(BaseModel):
    label: str
    count: int


class GradeTargetLineSummary(BaseModel):
    line_id: int
    line_name: str
    line_type: str
    threshold_label: str
    reached_count: int
    reached_rate: float
    near_below_count: int
    near_above_count: int


class GradeCriticalStudentItem(BaseModel):
    student_id: int
    student_no: str | None = None
    student_name: str
    class_id: int | None = None
    class_name: str | None = None
    total_score: float
    school_rank: int | None = None
    line_name: str
    status: str
    gap_label: str


class GradeClassContributionItem(BaseModel):
    class_id: int | None = None
    class_name: str
    student_count: int
    average_score: float
    top30_count: int = 0
    target_line_counts: dict[str, int] = Field(default_factory=dict)
    strongest_subject: str | None = None
    weakest_subject: str | None = None


class GradeRankAuditSummary(BaseModel):
    rank_scope_label: str = "校内名次（本次有效导入样本）"
    mapping_rate: float = 0.0
    unmapped_context_count: int = 0
    rank_diff_count: int = 0
    warnings: list[str] = Field(default_factory=list)


class GradeAnalyticsResponse(BaseModel):
    exam_id: int
    exam_name: str
    grade_id: int
    grade_name: str
    student_count: int
    total_average: float
    total_median: float
    total_max: float
    total_min: float
    total_standard_deviation: float
    excellent_rate: float | None = None
    class_breakdown: list[GradeClassAnalyticsItem]
    subject_breakdown: list[GradeSubjectAnalyticsItem]
    score_bands: list[GradeDistributionItem]
    rank_bands: list[GradeDistributionItem]
    target_line_summaries: list[GradeTargetLineSummary] = Field(default_factory=list)
    critical_students: list[GradeCriticalStudentItem] = Field(default_factory=list)
    class_contributions: list[GradeClassContributionItem] = Field(default_factory=list)
    rank_audit_summary: GradeRankAuditSummary | None = None


class GradePanoramaExamPointRead(BaseModel):
    exam_id: int
    exam_name: str
    exam_date: date
    academic_year_id: int | None = None
    academic_year_name: str | None = None
    semester_name: str | None = None
    student_count: int
    total_average: float
    total_median: float
    excellent_rate: float | None = None
    top10_count: int = 0
    top30_count: int = 0


class GradePanoramaYearSummaryRead(BaseModel):
    academic_year_id: int
    academic_year_name: str
    exam_count: int
    average_score: float
    average_excellent_rate: float | None = None
    best_exam_name: str
    latest_exam_name: str


class GradePanoramaSubjectPointRead(BaseModel):
    exam_id: int
    exam_name: str
    exam_date: date
    academic_year_name: str | None = None
    average_score: float
    excellent_rate: float
    valid_count: int


class GradePanoramaSubjectTrendRead(BaseModel):
    subject_id: int
    subject_name: str
    points: list[GradePanoramaSubjectPointRead] = Field(default_factory=list)


class GradePanoramaResponse(BaseModel):
    grade_id: int
    grade_name: str
    academic_year_count: int
    exam_count: int
    year_summaries: list[GradePanoramaYearSummaryRead] = Field(default_factory=list)
    exam_points: list[GradePanoramaExamPointRead] = Field(default_factory=list)
    subject_trends: list[GradePanoramaSubjectTrendRead] = Field(default_factory=list)


class ClassPanoramaResponse(BaseModel):
    class_id: int
    class_name: str
    academic_year_count: int
    exam_count: int
    year_summaries: list[GradePanoramaYearSummaryRead] = Field(default_factory=list)
    exam_points: list[GradePanoramaExamPointRead] = Field(default_factory=list)
    subject_trends: list[GradePanoramaSubjectTrendRead] = Field(default_factory=list)


class TeacherPanoramaResponse(BaseModel):
    teacher_id: int
    teacher_name: str
    academic_year_count: int
    exam_count: int
    year_summaries: list[GradePanoramaYearSummaryRead] = Field(default_factory=list)
    exam_points: list[GradePanoramaExamPointRead] = Field(default_factory=list)
    subject_trends: list[GradePanoramaSubjectTrendRead] = Field(default_factory=list)
