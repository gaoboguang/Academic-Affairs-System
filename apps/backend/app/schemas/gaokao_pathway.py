from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class GaokaoPathwayRulePayload(BaseModel):
    rule_code: str
    rule_name: str
    rule_type: str
    severity: str = "info"
    condition_json: dict[str, object] = Field(default_factory=dict)
    message_template: str | None = None
    source_document_id: int | None = None
    manual_review_required: bool = False
    valid_from_year: int | None = None
    valid_to_year: int | None = None
    is_active: bool = True


class GaokaoPathwayRuleRead(ORMModel):
    id: int
    pathway_id: int
    rule_code: str
    rule_name: str
    rule_type: str
    severity: str
    condition_json: dict[str, object] = Field(default_factory=dict)
    message_template: str | None = None
    source_document_id: int | None = None
    manual_review_required: bool
    valid_from_year: int | None = None
    valid_to_year: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_active: bool


class GaokaoPathwayPayload(BaseModel):
    province: str = "山东"
    pathway_code: str
    pathway_name: str
    pathway_group: str
    student_type: str | None = None
    exam_type: str | None = None
    batch_name: str | None = None
    volunteer_mode: str | None = None
    max_volunteer_count: int | None = None
    recommendation_depth: str
    status: str = "active"
    source_document_id: int | None = None
    summary: str | None = None
    risk_level: str | None = None
    notes_json: dict[str, object] = Field(default_factory=dict)
    is_active: bool = True


class GaokaoPathwayRead(ORMModel):
    id: int
    province: str
    pathway_code: str
    pathway_name: str
    pathway_group: str
    student_type: str | None = None
    exam_type: str | None = None
    batch_name: str | None = None
    volunteer_mode: str | None = None
    max_volunteer_count: int | None = None
    recommendation_depth: str
    status: str
    source_document_id: int | None = None
    summary: str | None = None
    risk_level: str | None = None
    notes_json: dict[str, object] = Field(default_factory=dict)
    rules: list[GaokaoPathwayRuleRead] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_active: bool


class GaokaoPathwayBootstrapResponse(BaseModel):
    province: str
    target_year: int
    total_count: int
    created_count: int
    skipped_count: int
    rule_created_count: int = 0
    rule_skipped_count: int = 0


class StudentPathwayProfilePayload(BaseModel):
    province: str = "山东"
    candidate_type: str | None = None
    exam_type: str | None = None
    subject_combination: str | None = None
    spring_exam_category: str | None = None
    art_track: str | None = None
    sports_track: str | None = None
    has_gaokao_registration: bool | None = None
    is_fresh_graduate: bool | None = None
    is_vocational_student: bool | None = None
    is_social_candidate: bool | None = None
    has_high_school_equivalent: bool | None = None
    accept_private_college: bool | None = None
    accept_sino_foreign: bool | None = None
    accept_junior_college: bool | None = None
    accept_outside_province: bool | None = None
    accept_early_batch: bool | None = None
    accept_service_commitment: bool | None = None
    accept_interview_or_physical_test: bool | None = None
    career_preferences_json: dict[str, object] = Field(default_factory=dict)
    region_preferences_json: dict[str, object] = Field(default_factory=dict)
    family_constraints_json: dict[str, object] = Field(default_factory=dict)
    known_body_limitations_json: dict[str, object] = Field(default_factory=dict)
    materials_json: dict[str, object] = Field(default_factory=dict)
    note: str | None = None
    is_active: bool = True


class StudentPathwayProfileRead(ORMModel):
    id: int | None = None
    student_id: int
    student_name: str | None = None
    province: str
    candidate_type: str | None = None
    exam_type: str | None = None
    subject_combination: str | None = None
    spring_exam_category: str | None = None
    art_track: str | None = None
    sports_track: str | None = None
    has_gaokao_registration: bool | None = None
    is_fresh_graduate: bool | None = None
    is_vocational_student: bool | None = None
    is_social_candidate: bool | None = None
    has_high_school_equivalent: bool | None = None
    accept_private_college: bool | None = None
    accept_sino_foreign: bool | None = None
    accept_junior_college: bool | None = None
    accept_outside_province: bool | None = None
    accept_early_batch: bool | None = None
    accept_service_commitment: bool | None = None
    accept_interview_or_physical_test: bool | None = None
    career_preferences_json: dict[str, object] = Field(default_factory=dict)
    region_preferences_json: dict[str, object] = Field(default_factory=dict)
    family_constraints_json: dict[str, object] = Field(default_factory=dict)
    known_body_limitations_json: dict[str, object] = Field(default_factory=dict)
    materials_json: dict[str, object] = Field(default_factory=dict)
    note: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_active: bool = True


class StudentPathwayRuleEvaluationRead(BaseModel):
    rule_id: int | None = None
    rule_code: str
    rule_name: str
    rule_type: str
    severity: str
    result: str
    message: str | None = None
    manual_review_required: bool = False
    missing_material_key: str | None = None


class StudentPathwayEvaluationRead(ORMModel):
    id: int | None = None
    student_id: int
    pathway_id: int
    target_year: int
    pathway_code: str | None = None
    pathway_name: str | None = None
    pathway_group: str | None = None
    status: str
    status_label: str
    score: float | None = None
    confidence_level: str
    matched_rules_json: list[dict[str, object]] = Field(default_factory=list)
    failed_rules_json: list[dict[str, object]] = Field(default_factory=list)
    warning_rules_json: list[dict[str, object]] = Field(default_factory=list)
    missing_materials_json: list[dict[str, object]] = Field(default_factory=list)
    recommendation_depth: str
    summary: str | None = None
    next_actions_json: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_active: bool = True


class StudentPathwayEvaluationResponse(BaseModel):
    student_id: int
    target_year: int
    profile: StudentPathwayProfileRead
    evaluations: list[StudentPathwayEvaluationRead] = Field(default_factory=list)
