import type { ImportFeedbackResult } from "../../utils/importFeedback";

export type ResultGroupKey = "challenge" | "steady" | "safe";

export interface CollegeItem {
  id: number;
  name: string;
  college_code?: string | null;
  province?: string | null;
  city?: string | null;
  school_type?: string | null;
  school_level_tags_json?: string[] | null;
  intro?: string | null;
  website?: string | null;
  supports_art: boolean;
  note?: string | null;
  alias_names?: string[] | null;
  is_active: boolean;
}

export interface CollegePayload {
  name: string;
  college_code: string | null;
  province: string | null;
  city: string | null;
  school_type: string | null;
  school_level_tags_json: string[];
  intro: string | null;
  website: string | null;
  supports_art: boolean;
  note: string | null;
  alias_names: string[];
  is_active: boolean;
}

export interface MajorItem {
  id: number;
  name: string;
  major_code?: string | null;
  category?: string | null;
  direction?: string | null;
  career_path?: string | null;
  is_art_related: boolean;
  note?: string | null;
  is_active: boolean;
}

export interface MajorPayload {
  name: string;
  major_code: string | null;
  category: string | null;
  direction: string | null;
  career_path: string | null;
  is_art_related: boolean;
  note: string | null;
  is_active: boolean;
}

export interface EmploymentDirectionItem {
  id: number;
  name: string;
  category?: string | null;
  alias_names_json?: string[] | null;
  description?: string | null;
  common_job_types_json?: string[] | null;
  common_industries_json?: string[] | null;
  prefers_postgraduate: boolean;
  requires_certificate: boolean;
  requires_long_cycle: boolean;
  supports_art: boolean;
  risk_note?: string | null;
  source_note?: string | null;
  is_active: boolean;
}

export interface EmploymentDirectionPayload {
  name: string;
  category: string | null;
  alias_names_json: string[];
  description: string | null;
  common_job_types_json: string[];
  common_industries_json: string[];
  prefers_postgraduate: boolean;
  requires_certificate: boolean;
  requires_long_cycle: boolean;
  supports_art: boolean;
  risk_note: string | null;
  source_note: string | null;
  is_active: boolean;
}

export type CareerPriorityFocus = "stability" | "salary" | "interest" | "long_term";

export interface CareerPreferenceFields {
  primary_direction_id?: number;
  secondary_direction_id?: number;
  alternative_direction_id?: number;
  priority_focuses_json: CareerPriorityFocus[];
  preferred_industries_json: string[];
  preferred_job_types_json: string[];
  target_employment_cities_json: string[];
  accepts_postgraduate: boolean;
  accepts_public_service: boolean;
  accepts_certificate: boolean;
  accepts_long_training: boolean;
}

export type StudentCareerPreferencePayload = CareerPreferenceFields;

