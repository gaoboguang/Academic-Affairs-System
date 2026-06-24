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


class ScoreQuestionImportResponse(ImportResult):
    batch_id: int
    snapshot_count: int = 0


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


class ExamAnalyzableStudentItem(BaseModel):
    id: int
    student_no: str
    name: str
    current_grade_id: int | None = None
    current_grade_name: str | None = None
    current_class_id: int | None = None
    current_class_name: str | None = None
    total_score: float | None = None
    class_rank: int | None = None
    grade_rank: int | None = None
    grade_percentile: float | None = None


class ExamAnalyzableStudentListResponse(BaseModel):
    exam_id: int
    total: int
    items: list[ExamAnalyzableStudentItem] = Field(default_factory=list)


class ExamScoreReportSubject(BaseModel):
    subject_id: int
    subject_name: str
    full_score: float | None = None
    sort_order: int = 0
    is_in_total: bool = True


class ExamScoreReportSubjectScore(BaseModel):
    subject_id: int
    subject_name: str
    score: float | None = None
    original_score: float | None = None
    converted_score: float | None = None
    score_value_type: str = "original"
    score_value_label: str = "原始分"
    class_rank: int | None = None
    grade_rank: int | None = None
    grade_percentile: float | None = None
    excellent_flag: bool = False
    pass_flag: bool = False


class ExamScoreReportRow(BaseModel):
    student_id: int
    student_no: str
    student_name: str
    class_id: int | None = None
    class_name: str | None = None
    total_score: float | None = None
    score_value_type: str = "original"
    score_value_label: str = "原始分"
    class_rank: int | None = None
    grade_rank: int | None = None
    grade_percentile: float | None = None
    subject_scores: list[ExamScoreReportSubjectScore] = Field(default_factory=list)


class ExamScoreReportSummary(BaseModel):
    student_count: int = 0
    subject_count: int = 0
    total_average: float | None = None
    total_max: float | None = None
    total_min: float | None = None


class ExamScoreReportResponse(BaseModel):
    exam_id: int
    exam_name: str
    rank_scope_label: str = "校内名次（本次有效导入样本）"
    subjects: list[ExamScoreReportSubject] = Field(default_factory=list)
    summary: ExamScoreReportSummary = Field(default_factory=ExamScoreReportSummary)
    rows: list[ExamScoreReportRow] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 50


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


class StudentKnowledgePointAnalytics(BaseModel):
    subject_id: int
    subject_name: str
    knowledge_point_id: int
    knowledge_point_name: str
    knowledge_path: str | None = None
    score: float
    full_score: float
    score_rate: float | None = None
    grade_average_rate: float | None = None
    grade_gap_rate: float | None = None
    lost_score: float
    priority_score: float
    diagnosis_label: str
    error_tag_stats: list[dict[str, object]] = Field(default_factory=list)
    dominant_error_tag: str | None = None
    question_count: int
    question_numbers: list[str] = Field(default_factory=list)
    suggestion: str | None = None


class StudentKnowledgeTrendPoint(BaseModel):
    exam_id: int
    exam_name: str
    exam_date: date
    score_rate: float | None = None
    grade_average_rate: float | None = None
    grade_gap_rate: float | None = None
    full_score: float
    lost_score: float
    diagnosis_label: str
    dominant_error_tag: str | None = None
    question_numbers: list[str] = Field(default_factory=list)


class StudentKnowledgeTrendAnalytics(BaseModel):
    subject_id: int
    subject_name: str
    knowledge_point_id: int
    knowledge_point_name: str
    knowledge_path: str | None = None
    trend_exam_count: int
    weak_exam_count: int
    latest_score_rate: float | None = None
    average_score_rate: float | None = None
    latest_grade_gap_rate: float | None = None
    average_grade_gap_rate: float | None = None
    trend_delta: float | None = None
    total_full_score: float
    total_lost_score: float
    priority_score: float
    trend_label: str
    error_tag_stats: list[dict[str, object]] = Field(default_factory=list)
    dominant_error_tag: str | None = None
    points: list[StudentKnowledgeTrendPoint] = Field(default_factory=list)
    suggestion: str | None = None


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


