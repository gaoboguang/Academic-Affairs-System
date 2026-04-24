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


class EmploymentDirectionPayload(BaseModel):
    name: str
    category: str | None = None
    alias_names_json: list[str] = Field(default_factory=list)
    description: str | None = None
    common_job_types_json: list[str] = Field(default_factory=list)
    common_industries_json: list[str] = Field(default_factory=list)
    prefers_postgraduate: bool = False
    requires_certificate: bool = False
    requires_long_cycle: bool = False
    supports_art: bool = False
    risk_note: str | None = None
    source_note: str | None = None
    is_active: bool = True


class EmploymentDirectionRead(ORMModel):
    id: int
    name: str
    category: str | None = None
    alias_names_json: list[str] = Field(default_factory=list)
    description: str | None = None
    common_job_types_json: list[str] = Field(default_factory=list)
    common_industries_json: list[str] = Field(default_factory=list)
    prefers_postgraduate: bool
    requires_certificate: bool
    requires_long_cycle: bool
    supports_art: bool
    risk_note: str | None = None
    source_note: str | None = None
    is_active: bool


class EmploymentDirectionBootstrapResponse(BaseModel):
    total_count: int
    created_count: int
    skipped_count: int


class MajorEmploymentMappingPayload(BaseModel):
    major_id: int
    direction_id: int
    strength: str = "medium"
    recommendation_note: str | None = None
    requires_postgraduate: bool = False
    requires_certificate: bool = False
    supported_student_types_json: list[str] = Field(default_factory=list)
    supports_art: bool = False
    note: str | None = None
    is_active: bool = True


class MajorEmploymentMappingRead(ORMModel):
    id: int
    major_id: int
    major_name: str
    direction_id: int
    direction_name: str
    direction_category: str | None = None
    strength: str
    recommendation_note: str | None = None
    requires_postgraduate: bool
    requires_certificate: bool
    supported_student_types_json: list[str] = Field(default_factory=list)
    supports_art: bool
    note: str | None = None
    is_active: bool


class MajorEmploymentMappingBootstrapResponse(BaseModel):
    major_total_count: int
    matched_major_count: int
    created_count: int
    skipped_count: int


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


class EnrollmentPlanRead(ORMModel):
    id: int
    year: int
    province: str
    batch: str
    exam_mode: str
    college_id: int
    college_name: str | None = None
    college_code_snapshot: str | None = None
    major_id: int | None = None
    major_name: str | None = None
    major_group_code: str
    major_code_snapshot: str | None = None
    plan_count: int
    subject_requirement: str | None = None
    tuition_fee: str | None = None
    schooling_years: str | None = None
    training_location: str | None = None
    student_type: str
    source_note: str | None = None
    import_batch_name: str | None = None
    is_active: bool


class EnrollmentPlanImportResponse(ImportResult):
    created_college_count: int = 0
    created_major_count: int = 0


class ProvinceVolunteerRulePayload(BaseModel):
    province: str
    year: int
    exam_mode: str
    batch: str
    candidate_type: str = ""
    batch_order: int | None = None
    total_score: int = 750
    volunteer_limit: int
    volunteer_unit_type: str
    subject_requirement_mode: str | None = None
    required_subjects_json: list[str] = Field(default_factory=list)
    first_choice_subjects_json: list[str] = Field(default_factory=list)
    reselect_subjects_json: list[str] = Field(default_factory=list)
    score_rule_summary: str | None = None
    parallel_rule_mode: str | None = None
    max_major_per_unit: int | None = None
    is_parallel: bool = True
    allow_adjustment: bool = True
    support_collect_round: bool = False
    special_rules_json: list[str] = Field(default_factory=list)
    note: str | None = None
    is_active: bool = True


class ProvinceVolunteerRuleRead(ORMModel):
    id: int
    province: str
    year: int
    exam_mode: str
    batch: str
    candidate_type: str = ""
    batch_order: int | None = None
    total_score: int
    volunteer_limit: int
    volunteer_unit_type: str
    subject_requirement_mode: str | None = None
    required_subjects_json: list[str] = Field(default_factory=list)
    first_choice_subjects_json: list[str] = Field(default_factory=list)
    reselect_subjects_json: list[str] = Field(default_factory=list)
    score_rule_summary: str | None = None
    parallel_rule_mode: str | None = None
    max_major_per_unit: int | None = None
    is_parallel: bool
    allow_adjustment: bool
    support_collect_round: bool
    special_rules_json: list[str] = Field(default_factory=list)
    note: str | None = None
    is_active: bool


