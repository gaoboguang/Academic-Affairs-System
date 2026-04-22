from __future__ import annotations

from datetime import date

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


class StudentSubjectAnalytics(BaseModel):
    subject_id: int
    subject_name: str
    score: float | None = None
    score_status: str
    class_rank: int | None = None
    grade_rank: int | None = None
    class_percentile: float | None = None
    grade_percentile: float | None = None
    excellent_flag: bool = False
    pass_flag: bool = False
    score_delta: float | None = None
    rank_delta: int | None = None


class StudentAnalyticsResponse(BaseModel):
    exam_id: int
    exam_name: str
    student_id: int
    student_name: str
    total_score: float
    class_rank: int | None = None
    grade_rank: int | None = None
    class_percentile: float | None = None
    grade_percentile: float | None = None
    previous_exam_id: int | None = None
    previous_exam_name: str | None = None
    total_score_delta: float | None = None
    class_rank_delta: int | None = None
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
