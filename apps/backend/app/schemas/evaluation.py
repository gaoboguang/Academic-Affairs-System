from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.archive import StoredFileRead
from app.schemas.common import ImportResult, ORMModel


class EvaluationQuestionPayload(BaseModel):
    dimension_name: str
    question_text: str
    score_max: float = 5.0
    weight: float = 1.0
    sort_order: int = 0
    is_active: bool = True


class EvaluationQuestionRead(ORMModel):
    id: int
    template_id: int
    dimension_name: str
    question_text: str
    score_max: float
    weight: float
    sort_order: int
    is_active: bool


class EvaluationTemplatePayload(BaseModel):
    name: str
    target_type: str = "teacher"
    weight_json: dict[str, float] | None = None
    questions: list[EvaluationQuestionPayload] = Field(default_factory=list)
    is_active: bool = True


class EvaluationTemplateRead(ORMModel):
    id: int
    name: str
    target_type: str
    weight_json: dict[str, float] | None = None
    is_active: bool
    questions: list[EvaluationQuestionRead] = Field(default_factory=list)


class EvaluationBatchRead(ORMModel):
    id: int
    template_id: int
    template_name: str | None = None
    semester_id: int
    semester_name: str | None = None
    source_filename: str | None = None
    import_time: datetime
    status: str
    response_count: int = 0
    teacher_count: int = 0
    is_active: bool


class EvaluationImportResponse(ImportResult):
    batch_id: int


class EvaluationTeacherSummaryRead(BaseModel):
    teacher_id: int
    teacher_name: str
    overall_avg_score: float
    response_count: int
    rank: int | None = None
    dimension_scores_json: dict[str, float] | None = None


class EvaluationBatchOverviewRead(BaseModel):
    batch_id: int
    template_name: str
    semester_name: str | None = None
    teacher_count: int
    teacher_summaries: list[EvaluationTeacherSummaryRead] = Field(default_factory=list)


class EvaluationBatchCompareTeacherRead(BaseModel):
    teacher_id: int
    teacher_name: str
    current_score: float
    compare_score: float
    score_delta: float
    current_rank: int | None = None
    compare_rank: int | None = None
    rank_delta: int | None = None
    response_count_delta: int = 0


class EvaluationBatchCompareRead(BaseModel):
    batch_id: int
    compare_batch_id: int
    batch_name: str
    compare_batch_name: str
    overlap_teacher_count: int
    improved_count: int
    declined_count: int
    unchanged_count: int
    only_current_count: int
    only_compare_count: int
    teacher_deltas: list[EvaluationBatchCompareTeacherRead] = Field(default_factory=list)


class EvaluationDimensionSummaryRead(BaseModel):
    dimension_name: str
    avg_score: float
    response_count: int


class EvaluationQuestionStatRead(BaseModel):
    question_text: str
    dimension_name: str
    avg_score: float
    response_count: int


class EvaluationClassStatRead(BaseModel):
    class_id: int | None = None
    class_name: str | None = None
    avg_score: float
    response_count: int


class EvaluationTeacherDetailRead(BaseModel):
    batch_id: int
    teacher_id: int
    teacher_name: str
    overall_avg_score: float
    response_count: int
    dimension_summaries: list[EvaluationDimensionSummaryRead] = Field(default_factory=list)
    question_stats: list[EvaluationQuestionStatRead] = Field(default_factory=list)
    class_stats: list[EvaluationClassStatRead] = Field(default_factory=list)


class EvaluationTeacherTrendPointRead(BaseModel):
    batch_id: int
    template_name: str
    semester_name: str | None = None
    overall_avg_score: float
    response_count: int
    rank: int | None = None
    import_time: datetime


class EvaluationTeacherTrendRead(BaseModel):
    teacher_id: int
    teacher_name: str
    points: list[EvaluationTeacherTrendPointRead] = Field(default_factory=list)


class AdviserQuantRuleVersionPayload(BaseModel):
    name: str
    semester_id: int | None = None
    is_default: bool = False
    status: str = "active"
    note: str | None = None
    is_active: bool = True


class AdviserQuantRuleVersionRead(ORMModel):
    id: int
    name: str
    semester_id: int | None = None
    semester_name: str | None = None
    is_default: bool
    status: str
    note: str | None = None
    is_active: bool


class AdviserQuantRuleItemPayload(BaseModel):
    item_name: str
    item_type: str
    default_score: float = 0.0
    requires_attachment: bool = False
    note: str | None = None
    sort_order: int = 0
    is_active: bool = True


class AdviserQuantRuleItemRead(ORMModel):
    id: int
    rule_version_id: int
    item_name: str
    item_type: str
    default_score: float
    requires_attachment: bool
    note: str | None = None
    sort_order: int
    is_active: bool


class AdviserQuantRecordAttachmentRead(ORMModel):
    id: int
    stored_file_id: int
    note: str | None = None
    file: StoredFileRead


class AdviserQuantRecordPayload(BaseModel):
    teacher_id: int
    class_id: int | None = None
    semester_id: int
    rule_item_id: int
    record_month: str
    score: float | None = None
    description: str | None = None
    attachment_file_ids: list[int] = Field(default_factory=list)
    is_active: bool = True


class AdviserQuantRecordRead(ORMModel):
    id: int
    teacher_id: int
    teacher_name: str | None = None
    class_id: int | None = None
    class_name: str | None = None
    semester_id: int
    semester_name: str | None = None
    rule_version_id: int
    rule_version_name: str | None = None
    rule_item_id: int
    item_name: str
    item_type: str
    record_month: str
    score: float
    requires_attachment: bool
    description: str | None = None
    recorded_at: datetime
    is_active: bool
    attachments: list[AdviserQuantRecordAttachmentRead] = Field(default_factory=list)


class AdviserQuantSummaryRead(BaseModel):
    teacher_id: int
    teacher_name: str
    semester_id: int
    semester_name: str | None = None
    rule_version_id: int | None = None
    rule_version_name: str | None = None
    total_score: float
    positive_score: float
    negative_score: float
    record_count: int
    class_names: list[str] = Field(default_factory=list)
    category_scores_json: dict[str, float] | None = None
