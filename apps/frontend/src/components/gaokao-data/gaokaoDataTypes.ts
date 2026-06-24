import type { components } from "../../types/api.generated";
import type {
  GaokaoCollegeEvidenceOption,
} from "../../utils/gaokaoEvidence";
import type {
  GaokaoOverviewTableStat,
} from "../../utils/gaokaoOverview";

type ApiSchemas = components["schemas"];

// 以下类型定义是「前端契约」，包含若干非空约束（例如 notes: string[]），
// 后端 OpenAPI 返回的是 `notes?: string[]`，实际运行时始终返回数组。
// 文件末尾有一段编译期兼容性检查 `_AssertSchemaCompat`——当后端 schema
// 改动导致不再兼容时，`npm run gen:api` 后 tsc 会直接报错。

export interface GaokaoDataOverview {
  source_mode: string;
  data_version?: string | null;
  generated_at?: string | null;
  school_total: number;
  recruit_site_covered: number;
  recruit_site_coverage_rate?: number | null;
  chapter_url_covered: number;
  chapter_url_coverage_rate?: number | null;
  fallback_url_covered: number;
  duplicate_group_total?: number | null;
  same_name_cross_site_group_total?: number | null;
  recent_batch_label?: string | null;
  last_updated_at?: string | null;
  notes: string[];
  core_tables: GaokaoOverviewTableStat[];
}

export interface GaokaoImportBatch {
  id: string;
  batch_name: string;
  source_type: string;
  source_filename?: string | null;
  status: string;
  finished_at?: string | null;
}

export interface GaokaoDataHealthTable {
  key: string;
  label: string;
  count: number;
  status: string;
  explanation?: string | null;
  notes: string[];
}

export interface GaokaoDataHealthType {
  key: string;
  label?: string | null;
  count: number;
}

export interface GaokaoDataHealthYearBreakdown {
  year: number;
  total: number;
  student_types: GaokaoDataHealthType[];
  batches: GaokaoDataHealthType[];
  status: string;
}

export interface GaokaoDataHealthCoverage {
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
  student_types: GaokaoDataHealthType[];
  batch_distribution: GaokaoDataHealthType[];
  year_breakdown: GaokaoDataHealthYearBreakdown[];
}

export interface GaokaoDataAuditItem {
  key: string;
  label: string;
  status: string;
  created: number;
  updated: number;
  duplicates: number;
  conflicts: number;
  pending_review: number;
  notes: string[];
}

export interface GaokaoDataFieldExplanation {
  field: string;
  label: string;
  explanation: string;
}

export interface GaokaoDataDeliveryAssessment {
  status: string;
  label: string;
  summary: string;
  pass_items: string[];
  warning_items: string[];
  blocking_items: string[];
}

export interface GaokaoDataSpecialTypeRisk {
  key: string;
  label: string;
  readiness: string;
  readiness_label: string;
  risk_level: string;
  plan_count: number;
  raw_plan_count: number;
  admission_count: number;
  raw_admission_count: number;
  score_line_count: number;
  volunteer_rule_count: number;
  special_rule_count: number;
  fallback_modes: string[];
  fallback_labels: string[];
  explanation: string;
  notes: string[];
}

