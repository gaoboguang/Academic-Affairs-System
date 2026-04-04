from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ImportResult, ORMModel


class CollegePayload(BaseModel):
    name: str
    college_code: str | None = None
    province: str | None = None
    city: str | None = None
    school_type: str | None = None
    school_level_tags_json: list[str] = Field(default_factory=list)
    intro: str | None = None
    website: str | None = None
    supports_art: bool = False
    note: str | None = None
    alias_names: list[str] = Field(default_factory=list)
    is_active: bool = True


class CollegeRead(ORMModel):
    id: int
    name: str
    college_code: str | None = None
    province: str | None = None
    city: str | None = None
    school_type: str | None = None
    school_level_tags_json: list[str] | None = None
    intro: str | None = None
    website: str | None = None
    supports_art: bool
    note: str | None = None
    alias_names: list[str] = Field(default_factory=list)
    is_active: bool


class MajorPayload(BaseModel):
    name: str
    major_code: str | None = None
    category: str | None = None
    direction: str | None = None
    career_path: str | None = None
    is_art_related: bool = False
    note: str | None = None
    is_active: bool = True


class MajorRead(ORMModel):
    id: int
    name: str
    major_code: str | None = None
    category: str | None = None
    direction: str | None = None
    career_path: str | None = None
    is_art_related: bool
    note: str | None = None
    is_active: bool


class AdmissionRecordRead(ORMModel):
    id: int
    year: int
    province: str
    batch: str
    college_id: int
    college_name: str | None = None
    major_id: int | None = None
    major_name: str | None = None
    student_type: str
    art_track: str | None = None
    subject_requirement: str | None = None
    min_score: float | None = None
    min_rank: int | None = None
    avg_score: float | None = None
    max_score: float | None = None
    plan_count: int | None = None
    source_note: str | None = None
    is_active: bool


class AdmissionImportResponse(ImportResult):
    created_college_count: int = 0
    created_major_count: int = 0


class RecommendationGeneratePayload(BaseModel):
    student_id: int
    exam_id: int
    name: str | None = None
    target_year: int | None = None
    province: str
    target_regions_json: list[str] = Field(default_factory=list)
    school_level_tags_json: list[str] = Field(default_factory=list)
    major_keyword: str | None = None
    subject_combination: str | None = None
    obey_adjustment: bool = False
    student_rank_override: int | None = None
    comprehensive_score: float | None = None
    professional_score: float | None = None
    culture_score: float | None = None
    note: str | None = None


class RecommendationBatchGeneratePayload(BaseModel):
    student_ids: list[int]
    exam_id: int
    name: str | None = None
    target_year: int | None = None
    province: str
    target_regions_json: list[str] = Field(default_factory=list)
    school_level_tags_json: list[str] = Field(default_factory=list)
    major_keyword: str | None = None
    subject_combination: str | None = None
    obey_adjustment: bool = False
    note: str | None = None


class RecommendationResultRead(ORMModel):
    id: int
    student_id: int
    student_name: str | None = None
    exam_id: int
    scheme_id: int
    scheme_name: str | None = None
    result_type: str
    college_id: int
    college_name: str | None = None
    major_id: int | None = None
    major_name: str | None = None
    reference_rank: int | None = None
    student_rank: int | None = None
    score_basis: str
    ratio: float | None = None
    reason_text: str | None = None
    risk_flags_json: list[str] | None = None
    snapshot_json: dict | None = None
    generated_at: datetime
    is_active: bool


class RecommendationGenerateResponse(BaseModel):
    scheme_id: int
    scheme_name: str
    student_id: int
    result_count: int
    challenge: list[RecommendationResultRead]
    steady: list[RecommendationResultRead]
    safe: list[RecommendationResultRead]


class RecommendationHistoryItem(BaseModel):
    scheme_id: int
    scheme_name: str
    student_id: int
    student_name: str
    exam_id: int
    province: str
    student_type: str
    generated_at: datetime
    result_count: int
    challenge_count: int
    steady_count: int
    safe_count: int


class RecommendationCollegeOption(BaseModel):
    id: int
    name: str


class RecommendationStrategyPresetPayload(BaseModel):
    name: str
    note: str | None = None
    safe_ratio_max: float = 0.85
    steady_ratio_max: float = 1.0
    rush_ratio_max: float = 1.15
    whitelist_college_ids: list[int] = Field(default_factory=list)
    blacklist_college_ids: list[int] = Field(default_factory=list)


class RecommendationStrategyPresetRead(BaseModel):
    id: str
    name: str
    note: str | None = None
    safe_ratio_max: float
    steady_ratio_max: float
    rush_ratio_max: float
    whitelist_college_ids: list[int] = Field(default_factory=list)
    blacklist_college_ids: list[int] = Field(default_factory=list)
    whitelist_colleges: list[RecommendationCollegeOption] = Field(default_factory=list)
    blacklist_colleges: list[RecommendationCollegeOption] = Field(default_factory=list)
    created_at: datetime


class RecommendationSettingsPayload(BaseModel):
    safe_ratio_max: float = 0.85
    steady_ratio_max: float = 1.0
    rush_ratio_max: float = 1.15
    whitelist_college_ids: list[int] = Field(default_factory=list)
    blacklist_college_ids: list[int] = Field(default_factory=list)


class RecommendationSettingsRead(BaseModel):
    safe_ratio_max: float
    steady_ratio_max: float
    rush_ratio_max: float
    whitelist_college_ids: list[int] = Field(default_factory=list)
    blacklist_college_ids: list[int] = Field(default_factory=list)
    whitelist_colleges: list[RecommendationCollegeOption] = Field(default_factory=list)
    blacklist_colleges: list[RecommendationCollegeOption] = Field(default_factory=list)
    strategy_presets: list[RecommendationStrategyPresetRead] = Field(default_factory=list)