class ProvinceVolunteerRuleBootstrapResponse(BaseModel):
    year: int
    total_count: int
    created_count: int
    skipped_count: int


class ProvinceScoreTransformRulePayload(BaseModel):
    province: str
    year: int
    exam_mode: str = ""
    subject_code: str | None = None
    subject_name: str
    score_mode: str
    sort_order: int | None = None
    grade_table_json: list[dict[str, object]] = Field(default_factory=list)
    formula_json: dict[str, object] = Field(default_factory=dict)
    source_note: str | None = None
    note: str | None = None
    is_active: bool = True


class ProvinceScoreTransformRuleRead(ORMModel):
    id: int
    province: str
    year: int
    exam_mode: str = ""
    subject_code: str | None = None
    subject_name: str
    score_mode: str
    sort_order: int | None = None
    grade_table_json: list[dict[str, object]] = Field(default_factory=list)
    formula_json: dict[str, object] = Field(default_factory=dict)
    source_note: str | None = None
    note: str | None = None
    is_active: bool


class ProvinceScoreTransformRuleBootstrapResponse(BaseModel):
    year: int
    total_count: int
    created_count: int
    skipped_count: int


class SubjectRequirementDictPayload(BaseModel):
    province: str
    year: int
    exam_mode: str = ""
    requirement_code: str
    requirement_text: str
    match_mode: str
    sort_order: int | None = None
    normalized_subjects_json: list[str] = Field(default_factory=list)
    source_note: str | None = None
    note: str | None = None
    is_active: bool = True


class SubjectRequirementDictRead(ORMModel):
    id: int
    province: str
    year: int
    exam_mode: str = ""
    requirement_code: str
    requirement_text: str
    match_mode: str
    sort_order: int | None = None
    normalized_subjects_json: list[str] = Field(default_factory=list)
    source_note: str | None = None
    note: str | None = None
    is_active: bool


class SubjectRequirementDictBootstrapResponse(BaseModel):
    year: int
    total_count: int
    created_count: int
    skipped_count: int


class SpecialTypeRulePayload(BaseModel):
    province: str
    year: int
    student_type: str
    category_code: str
    category_label: str
    sort_order: int | None = None
    match_keywords_json: list[str] = Field(default_factory=list)
    review_notes_json: list[str] = Field(default_factory=list)
    priority_bonus: int = 0
    priority_notes_json: list[str] = Field(default_factory=list)
    source_note: str | None = None
    note: str | None = None
    is_active: bool = True


class SpecialTypeRuleRead(ORMModel):
    id: int
    province: str
    year: int
    student_type: str
    category_code: str
    category_label: str
    sort_order: int | None = None
    match_keywords_json: list[str] = Field(default_factory=list)
    review_notes_json: list[str] = Field(default_factory=list)
    priority_bonus: int
    priority_notes_json: list[str] = Field(default_factory=list)
    source_note: str | None = None
    note: str | None = None
    is_active: bool


class SpecialTypeRuleBootstrapResponse(BaseModel):
    year: int
    total_count: int
    created_count: int
    skipped_count: int


class VolunteerWorkbenchPreviewPayload(BaseModel):
    student_id: int
    exam_id: int
    province: str
    target_year: int | None = None
    batch: str | None = None
    exam_mode: str | None = None
    candidate_type: str = ""
    score_input_mode: str = "actual_rank"
    score_range_min: float | None = None
    score_range_max: float | None = None
    rank_range_min: int | None = None
    rank_range_max: int | None = None
    reference_exam_name: str | None = None
    use_historical_mapping: bool = False
    risk_preference: str = "balanced"
    target_regions_json: list[str] = Field(default_factory=list)
    school_level_tags_json: list[str] = Field(default_factory=list)
    major_keyword: str | None = None
    subject_combination: str | None = None
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
    student_rank_override: int | None = None
    comprehensive_score: float | None = None
    professional_score: float | None = None
    culture_score: float | None = None
    note: str | None = None