export interface GaokaoDataPublicationSource {
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

export interface GaokaoDataPublicationStatus {
  key: string;
  label: string;
  category: string;
  target_year: number;
  status: string;
  status_label: string;
  record_count: number;
  source_documents: GaokaoDataPublicationSource[];
  action_label: string;
  explanation: string;
  notes: string[];
  blocks_recommendation: boolean;
}

export interface GaokaoDataHealth {
  db_path: string;
  exists: boolean;
  generated_at: string;
  schema_version?: string | null;
  province: string;
  expected_years: number[];
  field_explanations: GaokaoDataFieldExplanation[];
  delivery_assessment?: GaokaoDataDeliveryAssessment | null;
  tables: GaokaoDataHealthTable[];
  coverage: GaokaoDataHealthCoverage[];
  publication_status: GaokaoDataPublicationStatus[];
  special_type_risks: GaokaoDataSpecialTypeRisk[];
  audit_summary: GaokaoDataAuditItem[];
  gaps: string[];
  summary: string;
}

export interface GaokaoReviewBucket {
  code: string;
  title: string;
  count?: number | null;
  description: string;
}

export interface GaokaoReviewQuickFilter {
  code: string;
  title: string;
  count: number;
  description: string;
}

export interface GaokaoReviewGroupComparisonField {
  key: string;
  title: string;
  status: string;
  distinct_total: number;
  missing_total: number;
  sample_values: string[];
  summary: string;
}

export interface GaokaoReviewGroup {
  key: string;
  title: string;
  group_type?: string | null;
  item_count: number;
  comparison_fields?: GaokaoReviewGroupComparisonField[];
  priority_code?: string | null;
  priority_label?: string | null;
  priority_score?: number;
  priority_reasons?: string[];
  suggested_action?: string | null;
  high_priority_member_total: number;
  unresolved_total: number;
  missing_chapter_total: number;
  missing_recruit_site_total: number;
  member_items?: GaokaoReviewGroupMember[];
}

export interface GaokaoReviewGroupMember {
  college_id?: number | null;
  college_name?: string | null;
  college_code?: string | null;
  review_status?: string | null;
  province?: string | null;
  official_site?: string | null;
  recruit_site?: string | null;
  chapter_url?: string | null;
  fallback_url?: string | null;
  effective_chapter_url?: string | null;
  source_title?: string | null;
  source_url?: string | null;
  updated_at?: string | null;
  priority_code?: string | null;
  priority_label?: string | null;
  priority_score?: number;
  priority_reasons?: string[];
}

export interface GaokaoReviewItem {
  college_id?: number | null;
  college_name?: string | null;
  college_code?: string | null;
  duplicate_group_key?: string | null;
  same_name_group_key?: string | null;
  review_status?: string | null;
  retrieval_status?: string | null;
  recruit_site?: string | null;
  chapter_url?: string | null;
  fallback_url?: string | null;
  priority_code?: string | null;
  priority_label?: string | null;
  priority_score?: number;
  priority_reasons?: string[];
}

export interface GaokaoCollegeOption extends GaokaoCollegeEvidenceOption {
  source_mode: string;
}

export interface GaokaoReviewSummary {
  source_available: boolean;
  source_mode: string;
  active_filter: string;
  active_focus: string;
  active_sort: string;
  active_keyword?: string | null;
  matched_total?: number | null;
  queue_total: number;
  duplicate_group_total?: number | null;
  same_name_cross_site_group_total?: number | null;
  counts: GaokaoReviewBucket[];
  quick_filters: GaokaoReviewQuickFilter[];
  items: GaokaoReviewItem[];
  priority_groups: GaokaoReviewGroup[];
  duplicate_groups: GaokaoReviewGroup[];
  same_name_groups: GaokaoReviewGroup[];
  highlights: string[];
  notes: string[];
}

export interface GaokaoCollegeEvidence {
  source_available: boolean;
  source_mode: string;
  college_id: number;
  college_name?: string | null;
  college_code?: string | null;
  province?: string | null;
  official_site?: string | null;
  recruit_site?: string | null;
  chapter_url?: string | null;
  fallback_url?: string | null;
  source_url?: string | null;
  source_title?: string | null;
  review_status?: string | null;
  retrieval_status?: string | null;
  message?: string | null;
  notes: string[];
}

export interface GaokaoShandongMonitor {
  province: string;
  data_version?: string | null;
  ready_section_total: number;
  gap_section_total: number;
  priority_notes: string[];
  sections: GaokaoOverviewTableStat[];
  notes: string[];
}

// ---------------------------------------------------------------------------
// 编译期兼容性检查：本文件的类型必须是后端 OpenAPI 生成类型的「子类型」。
// 当后端字段改名或类型变更时，`npm run gen:api` 之后此文件会先报错，
// 让前端改动集中在这一处、不再把错误扩散到各 Vue 组件。
// ---------------------------------------------------------------------------

type IsAssignable<L, R> = [L] extends [R] ? true : false;

interface _SchemaAssertions {
  overview: IsAssignable<GaokaoDataOverview, ApiSchemas["GaokaoDataOverviewRead"]>;
  importBatch: IsAssignable<GaokaoImportBatch, ApiSchemas["GaokaoImportBatchRead"]>;
  healthTable: IsAssignable<GaokaoDataHealthTable, ApiSchemas["GaokaoDataHealthTableRead"]>;
  healthType: IsAssignable<GaokaoDataHealthType, ApiSchemas["GaokaoDataHealthTypeRead"]>;
  healthYearBreakdown: IsAssignable<
    GaokaoDataHealthYearBreakdown,
    ApiSchemas["GaokaoDataHealthYearBreakdownRead"]
  >;
  healthCoverage: IsAssignable<
    GaokaoDataHealthCoverage,
    ApiSchemas["GaokaoDataHealthCoverageRead"]
  >;
  auditItem: IsAssignable<GaokaoDataAuditItem, ApiSchemas["GaokaoDataAuditItemRead"]>;
  fieldExplanation: IsAssignable<
    GaokaoDataFieldExplanation,
    ApiSchemas["GaokaoDataFieldExplanationRead"]
  >;
  deliveryAssessment: IsAssignable<
    GaokaoDataDeliveryAssessment,
    ApiSchemas["GaokaoDataDeliveryAssessmentRead"]
  >;
  specialTypeRisk: IsAssignable<
    GaokaoDataSpecialTypeRisk,
    ApiSchemas["GaokaoDataSpecialTypeRiskRead"]
  >;
  publicationSource: IsAssignable<
    GaokaoDataPublicationSource,
    ApiSchemas["GaokaoDataPublicationSourceRead"]
  >;
  publicationStatus: IsAssignable<
    GaokaoDataPublicationStatus,
    ApiSchemas["GaokaoDataPublicationStatusRead"]
  >;
  health: IsAssignable<GaokaoDataHealth, ApiSchemas["GaokaoDataHealthRead"]>;
  reviewBucket: IsAssignable<GaokaoReviewBucket, ApiSchemas["GaokaoReviewBucketRead"]>;
  reviewQuickFilter: IsAssignable<
    GaokaoReviewQuickFilter,
    ApiSchemas["GaokaoReviewQuickFilterRead"]
  >;
  reviewGroupField: IsAssignable<
    GaokaoReviewGroupComparisonField,
    ApiSchemas["GaokaoReviewGroupComparisonFieldRead"]
  >;
  reviewGroupMember: IsAssignable<
    GaokaoReviewGroupMember,
    ApiSchemas["GaokaoReviewGroupMemberRead"]
  >;
  reviewItem: IsAssignable<GaokaoReviewItem, ApiSchemas["GaokaoReviewItemRead"]>;
  reviewGroup: IsAssignable<GaokaoReviewGroup, ApiSchemas["GaokaoReviewGroupRead"]>;
  reviewSummary: IsAssignable<GaokaoReviewSummary, ApiSchemas["GaokaoReviewSummaryRead"]>;
  collegeEvidence: IsAssignable<
    GaokaoCollegeEvidence,
    ApiSchemas["GaokaoCollegeEvidenceRead"]
  >;
  shandongMonitor: IsAssignable<
    GaokaoShandongMonitor,
    ApiSchemas["GaokaoShandongMonitorRead"]
  >;
}

type _AssertAllTrue<T> = {
  [K in keyof T]: T[K] extends true ? T[K] : never;
};

type _SchemaCompatOk = _AssertAllTrue<_SchemaAssertions>;

// 下面这行若标红，说明至少有一条不兼容。
// 看最近一次 OpenAPI 变更并对齐上面的 interface 即可。
const _schemaCompatOk: _SchemaCompatOk = {} as _SchemaCompatOk;
void _schemaCompatOk;