export interface StudentCareerPreference extends CareerPreferenceFields {
  id: number;
  student_id: number;
  primary_direction_name?: string | null;
  secondary_direction_name?: string | null;
  alternative_direction_name?: string | null;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface MajorEmploymentMappingItem {
  id: number;
  major_id: number;
  major_name: string;
  direction_id: number;
  direction_name: string;
  direction_category?: string | null;
  strength: string;
  recommendation_note?: string | null;
  requires_postgraduate: boolean;
  requires_certificate: boolean;
  supported_student_types_json?: string[] | null;
  supports_art: boolean;
  note?: string | null;
  is_active: boolean;
}

export interface MajorEmploymentMappingPayload {
  major_id: number;
  direction_id: number;
  strength: string;
  recommendation_note: string | null;
  requires_postgraduate: boolean;
  requires_certificate: boolean;
  supported_student_types_json: string[];
  supports_art: boolean;
  note: string | null;
  is_active: boolean;
}

export type BoolFilter = "all" | "true" | "false";

export interface AdmissionImportResponse extends ImportFeedbackResult {
  created_college_count: number;
  created_major_count: number;
}

export interface EnrollmentPlanImportResponse extends ImportFeedbackResult {
  created_college_count: number;
  created_major_count: number;
}

export interface RecommendationGenerateResponse {
  scheme_id: number;
  scheme_name: string;
  student_id: number;
  result_count: number;
  challenge: RecommendationResult[];
  steady: RecommendationResult[];
  safe: RecommendationResult[];
}

export interface BatchGenerateResponse {
  message: string;
  scheme_ids: number[];
  result_count: number;
  items: Array<{
    student_id: number;
    student_name: string;
    province: string;
    scheme_id: number;
    result_count: number;
  }>;
}

export interface ExportRecord {
  download_url: string;
}

export interface AdmissionRecord {
  id: number;
  year: number;
  province: string;
  batch: string;
  college_id: number;
  college_name?: string | null;
  major_id?: number | null;
  major_name?: string | null;
  student_type: string;
  art_track?: string | null;
  subject_requirement?: string | null;
  min_score?: number | null;
  min_rank?: number | null;
  avg_score?: number | null;
  max_score?: number | null;
  plan_count?: number | null;
  source_note?: string | null;
  is_active: boolean;
}

export interface EnrollmentPlanItem {
  id: number;
  year: number;
  province: string;
  batch: string;
  exam_mode: string;
  college_id: number;
  college_name?: string | null;
  college_code_snapshot?: string | null;
  major_id?: number | null;
  major_name?: string | null;
  major_group_code: string;
  major_code_snapshot?: string | null;
  plan_count: number;
  subject_requirement?: string | null;
  tuition_fee?: string | null;
  schooling_years?: string | null;
  training_location?: string | null;
  student_type: string;
  source_note?: string | null;
  import_batch_name?: string | null;
  is_active: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface PaginationState {
  page: number;
  page_size: number;
  total: number;
}

export interface ExamOption {
  id: number;
  name: string;
}

export interface StudentOption {
  id: number;
  student_no: string;
  name: string;
  origin_province?: string | null;
  student_type?: string | null;
}

export interface RecommendationCollegeOption {
  id: number;
  name: string;
}

export interface RecommendationStrategyPreset {
  id: string;
  name: string;
  note?: string | null;
  safe_ratio_max: number;
  steady_ratio_max: number;
  rush_ratio_max: number;
  whitelist_college_ids: number[];
  blacklist_college_ids: number[];
  whitelist_colleges: RecommendationCollegeOption[];
  blacklist_colleges: RecommendationCollegeOption[];
  created_at: string;
}

export interface RecommendationSettings {
  safe_ratio_max: number;
  steady_ratio_max: number;
  rush_ratio_max: number;
  whitelist_college_ids: number[];
  blacklist_college_ids: number[];
  whitelist_colleges: RecommendationCollegeOption[];
  blacklist_colleges: RecommendationCollegeOption[];
  strategy_presets: RecommendationStrategyPreset[];
}

export interface RecommendationHistoryItem {
  scheme_id: number;
  scheme_name: string;
  student_id: number;
  student_name: string;
  exam_id: number;
  province: string;
  target_year?: number | null;
  student_type: string;
  score_input_mode: ScoreInputMode;
  score_input_label?: string | null;
  score_confidence?: string | null;
  reference_exam_name?: string | null;
  use_historical_mapping: boolean;
  generated_at: string;
  result_count: number;
  challenge_count: number;
  steady_count: number;
  safe_count: number;
}

export interface RecommendationResult {
  id: number;
  student_id: number;
  student_name?: string | null;
  exam_id: number;
  scheme_id: number;
  scheme_name?: string | null;
  result_type: ResultGroupKey;
  college_id: number;
  college_name?: string | null;
  major_id?: number | null;
  major_name?: string | null;
  reference_rank?: number | null;
  student_rank?: number | null;
  score_basis: string;
  reference_scope?: string | null;
  reference_years_json: number[];
  reference_record_count: number;
  reference_source_notes_json: string[];
  fallback_priority_score?: number | null;
  fallback_priority_label?: string | null;
  fallback_priority_notes_json?: string[] | null;
  fallback_category_label?: string | null;
  fallback_review_notes_json?: string[] | null;
  ratio?: number | null;
  career_match_score?: number | null;
  career_match_strength?: string | null;
  career_match_summary?: string | null;
  career_match_reasons_json?: string[] | null;
  matched_direction_names_json?: string[] | null;
  requires_postgraduate_path?: boolean | null;
  requires_certificate_path?: boolean | null;
  requires_long_training_path?: boolean | null;
  reason_text?: string | null;
  risk_flags_json?: string[] | null;
  snapshot_json?: Record<string, unknown> | null;
  generated_at: string;
  is_active: boolean;
}

export interface CollegeFiltersState {
  keyword: string;
  province: string;
  supports_art: BoolFilter;
}

export interface MajorFiltersState {
  keyword: string;
  is_art_related: BoolFilter;
}

export interface EmploymentDirectionFiltersState {
  keyword: string;
  category: string;
}

export interface MajorEmploymentMappingFiltersState {
  keyword: string;
  major_id?: number;
  direction_id?: number;
  strength: string;
}

export interface AdmissionFiltersState {
  year?: number;
  province: string;
  college_id?: number;
  student_type: string;
}

export interface EnrollmentPlanFiltersState {
  year?: number;
  province: string;
  batch: string;
  college_id?: number;
  student_type: string;
  keyword: string;
}

export interface HistoryFiltersState {
  student_id?: number;
}

export interface ProvinceVolunteerRule {
  id: number;
  province: string;
  year: number;
  exam_mode: string;
  batch: string;
  candidate_type: string;
  batch_order?: number | null;
  total_score: number;
  volunteer_limit: number;
  volunteer_unit_type: string;
  subject_requirement_mode?: string | null;
  required_subjects_json: string[];
  first_choice_subjects_json: string[];
  reselect_subjects_json: string[];
  score_rule_summary?: string | null;
  parallel_rule_mode?: string | null;
  max_major_per_unit?: number | null;
  is_parallel: boolean;
  allow_adjustment: boolean;
  support_collect_round: boolean;
  special_rules_json: string[];
  note?: string | null;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface ProvinceVolunteerRuleFiltersState {
  year?: number;
  province: string;
  exam_mode: string;
  candidate_type: string;
}

export interface ProvinceVolunteerRulePayload {
  province: string;
  year: number;
  exam_mode: string;
  batch: string;
  candidate_type: string;
  batch_order?: number;
  total_score: number;
  volunteer_limit: number;
  volunteer_unit_type: string;
  subject_requirement_mode?: string | null;
  required_subjects_json: string[];
  first_choice_subjects_json: string[];
  reselect_subjects_json: string[];
  score_rule_summary?: string | null;
  parallel_rule_mode?: string | null;
  max_major_per_unit?: number;
  is_parallel: boolean;
  allow_adjustment: boolean;
  support_collect_round: boolean;
  special_rules_json: string[];
  note: string | null;
  is_active: boolean;
}

export interface ProvinceVolunteerRuleBootstrapResponse {
  year: number;
  total_count: number;
  created_count: number;
  skipped_count: number;
}

export interface ProvinceScoreTransformRule {
  id: number;
  province: string;
  year: number;
  exam_mode: string;
  subject_code?: string | null;
  subject_name: string;
  score_mode: string;
  sort_order?: number | null;
  grade_table_json: Array<Record<string, unknown>>;
  formula_json: Record<string, unknown>;
  source_note?: string | null;
  note?: string | null;
  is_active: boolean;
}

export interface ProvinceScoreTransformRuleFiltersState {
  year?: number;
  province: string;
  exam_mode: string;
  subject_name: string;
}

export interface ProvinceScoreTransformRuleBootstrapResponse {
  year: number;
  total_count: number;
  created_count: number;
  skipped_count: number;
}

export interface SubjectRequirementDict {
  id: number;
  province: string;
  year: number;
  exam_mode: string;
  requirement_code: string;
  requirement_text: string;
  match_mode: string;
  sort_order?: number | null;
  normalized_subjects_json: string[];
  source_note?: string | null;
  note?: string | null;
  is_active: boolean;
}

export interface SubjectRequirementDictFiltersState {
  year?: number;
  province: string;
  exam_mode: string;
  requirement_code: string;
}

export interface SubjectRequirementDictBootstrapResponse {
  year: number;
  total_count: number;
  created_count: number;
  skipped_count: number;
}

export interface SpecialTypeRule {
  id: number;
  province: string;
  year: number;
  student_type: string;
  category_code: string;
  category_label: string;
  sort_order?: number | null;
  match_keywords_json: string[];
  review_notes_json: string[];
  priority_bonus: number;
  priority_notes_json: string[];
  source_note?: string | null;
  note?: string | null;
  is_active: boolean;
}

export interface SpecialTypeRuleFiltersState {
  year?: number;
  province: string;
  student_type: string;
}

export interface SpecialTypeRuleBootstrapResponse {
  year: number;
  total_count: number;
  created_count: number;
  skipped_count: number;
}

export type ScoreInputMode =
  | "actual_rank"
  | "actual_score"
  | "estimated_score"
  | "estimated_score_and_rank"
  | "score_range"
  | "rank_range";

export type RiskPreference = "conservative" | "balanced" | "aggressive";

export type ShandongRecommendationSourceMode = "exam_projection" | "manual_score" | "manual_rank";

export interface StudentGaokaoScoreProjectionPayload {
  student_id: number;
  target_year: number;
  province: string;
  source_mode: "manual_score" | "manual_rank" | "exam_projection";
  manual_score?: number;
  manual_rank?: number;
  selected_exam_ids: number[];
  note?: string;
}

export interface StudentGaokaoScoreProjectionRead {
  id?: number | null;
  student_id: number;
  student_name?: string | null;
  target_year: number;
  province: string;
  source_mode: string;
  predicted_score?: number | null;
  predicted_rank?: number | null;
  rank_range_low?: number | null;
  rank_range_high?: number | null;
  confidence_level: string;
  rank_projection_basis?: string | null;
  selected_exam_ids_json: number[];
  calculation_detail_json: Record<string, unknown>;
  note?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  is_active: boolean;
}

export interface ShandongRecommendationFormState {
  student_id?: number;
  exam_id?: number;
  target_year: number;
  batch: string;
  source_mode: ShandongRecommendationSourceMode;
  manual_score?: number;
  manual_rank?: number;
  risk_preference: RiskPreference;
  selected_subjects_json: string[];
  target_regions_json: string[];
  school_level_tags_json: string[];
  major_keyword: string;
  limit: number;
}

export interface ShandongRushStableSafeRecommendationPayload {
  student_id?: number;
  projection_id?: number;
  target_year: number;
  province: "山东";
  student_type: "general";
  batch?: string;
  subject_combination?: string;
  source_mode: "manual_score" | "manual_rank" | "projection";
  manual_score?: number;
  manual_rank?: number;
  risk_preference: RiskPreference;
  target_regions_json: string[];
  school_level_tags_json: string[];
  major_keyword?: string;
  limit: number;
}

export interface ShandongRushStableSafeCandidate {
  college_id: number;
  college_name: string;
  college_code_snapshot?: string | null;
  major_id?: number | null;
  major_name?: string | null;
  major_code_snapshot?: string | null;
  bucket: string;
  bucket_label: string;
  rank_margin?: number | null;
  rank_margin_ratio?: number | null;
  score_summary: Record<string, unknown>;
  years_used: number[];
  historical_summary: Record<string, unknown>;
  plan_count?: number | null;
  subject_requirement?: string | null;
  data_confidence: string;
  risk_flags: string[];
  explanation_text: string;
  source_document_ids: number[];
}

export interface ShandongRushStableSafeSummary {
  rush_count: number;
  stable_count: number;
  safe_count: number;
  watch_count: number;
  excluded_subject_mismatch_count: number;
}

export interface ShandongRushStableSafeRecommendationResponse {
  student_id?: number | null;
  student_name?: string | null;
  province: string;
  target_year: number;
  student_type: string;
  source_mode: string;
  predicted_score?: number | null;
  predicted_rank: number;
  rank_range_low?: number | null;
  rank_range_high?: number | null;
  rank_projection_basis?: string | null;
  risk_preference: string;
  data_years: number[];
  input_notes: string[];
  summary: ShandongRushStableSafeSummary;
  rush: ShandongRushStableSafeCandidate[];
  stable: ShandongRushStableSafeCandidate[];
  safe: ShandongRushStableSafeCandidate[];
  watch: ShandongRushStableSafeCandidate[];
}

export interface ShandongDataHealthType {
  key: string;
  label?: string | null;
  count: number;
}

export interface ShandongDataHealthYearBreakdown {
  year: number;
  total: number;
  student_types: ShandongDataHealthType[];
  batches: ShandongDataHealthType[];
  status: string;
}

export interface ShandongDataHealthCoverage {
  key: string;
  label: string;
  status: string;
  total: number;
  years: number[];
  missing_years: number[];
  readiness: string;
  readiness_label?: string | null;
  risk_level: string;
  explanation?: string | null;
  notes: string[];
  student_types: ShandongDataHealthType[];
  batch_distribution: ShandongDataHealthType[];
  year_breakdown: ShandongDataHealthYearBreakdown[];
}

export interface ShandongPublicationSource {
  id: number;
  title: string;
  url?: string | null;
  official_org?: string | null;
  published_at?: string | null;
  local_file_path?: string | null;
  file_sha256?: string | null;
  status?: string | null;
  note?: string | null;
}

export interface ShandongPublicationStatus {
  key: string;
  label: string;
  category: string;
  target_year: number;
  status: string;
  status_label: string;
  record_count: number;
  source_documents: ShandongPublicationSource[];
  action_label: string;
  explanation: string;
  notes: string[];
  blocks_recommendation: boolean;
}

export interface ShandongRecommendationDataHealth {
  generated_at: string;
  province: string;
  expected_years: number[];
  coverage: ShandongDataHealthCoverage[];
  publication_status: ShandongPublicationStatus[];
  gaps: string[];
  summary: string;
}

export interface VolunteerWorkbenchPreviewPayload extends CareerPreferenceFields {
  student_id: number;
  exam_id: number;
  province: string;
  target_year?: number;
  batch?: string;
  exam_mode?: string;
  candidate_type: string;
  score_input_mode: ScoreInputMode;
  score_range_min?: number;
  score_range_max?: number;
  rank_range_min?: number;
  rank_range_max?: number;
  reference_exam_name?: string;
  use_historical_mapping: boolean;
  risk_preference: RiskPreference;
  target_regions_json: string[];
  school_level_tags_json: string[];
  major_keyword?: string;
  subject_combination?: string;
  student_rank_override?: number;
  comprehensive_score?: number;
  professional_score?: number;
  culture_score?: number;
  note?: string;
}

export interface VolunteerWorkbenchCandidate {
  plan_id: number;
  year: number;
  province: string;
  batch: string;
  exam_mode: string;
  college_id: number;
  college_name: string;
  college_code_snapshot?: string | null;
  major_id?: number | null;
  major_name?: string | null;
  major_group_code?: string | null;
  major_code_snapshot?: string | null;
  major_direction?: string | null;
  career_path?: string | null;
  major_note?: string | null;
  plan_count: number;
  subject_requirement?: string | null;
  tuition_fee?: string | null;
  schooling_years?: string | null;
  training_location?: string | null;
  student_type: string;
  result_type: ResultGroupKey;
  reference_rank?: number | null;
  latest_admission_year?: number | null;
  latest_min_rank?: number | null;
  latest_min_score?: number | null;
  score_basis: string;
  reference_scope?: string | null;
  reference_years_json: number[];
  reference_record_count: number;
  reference_source_notes_json: string[];
  fallback_priority_score?: number | null;
  fallback_priority_label?: string | null;
  fallback_priority_notes_json?: string[] | null;
  fallback_category_label?: string | null;
  fallback_review_notes_json?: string[] | null;
  ratio?: number | null;
  career_match_score?: number | null;
  career_match_strength?: string | null;
  career_match_summary?: string | null;
  career_match_reasons_json: string[];
  matched_direction_names_json: string[];
  requires_postgraduate_path?: boolean | null;
  requires_certificate_path?: boolean | null;
  requires_long_training_path?: boolean | null;
  matched_rule_exam_mode?: string | null;
  matched_rule_batch?: string | null;
  matched_rule_candidate_type?: string | null;
  matched_rule_is_baseline: boolean;
  chapter_url?: string | null;
  chapter_review_status?: string | null;
  chapter_retrieval_status?: string | null;
  chapter_campus_note?: string | null;
  chapter_other_risk_note?: string | null;
  chapter_language_requirement?: string | null;
  chapter_single_subject_requirement?: string | null;
  chapter_gender_requirement?: string | null;
  chapter_height_requirement?: string | null;
  chapter_vision_requirement?: string | null;
  chapter_color_vision_requirement?: string | null;
  chapter_physical_exam_requirement?: string | null;
  match_tags_json: string[];
  match_notes_json: string[];
  reason_text: string;
  risk_flags_json: string[];
  source_note?: string | null;
  import_batch_name?: string | null;
}

export interface VolunteerWorkbenchPreviewResponse {
  student_id: number;
  student_name: string;
  exam_id: number;
  exam_name: string;
  province: string;
  target_year: number;
  student_type: string;
  candidate_type: string;
  total_score: number;
  snapshot_rank?: number | null;
  effective_rank?: number | null;
  score_input_mode: ScoreInputMode;
  score_input_label: string;
  score_confidence: string;
  input_notes: string[];
  rule_alerts: VolunteerWorkbenchRuleAlert[];
  applicable_rule_count: number;
  applicable_rules: ProvinceVolunteerRule[];
  candidate_count: number;
  returned_candidate_count?: number;
  is_candidate_truncated?: boolean;
  candidates: VolunteerWorkbenchCandidate[];
}

export interface VolunteerWorkbenchExplanationItem {
  label: string;
  value: string;
}

export interface VolunteerWorkbenchExplanation {
  items: VolunteerWorkbenchExplanationItem[];
  notes: string[];
}

export interface VolunteerRuleInsightFact {
  label: string;
  value: string;
}

export interface VolunteerRuleInsightCard {
  key: string;
  title: string;
  subtitle: string;
  facts: VolunteerRuleInsightFact[];
  notes: string[];
  isSelected: boolean;
}

export interface VolunteerBoundaryInsightCard {
  key: string;
  title: string;
  summary: string;
  detail: string;
  tone: "success" | "warning" | "info";
}

export interface VolunteerWorkbenchRuleAlert {
  code: string;
  level: string;
  title: string;
  detail: string;
}

export interface VolunteerDraftCheckItem {
  level: "success" | "warning" | "info";
  title: string;
  detail: string;
}

export interface VolunteerWorkbenchFormState extends CareerPreferenceFields {
  student_id?: number;
  exam_id?: number;
  province: string;
  target_year?: number;
  batch: string;
  exam_mode: string;
  candidate_type: string;
  score_input_mode: ScoreInputMode;
  score_range_min?: number;
  score_range_max?: number;
  rank_range_min?: number;
  rank_range_max?: number;
  reference_exam_name: string;
  use_historical_mapping: boolean;
  risk_preference: RiskPreference;
  target_regions_json: string[];
  school_level_tags_json: string[];
  major_keyword: string;
  subject_combination: string;
  student_rank_override?: number;
  comprehensive_score?: number;
  professional_score?: number;
  culture_score?: number;
  note: string;
}

export interface VolunteerDraftItem {
  order: number;
  plan_id: number;
  candidate: VolunteerWorkbenchCandidate;
}

export type VolunteerDraftViewMode = "batch" | "risk";

export interface VolunteerDraftViewSection {
  key: ResultGroupKey;
  label: string;
  description: string;
  tagType: "danger" | "warning" | "success";
  items: VolunteerDraftItem[];
}

export interface VolunteerDraftComparisonEntry {
  key: string;
  label: string;
  currentOrder?: number;
  compareOrder?: number;
  currentType?: ResultGroupKey;
  compareType?: ResultGroupKey;
}

export interface VolunteerDraftComparisonSummary {
  added: VolunteerDraftComparisonEntry[];
  removed: VolunteerDraftComparisonEntry[];
  reordered: VolunteerDraftComparisonEntry[];
  regrouped: VolunteerDraftComparisonEntry[];
  commonCount: number;
}

export type VolunteerEmploymentColumnKey =
  | "target_direction"
  | "match_strength"
  | "needs_postgraduate"
  | "needs_certificate"
  | "summary";

export type VolunteerEmploymentMatchStrength = "core" | "high" | "medium" | "transferable" | "pending";

export type VolunteerEmploymentHintStatus = "yes" | "not_explicit" | "pending";

export interface VolunteerEmploymentProfile {
  targetDirection: string;
  matchStrength: VolunteerEmploymentMatchStrength;
  needsPostgraduate: VolunteerEmploymentHintStatus;
  needsCertificate: VolunteerEmploymentHintStatus;
  summary: string;
}

export interface VolunteerDraftSavePayload extends CareerPreferenceFields {
  name: string;
  student_id: number;
  exam_id: number;
  province: string;
  target_year: number;
  batch?: string;
  exam_mode?: string;
  candidate_type: string;
  score_input_mode: ScoreInputMode;
  score_range_min?: number;
  score_range_max?: number;
  rank_range_min?: number;
  rank_range_max?: number;
  reference_exam_name?: string;
  use_historical_mapping: boolean;
  risk_preference: RiskPreference;
  target_regions_json: string[];
  school_level_tags_json: string[];
  major_keyword?: string;
  subject_combination?: string;
  student_rank_override?: number;
  comprehensive_score?: number;
  professional_score?: number;
  culture_score?: number;
  note?: string;
  selected_rule?: ProvinceVolunteerRule | null;
  items: Array<{
    order: number;
    plan_id?: number | null;
    candidate: VolunteerWorkbenchCandidate;
  }>;
}

export interface VolunteerDraftSummary {
  id: number;
  name: string;
  student_id: number;
  student_name?: string | null;
  exam_id: number;
  exam_name?: string | null;
  province: string;
  target_year: number;
  batch?: string | null;
  exam_mode?: string | null;
  candidate_type: string;
  score_input_mode: ScoreInputMode;
  item_count: number;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface VolunteerDraftDetail extends VolunteerDraftSummary {
  score_range_min?: number | null;
  score_range_max?: number | null;
  rank_range_min?: number | null;
  rank_range_max?: number | null;
  reference_exam_name?: string | null;
  use_historical_mapping: boolean;
  risk_preference: RiskPreference;
  target_regions_json: string[];
  school_level_tags_json: string[];
  major_keyword?: string | null;
  subject_combination?: string | null;
  primary_direction_id?: number | null;
  secondary_direction_id?: number | null;
  alternative_direction_id?: number | null;
  priority_focuses_json: CareerPriorityFocus[];
  preferred_industries_json: string[];
  preferred_job_types_json: string[];
  target_employment_cities_json: string[];
  accepts_postgraduate: boolean;
  accepts_public_service: boolean;
  accepts_certificate: boolean;
  accepts_long_training: boolean;
  student_rank_override?: number | null;
  comprehensive_score?: number | null;
  professional_score?: number | null;
  culture_score?: number | null;
  note?: string | null;
  selected_rule?: ProvinceVolunteerRule | null;
  rule_alerts?: VolunteerWorkbenchRuleAlert[];
  applicable_rules?: ProvinceVolunteerRule[];
  items: Array<{
    id: number;
    order: number;
    plan_id?: number | null;
    candidate: VolunteerWorkbenchCandidate;
    created_at: string;
    updated_at: string;
    is_active: boolean;
  }>;
}

export interface RecommendationFormState {
  name: string;
  student_id?: number;
  student_ids: number[];
  exam_id?: number;
  target_year?: number;
  province: string;
  target_regions_json: string[];
  school_level_tags_json: string[];
  major_keyword: string;
  subject_combination: string;
  obey_adjustment: boolean;
  score_input_mode: ScoreInputMode;
  score_range_min?: number;
  score_range_max?: number;
  rank_range_min?: number;
  rank_range_max?: number;
  reference_exam_name: string;
  use_historical_mapping: boolean;
  risk_preference: RiskPreference;
  student_rank_override?: number;
  comprehensive_score?: number;
  professional_score?: number;
  culture_score?: number;
  note: string;
}

export interface StrategyPresetFormState {
  name: string;
  note: string;
}