class VolunteerWorkbenchCandidateRead(BaseModel):
    plan_id: int
    year: int
    province: str
    batch: str
    exam_mode: str
    college_id: int
    college_name: str
    college_code_snapshot: str | None = None
    major_id: int | None = None
    major_name: str | None = None
    major_group_code: str | None = None
    major_code_snapshot: str | None = None
    major_direction: str | None = None
    career_path: str | None = None
    major_note: str | None = None
    plan_count: int
    subject_requirement: str | None = None
    tuition_fee: str | None = None
    schooling_years: str | None = None
    training_location: str | None = None
    student_type: str
    result_type: str
    reference_rank: int | None = None
    latest_admission_year: int | None = None
    latest_min_rank: int | None = None
    latest_min_score: float | None = None
    score_basis: str
    reference_scope: str | None = None
    reference_years_json: list[int] = Field(default_factory=list)
    reference_record_count: int = 0
    reference_source_notes_json: list[str] = Field(default_factory=list)
    fallback_priority_score: float | None = None
    fallback_priority_label: str | None = None
    fallback_priority_notes_json: list[str] = Field(default_factory=list)
    fallback_category_label: str | None = None
    fallback_review_notes_json: list[str] = Field(default_factory=list)
    ratio: float | None = None
    career_match_score: float | None = None
    career_match_strength: str | None = None
    career_match_summary: str | None = None
    career_match_reasons_json: list[str] = Field(default_factory=list)
    matched_direction_names_json: list[str] = Field(default_factory=list)
    requires_postgraduate_path: bool | None = None
    requires_certificate_path: bool | None = None
    requires_long_training_path: bool | None = None
    matched_rule_exam_mode: str | None = None
    matched_rule_batch: str | None = None
    matched_rule_candidate_type: str | None = None
    matched_rule_is_baseline: bool = False
    chapter_url: str | None = None
    chapter_review_status: str | None = None
    chapter_retrieval_status: str | None = None
    chapter_campus_note: str | None = None
    chapter_other_risk_note: str | None = None
    chapter_language_requirement: str | None = None
    chapter_single_subject_requirement: str | None = None
    chapter_gender_requirement: str | None = None
    chapter_height_requirement: str | None = None
    chapter_vision_requirement: str | None = None
    chapter_color_vision_requirement: str | None = None
    chapter_physical_exam_requirement: str | None = None
    match_tags_json: list[str] = Field(default_factory=list)
    match_notes_json: list[str] = Field(default_factory=list)
    reason_text: str
    risk_flags_json: list[str] = Field(default_factory=list)
    source_note: str | None = None
    import_batch_name: str | None = None


class VolunteerWorkbenchRuleAlertRead(BaseModel):
    code: str
    level: str
    title: str
    detail: str


class VolunteerWorkbenchPreviewResponse(BaseModel):
    student_id: int
    student_name: str
    exam_id: int
    exam_name: str
    province: str
    target_year: int
    student_type: str
    candidate_type: str
    total_score: float
    snapshot_rank: int | None = None
    effective_rank: int | None = None
    score_input_mode: str = "actual_rank"
    score_input_label: str
    score_confidence: str
    input_notes: list[str] = Field(default_factory=list)
    rule_alerts: list[VolunteerWorkbenchRuleAlertRead] = Field(default_factory=list)
    applicable_rule_count: int
    applicable_rules: list[ProvinceVolunteerRuleRead] = Field(default_factory=list)
    candidate_count: int
    candidates: list[VolunteerWorkbenchCandidateRead] = Field(default_factory=list)


class VolunteerDraftItemPayload(BaseModel):
    order: int
    plan_id: int | None = None
    candidate: VolunteerWorkbenchCandidateRead


class VolunteerDraftPayload(BaseModel):
    name: str
    student_id: int
    exam_id: int
    province: str
    target_year: int
    batch: str | None = None
    exam_mode: str | None = None
    candidate_type: str = ""
    score_input_mode: str = "actual_rank"
    score_range_min: float | None = None
    score_range_max: float | None = None
    rank_range_min: int | None = None
    rank_range_max: int | None = None
    reference_exam_name: str | None = None
    use_historical_mapping: bool = False
    risk_preference: str = "balanced"
    target_regions_json: list[str] = Field(default_factory=list)
    school_level_tags_json: list[str] = Field(default_factory=list)
    major_keyword: str | None = None
    subject_combination: str | None = None
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
    student_rank_override: int | None = None
    comprehensive_score: float | None = None
    professional_score: float | None = None
    culture_score: float | None = None
    note: str | None = None
    selected_rule: ProvinceVolunteerRuleRead | None = None
    items: list[VolunteerDraftItemPayload] = Field(default_factory=list)