class StudentTrendShape(BaseModel):
    label: str = "数据不足"
    slope: float | None = None
    summary: str = ""


class StudentStabilityMetric(BaseModel):
    level: str = "unknown"
    rank_stddev: float | None = None
    score_cv: float | None = None
    sample_count: int = 0
    summary: str = ""


class StudentSubjectTrendShape(BaseModel):
    subject_id: int
    subject_name: str
    label: str = "数据不足"
    slope: float | None = None
    stability_level: str = "unknown"
    sparkline: list[float | None] = Field(default_factory=list)


class StudentSubjectStructurePoint(BaseModel):
    subject_id: int
    subject_name: str
    student_t_score: float | None = None
    class_average_t: float = 50.0
    z_score: float | None = None


class StudentSubjectLossConcentration(BaseModel):
    subject_id: int
    subject_name: str
    top_paths: list[str] = Field(default_factory=list)
    loss_share: float | None = None  # 0..1, share of subject's lost points by top knowledge points


class StudentSubjectStructure(BaseModel):
    radar_points: list[StudentSubjectStructurePoint] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    loss_concentration: list[StudentSubjectLossConcentration] = Field(default_factory=list)
    summary: str = ""


class StudentPeerSubjectGap(BaseModel):
    subject_id: int
    subject_name: str
    student_score: float | None = None
    peer_average: float | None = None
    gap: float | None = None  # student - peer (negative = behind)
    gap_rank_in_peers: int | None = None  # 1 = top of the peer cohort


class StudentPeerComparison(BaseModel):
    peer_count: int = 0
    peer_radius: int = 0
    peer_total_average: float | None = None
    peer_sample_note: str | None = None
    subject_gaps: list[StudentPeerSubjectGap] = Field(default_factory=list)
    laggard_subjects: list[str] = Field(default_factory=list)


class StudentTargetSubjectPlan(BaseModel):
    subject_id: int
    subject_name: str
    gain_needed: float
    feasibility: str = "unknown"  # high / medium / low / unknown
    note: str = ""


class StudentTargetProgress(BaseModel):
    line_id: int | None = None
    line_name: str
    line_kind: str = "score"  # score / rank
    current_score: float | None = None
    target_score: float | None = None
    gap: float | None = None
    trend_estimate: float | None = None  # projected change in score over next exam
    reach_probability_level: str = "unknown"
    reach_probability: float | None = None
    required_subject_combos: list[StudentTargetSubjectPlan] = Field(default_factory=list)
    note: str = ""


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
    target_progress: list[StudentTargetProgress] = Field(default_factory=list)
    trend_points: list[StudentTotalTrendPoint] = Field(default_factory=list)
    subject_trends: list[StudentSubjectTrendSeries] = Field(default_factory=list)
    trend_shape: StudentTrendShape = Field(default_factory=StudentTrendShape)
    stability: StudentStabilityMetric = Field(default_factory=StudentStabilityMetric)
    subject_trend_shapes: list[StudentSubjectTrendShape] = Field(default_factory=list)
    subject_structure: StudentSubjectStructure = Field(default_factory=StudentSubjectStructure)
    peer_comparison: StudentPeerComparison = Field(default_factory=StudentPeerComparison)
    knowledge_points: list[StudentKnowledgePointAnalytics] = Field(default_factory=list)
    knowledge_trends: list[StudentKnowledgeTrendAnalytics] = Field(default_factory=list)
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


class GradeExamAnomaly(BaseModel):
    is_outlier: bool = False
    median_drop: float | None = None
    spread_change: float | None = None
    sample_size: int = 0
    reason: str = ""
    recommendation: str = ""


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
    exam_anomaly: GradeExamAnomaly = Field(default_factory=GradeExamAnomaly)


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
