export interface TeacherOption {
  id: number;
  name: string;
}

export interface UploadedAttachment {
  id: number;
  original_filename: string;
  download_url: string;
}

export interface EvaluationQuestion {
  id?: number;
  dimension_name: string;
  question_text: string;
  score_max: number;
  weight: number;
  sort_order: number;
  is_active: boolean;
}

export interface EvaluationTemplate {
  id: number;
  name: string;
  target_type: string;
  weight_json?: Record<string, number> | null;
  is_active: boolean;
  questions: EvaluationQuestion[];
}

export interface EvaluationBatch {
  id: number;
  template_id: number;
  template_name?: string | null;
  semester_id: number;
  semester_name?: string | null;
  source_filename?: string | null;
  import_time: string;
  status: string;
  response_count: number;
  teacher_count: number;
}

export interface EvaluationImportResponse {
  batch_id: number;
  message: string;
  success_rows: number;
  failed_rows: number;
}

export interface EvaluationTeacherSummary {
  teacher_id: number;
  teacher_name: string;
  overall_avg_score: number;
  response_count: number;
  rank?: number | null;
  dimension_scores_json?: Record<string, number> | null;
}

export interface EvaluationOverview {
  batch_id: number;
  template_name: string;
  semester_name?: string | null;
  teacher_count: number;
  teacher_summaries: EvaluationTeacherSummary[];
}

export interface EvaluationBatchCompareTeacher {
  teacher_id: number;
  teacher_name: string;
  current_score: number;
  compare_score: number;
  score_delta: number;
  current_rank?: number | null;
  compare_rank?: number | null;
  rank_delta?: number | null;
  response_count_delta: number;
}

export interface EvaluationBatchCompare {
  batch_id: number;
  compare_batch_id: number;
  batch_name: string;
  compare_batch_name: string;
  overlap_teacher_count: number;
  improved_count: number;
  declined_count: number;
  unchanged_count: number;
  only_current_count: number;
  only_compare_count: number;
  teacher_deltas: EvaluationBatchCompareTeacher[];
}

export interface EvaluationDimensionSummary {
  dimension_name: string;
  avg_score: number;
  response_count: number;
}

export interface EvaluationQuestionStat {
  question_text: string;
  dimension_name: string;
  avg_score: number;
  response_count: number;
}

export interface EvaluationTeacherDetail {
  batch_id: number;
  teacher_id: number;
  teacher_name: string;
  overall_avg_score: number;
  response_count: number;
  dimension_summaries: EvaluationDimensionSummary[];
  question_stats: EvaluationQuestionStat[];
}

export interface EvaluationTeacherTrendPoint {
  batch_id: number;
  template_name: string;
  semester_name?: string | null;
  overall_avg_score: number;
  response_count: number;
  rank?: number | null;
  import_time: string;
}

export interface EvaluationTeacherTrend {
  teacher_id: number;
  teacher_name: string;
  points: EvaluationTeacherTrendPoint[];
}

export interface RuleVersion {
  id: number;
  name: string;
  semester_id?: number | null;
  semester_name?: string | null;
  is_default: boolean;
  status: string;
  note?: string | null;
  is_active: boolean;
}

export interface RuleItem {
  id?: number;
  rule_version_id?: number;
  item_name: string;
  item_type: string;
  default_score: number;
  requires_attachment: boolean;
  note?: string | null;
  sort_order: number;
  is_active: boolean;
}

export interface QuantAttachment {
  id: number;
  stored_file_id: number;
  file: UploadedAttachment;
}

export interface QuantRecord {
  id: number;
  teacher_id: number;
  teacher_name?: string | null;
  class_id?: number | null;
  class_name?: string | null;
  semester_id: number;
  semester_name?: string | null;
  rule_version_id: number;
  rule_version_name?: string | null;
  rule_item_id: number;
  item_name: string;
  item_type: string;
  record_month: string;
  score: number;
  requires_attachment: boolean;
  description?: string | null;
  recorded_at: string;
  attachments: QuantAttachment[];
}

export interface QuantSummary {
  teacher_id: number;
  teacher_name: string;
  semester_id: number;
  semester_name?: string | null;
  rule_version_id?: number | null;
  rule_version_name?: string | null;
  total_score: number;
  positive_score: number;
  negative_score: number;
  record_count: number;
  class_names: string[];
  category_scores_json?: Record<string, number> | null;
}

export interface EvaluationImportFormState {
  template_id?: number;
  semester_id?: number;
}

export interface QuantFiltersState {
  semester_id?: number;
  teacher_id?: number;
  rule_version_id?: number;
}

export interface TemplateFormState {
  name: string;
  target_type: string;
}

export interface RuleVersionFormState {
  name: string;
  semester_id?: number;
  is_default: boolean;
  status: string;
  note: string;
  is_active: boolean;
}

export interface QuantFormState {
  teacher_id?: number;
  class_id?: number;
  semester_id?: number;
  rule_item_id?: number;
  record_month: string;
  score?: number;
  description: string;
  attachments: UploadedAttachment[];
}