class VolunteerDraftItemRead(ORMModel):
    id: int
    order: int
    plan_id: int | None = None
    candidate: VolunteerWorkbenchCandidateRead


class VolunteerDraftSummaryRead(ORMModel):
    id: int
    name: str
    student_id: int
    student_name: str | None = None
    exam_id: int
    exam_name: str | None = None
    province: str
    target_year: int
    batch: str | None = None
    exam_mode: str | None = None
    candidate_type: str = ""
    score_input_mode: str = "actual_rank"
    item_count: int
    updated_at: datetime
    is_active: bool


class VolunteerDraftRead(VolunteerDraftSummaryRead):
    score_range_min: float | None = None
    score_range_max: float | None = None
    rank_range_min: int | None = None
    rank_range_max: int | None = None
    reference_exam_name: str | None = None
    use_historical_mapping: bool = False
    risk_preference: str = "balanced"
    target_regions_json: list[str] = Field(default_factory=list)
    school_level_tags_json: list[str] = Field(default_factory=list)
    major_keyword: str | None = None
    subject_combination: str | None = None
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
    student_rank_override: int | None = None
    comprehensive_score: float | None = None
    professional_score: float | None = None
    culture_score: float | None = None
    note: str | None = None
    selected_rule: ProvinceVolunteerRuleRead | None = None
    rule_alerts: list[VolunteerWorkbenchRuleAlertRead] = Field(default_factory=list)
    applicable_rules: list[ProvinceVolunteerRuleRead] = Field(default_factory=list)
    items: list[VolunteerDraftItemRead] = Field(default_factory=list)


class RecommendationGeneratePayload(BaseModel):
    student_id: int
    exam_id: int
    name: str | None = None
    target_year: int | None = None
    province: str | None = None
    target_regions_json: list[str] = Field(default_factory=list)
    school_level_tags_json: list[str] = Field(default_factory=list)
    major_keyword: str | None = None
    subject_combination: str | None = None
    obey_adjustment: bool = False
    score_input_mode: str = "actual_rank"
    score_range_min: float | None = None
    score_range_max: float | None = None
    rank_range_min: int | None = None
    rank_range_max: int | None = None
    reference_exam_name: str | None = None
    use_historical_mapping: bool = False
    risk_preference: str = "balanced"
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
    province: str | None = None
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
    reference_scope: str | None = None
    reference_years_json: list[int] = Field(default_factory=list)
    reference_record_count: int = 0
    reference_source_notes_json: list[str] = Field(default_factory=list)
    fallback_priority_score: float | None = None
    fallback_priority_label: str | None = None
    fallback_priority_notes_json: list[str] = Field(default_factory=list)
    fallback_category_label: str | None = None
    fallback_review_notes_json: list[str] = Field(default_factory=list)
    ratio: float | None = None
    career_match_score: float | None = None
    career_match_strength: str | None = None
    career_match_summary: str | None = None
    career_match_reasons_json: list[str] = Field(default_factory=list)
    matched_direction_names_json: list[str] = Field(default_factory=list)
    requires_postgraduate_path: bool | None = None
    requires_certificate_path: bool | None = None
    requires_long_training_path: bool | None = None
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


class RecommendationBatchGenerateItem(BaseModel):
    student_id: int
    student_name: str
    province: str
    scheme_id: int
    result_count: int


class RecommendationBatchGenerateResponse(BaseModel):
    message: str
    scheme_ids: list[int] = Field(default_factory=list)
    result_count: int
    items: list[RecommendationBatchGenerateItem] = Field(default_factory=list)


class RecommendationHistoryItem(BaseModel):
    scheme_id: int
    scheme_name: str
    student_id: int
    student_name: str
    exam_id: int
    province: str
    target_year: int | None = None
    student_type: str
    score_input_mode: str = "actual_rank"
    score_input_label: str | None = None
    score_confidence: str | None = None
    reference_exam_name: str | None = None
    use_historical_mapping: bool = False
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
