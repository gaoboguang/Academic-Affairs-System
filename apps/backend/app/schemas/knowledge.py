from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import ImportResult, ORMModel
from app.schemas.planning import PlanningTaskRead


class KnowledgePointNodeRead(BaseModel):
    id: int
    subject_id: int
    subject_name: str | None = None
    parent_id: int | None = None
    name: str
    code: str | None = None
    description: str | None = None
    sort_order: int = 0
    source_type: str = "manual"
    path: str
    is_active: bool = True
    children: list["KnowledgePointNodeRead"] = Field(default_factory=list)


class KnowledgeTreeResponse(BaseModel):
    subject_id: int | None = None
    items: list[KnowledgePointNodeRead] = Field(default_factory=list)


class KnowledgePointPayload(BaseModel):
    subject_id: int
    name: str
    parent_id: int | None = None
    code: str | None = None
    description: str | None = None
    sort_order: int = 0
    source_type: str = "manual"
    is_active: bool = True


class KnowledgePointRead(ORMModel):
    id: int
    subject_id: int
    parent_id: int | None = None
    name: str
    code: str | None = None
    description: str | None = None
    sort_order: int = 0
    source_type: str = "manual"
    is_active: bool
    path: str | None = None


class KnowledgePointAliasPayload(BaseModel):
    subject_id: int
    knowledge_point_id: int
    alias_name: str
    source_type: str = "manual"
    note: str | None = None
    is_active: bool = True


class KnowledgePointAliasRead(ORMModel):
    id: int
    subject_id: int
    subject_name: str | None = None
    knowledge_point_id: int
    knowledge_point_name: str | None = None
    knowledge_point_path: str | None = None
    alias_name: str
    normalized_alias: str
    source_type: str
    note: str | None = None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ErrorReasonTagPayload(BaseModel):
    name: str
    description: str | None = None
    sort_order: int = 0
    is_builtin: bool = False
    is_active: bool = True


class ErrorReasonTagRead(ORMModel):
    id: int
    name: str
    normalized_name: str
    description: str | None = None
    sort_order: int = 0
    is_builtin: bool = False
    is_active: bool


class KnowledgeBaseImportResponse(ImportResult):
    point_count: int = 0
    alias_count: int = 0
    error_tag_count: int = 0


class KnowledgeErrorTagStat(BaseModel):
    tag: str
    count: int


class KnowledgeTaskCandidate(BaseModel):
    student_id: int
    student_name: str
    class_name: str | None = None
    subject_id: int
    subject_name: str
    knowledge_point_id: int
    knowledge_point_name: str
    knowledge_path: str | None = None
    source_ref_id: str
    title: str
    description: str
    priority: str = "medium"
    due_date: date | None = None
    reason: str
    existing_task_id: int | None = None
    will_create: bool = True


class KnowledgeTaskPreviewResponse(BaseModel):
    exam_id: int
    student_id: int | None = None
    class_id: int | None = None
    due_date: date | None = None
    candidates: list[KnowledgeTaskCandidate] = Field(default_factory=list)
    create_count: int = 0
    skip_count: int = 0
    notices: list[str] = Field(default_factory=list)


class KnowledgeTaskGeneratePayload(BaseModel):
    due_date: date | None = None
    knowledge_point_ids: list[int] = Field(default_factory=list)


class KnowledgeTaskGenerateResponse(BaseModel):
    created_count: int
    skipped_count: int
    tasks: list[PlanningTaskRead] = Field(default_factory=list)
    notices: list[str] = Field(default_factory=list)


class ClassKnowledgeBriefingStudent(BaseModel):
    student_id: int
    student_name: str
    student_no: str | None = None
    class_name: str | None = None
    score_rate: float | None = None
    lost_score: float = 0
    diagnosis_label: str
    main_error_tag: str | None = None


class ClassKnowledgeBriefingItem(BaseModel):
    subject_id: int
    subject_name: str
    knowledge_point_id: int
    knowledge_point_name: str
    knowledge_path: str | None = None
    weak_student_count: int
    total_student_count: int
    average_score_rate: float | None = None
    grade_average_rate: float | None = None
    lost_score_total: float
    question_numbers: list[str] = Field(default_factory=list)
    error_tag_stats: list[KnowledgeErrorTagStat] = Field(default_factory=list)
    priority_score: float
    priority_label: str
    suggestion: str
    weak_students: list[ClassKnowledgeBriefingStudent] = Field(default_factory=list)


class ClassKnowledgeBriefingResponse(BaseModel):
    exam_id: int
    exam_name: str
    class_id: int
    class_name: str
    subject_id: int | None = None
    generated_at: datetime
    items: list[ClassKnowledgeBriefingItem] = Field(default_factory=list)
    notices: list[str] = Field(default_factory=list)
