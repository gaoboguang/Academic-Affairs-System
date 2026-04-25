import { uniqueStrings } from "./helpers";
import type {
  ShandongRecommendationDataHealth,
  ShandongRecommendationFormState,
  ShandongRecommendationSourceMode,
  ShandongRushStableSafeCandidate,
  ShandongRushStableSafeRecommendationPayload,
  ShandongRushStableSafeRecommendationResponse,
  StudentGaokaoScoreProjectionPayload,
  StudentGaokaoScoreProjectionRead,
} from "./types";

export const shandongSubjectOptions = ["物理", "化学", "生物", "政治", "历史", "地理"];

export const shandongRiskPreferenceOptions: Array<{ label: string; value: ShandongRecommendationFormState["risk_preference"]; help: string }> = [
  { label: "保守", value: "conservative", help: "更看重稳妥和保底，冲刺范围收窄。" },
  { label: "均衡", value: "balanced", help: "默认口径，兼顾冲刺、稳妥和保底。" },
  { label: "冲刺", value: "aggressive", help: "允许更多边际接近的候选进入冲刺。" },
];

export const shandongSourceModeOptions: Array<{ label: string; value: ShandongRecommendationSourceMode; help: string }> = [
  { label: "选择学生与考试估算", value: "exam_projection", help: "先按校内考试生成高考预估快照，再进入冲稳保推荐。" },
  { label: "手动填写预估分", value: "manual_score", help: "系统会用一分一段把分数换算为山东全省位次。" },
  { label: "手动填写全省位次", value: "manual_rank", help: "直接使用已确认的山东全省位次，结果最稳定。" },
];

export const SHANDONG_2026_DATA_NOTICE =
  "2026 普通类正式招生计划如未完全公开，当前主要参考 2023-2025 历史投档数据；正式填报前需导入 2026 官方计划，并以山东省教育招生考试院最终发布的招生计划和高校章程为准。";

export const SHANDONG_RECOMMENDATION_PRINT_STORAGE_PREFIX = "local-edu-tool:shandong-recommendation-report:";

export interface ShandongResultGroup {
  key: "rush" | "stable" | "safe" | "watch";
  label: string;
  description: string;
  tagType: "danger" | "warning" | "success" | "info";
  items: ShandongRushStableSafeCandidate[];
}

export interface ShandongHistoricalRankRow {
  year?: number;
  min_rank?: number | null;
  min_score?: number | null;
  plan_count?: number | null;
  source_note?: string | null;
}

export interface ShandongCoverageRow {
  key: string;
  label: string;
  status: string;
  statusLabel: string;
  total: number;
  coveredYears: number[];
  missingYears: number[];
  explanation: string;
}

export interface ShandongRecommendationPrintPayload {
  created_at: string;
  result: ShandongRushStableSafeRecommendationResponse;
  projection?: StudentGaokaoScoreProjectionRead | null;
  data_health_summary?: string | null;
  data_health_gaps: string[];
}

export function createShandongRecommendationForm(): ShandongRecommendationFormState {
  return {
    student_id: undefined,
    exam_id: undefined,
    target_year: 2026,
    batch: "常规批",
    source_mode: "exam_projection",
    manual_score: undefined,
    manual_rank: undefined,
    risk_preference: "balanced",
    selected_subjects_json: [],
    target_regions_json: [],
    school_level_tags_json: [],
    major_keyword: "",
    limit: 120,
  };
}

export function validateShandongRecommendationForm(form: ShandongRecommendationFormState): string | null {
  if (!form.student_id) {
    return "请先选择学生，系统会用学生档案核对是否为山东普通类。";
  }
  if (!form.target_year) {
    return "请选择目标年份。";
  }
  if (!form.selected_subjects_json.length) {
    return "请选择学生选科组合，系统会据此排除选科不符的计划。";
  }
  if (form.source_mode === "exam_projection" && !form.exam_id) {
    return "选择学生与考试估算时，需要同时选择一次参考考试。";
  }
  if (form.source_mode === "manual_score" && form.manual_score === undefined) {
    return "手动预估分入口需要填写预估高考分数。";
  }
  if (form.source_mode === "manual_rank" && form.manual_rank === undefined) {
    return "手动位次入口需要填写山东全省位次。";
  }
  if (form.source_mode === "manual_rank" && form.manual_rank !== undefined && form.manual_rank <= 0) {
    return "山东全省位次必须大于 0。";
  }
  if (form.limit < 1 || form.limit > 300) {
    return "单组展示数量请保持在 1 到 300 之间。";
  }
  return null;
}

export function buildShandongProjectionPayload(
  form: ShandongRecommendationFormState,
): StudentGaokaoScoreProjectionPayload {
  return {
    student_id: form.student_id as number,
    target_year: form.target_year,
    province: "山东",
    source_mode: "exam_projection",
    selected_exam_ids: [form.exam_id as number],
    note: "山东普通类推荐工作台自动生成",
  };
}

export function buildShandongRecommendationPayload(
  form: ShandongRecommendationFormState,
  projectionId?: number,
): ShandongRushStableSafeRecommendationPayload {
  const sourceMode = form.source_mode === "exam_projection" ? "projection" : form.source_mode;
  return {
    student_id: form.student_id,
    projection_id: projectionId,
    target_year: form.target_year,
    province: "山东",
    student_type: "general",
    batch: normalizeOptionalString(form.batch),
    subject_combination: formatSubjectCombination(form.selected_subjects_json),
    source_mode: sourceMode,
    manual_score: form.manual_score,
    manual_rank: form.manual_rank,
    risk_preference: form.risk_preference,
    target_regions_json: uniqueStrings(form.target_regions_json),
    school_level_tags_json: uniqueStrings(form.school_level_tags_json),
    major_keyword: normalizeOptionalString(form.major_keyword),
    limit: form.limit,
  };
}

export function buildShandongRecommendationReportName(result: ShandongRushStableSafeRecommendationResponse): string {
  return `${result.student_name || "未命名学生"} ${result.target_year} 山东普通类冲稳保推荐报告`;
}

export function buildShandongRecommendationExportPayload(result: ShandongRushStableSafeRecommendationResponse): {
  report_name: string;
  result: ShandongRushStableSafeRecommendationResponse;
} {
  return {
    report_name: buildShandongRecommendationReportName(result),
    result,
  };
}

export function buildShandongRecommendationPrintPayload(
  result: ShandongRushStableSafeRecommendationResponse,
  projection?: StudentGaokaoScoreProjectionRead | null,
  dataHealth?: ShandongRecommendationDataHealth | null,
): ShandongRecommendationPrintPayload {
  return {
    created_at: new Date().toISOString(),
    result,
    projection,
    data_health_summary: dataHealth?.summary ?? null,
    data_health_gaps: dataHealth?.gaps ?? [],
  };
}

export function buildShandongResultGroups(
  result: ShandongRushStableSafeRecommendationResponse | null,
): ShandongResultGroup[] {
  return [
    {
      key: "rush",
      label: "冲",
      description: "有机会但风险较高，适合作为前段冲刺。",
      tagType: "danger",
      items: result?.rush ?? [],
    },
    {
      key: "stable",
      label: "稳",
      description: "位次边际较合适，适合作为主体选择。",
      tagType: "warning",
      items: result?.stable ?? [],
    },
    {
      key: "safe",
      label: "保",
      description: "位次优势更明显，用于保底和防滑档。",
      tagType: "success",
      items: result?.safe ?? [],
    },
    {
      key: "watch",
      label: "仅关注",
      description: "数据不足、边际偏弱或需人工复核，不建议直接当作冲稳保结论。",
      tagType: "info",
      items: result?.watch ?? [],
    },
  ];
}

export function buildShandongCoverageRows(
  dataHealth: ShandongRecommendationDataHealth | null,
  targetYears = [2023, 2024, 2025],
): ShandongCoverageRow[] {
  if (!dataHealth) return [];
  return dataHealth.coverage.map((item) => {
    const coveredYears = targetYears.filter((year) => item.years.includes(year));
    const missingYears = targetYears.filter((year) => !item.years.includes(year));
    return {
      key: item.key,
      label: item.label,
      status: item.status,
      statusLabel: item.readiness_label || formatShandongStatus(item.status),
      total: item.total,
      coveredYears,
      missingYears,
      explanation: item.explanation || item.notes[0] || "当前暂无补充说明。",
    };
  });
}

export function getShandongHistoricalRankRows(
  candidate: ShandongRushStableSafeCandidate,
): ShandongHistoricalRankRow[] {
  const rows = candidate.historical_summary.rank_rows;
  if (!Array.isArray(rows)) return [];
  return rows
    .map((row) => (isRecord(row) ? row : null))
    .filter((row): row is Record<string, unknown> => Boolean(row))
    .map((row) => ({
      year: toNumber(row.year),
      min_rank: toNullableNumber(row.min_rank),
      min_score: toNullableNumber(row.min_score),
      plan_count: toNullableNumber(row.plan_count),
      source_note: typeof row.source_note === "string" ? row.source_note : null,
    }));
}

export function getShandongPlanChangeSummary(candidate: ShandongRushStableSafeCandidate): string {
  const planChange = isRecord(candidate.historical_summary.plan_change) ? candidate.historical_summary.plan_change : {};
  const targetCount = toNullableNumber(planChange.target_year_plan_count);
  const latestCount = toNullableNumber(planChange.latest_historical_plan_count);
  const factor = toNullableNumber(planChange.plan_change_factor);
  if (targetCount === null && latestCount === null) {
    return "目标年份计划暂缺，需要等正式计划或人工导入后复核。";
  }
  const parts = [
    targetCount === null ? "目标年份计划暂缺" : `目标年份计划 ${targetCount} 人`,
    latestCount === null ? "近年计划待补" : `近年参考计划 ${latestCount} 人`,
    factor === null ? null : `变化系数 ${factor.toFixed(2)}`,
  ].filter(Boolean);
  return parts.join("；");
}

export function getShandongReferenceRank(candidate: ShandongRushStableSafeCandidate): number | null {
  return toNullableNumber(candidate.score_summary.reference_rank);
}

export function getShandongLatestMinScore(candidate: ShandongRushStableSafeCandidate): number | null {
  return toNullableNumber(candidate.score_summary.latest_min_score);
}

export function getShandongLatestMinRank(candidate: ShandongRushStableSafeCandidate): number | null {
  return toNullableNumber(candidate.score_summary.latest_min_rank);
}

export function formatShandongRiskFlag(value: string): string {
  const mapping: Record<string, string> = {
    rank_projection_from_previous_year: "用上一年一分一段换位次",
    rank_projection_from_school_exam: "校内考试估算位次",
    three_year_data_incomplete: "近三年样本不完整",
    historical_data_missing: "历史样本不足",
    plan_missing: "目标年计划暂缺",
    plan_decreased: "计划数减少",
    subject_requirement_check: "选科仍需核对",
  };
  return mapping[value] ?? value;
}

export function formatShandongSourceMode(value?: string | null): string {
  const mapping: Record<string, string> = {
    exam_projection: "校内考试估算",
    manual_score: "手动预估分",
    manual_rank: "手动全省位次",
    projection: "学生预估快照",
  };
  return (value ? mapping[value] : null) ?? "待确认";
}

export function formatShandongRiskPreference(value?: string | null): string {
  const mapping: Record<string, string> = {
    conservative: "保守",
    balanced: "均衡",
    aggressive: "冲刺",
  };
  return (value ? mapping[value] : null) ?? "待确认";
}

export function formatShandongConfidence(value?: string | null): string {
  const mapping: Record<string, string> = {
    high: "高",
    medium: "中",
    low: "低",
  };
  return (value ? mapping[value] : null) ?? "待确认";
}

export function formatShandongStatus(value?: string | null): string {
  const mapping: Record<string, string> = {
    ok: "正常",
    gap: "需关注",
    missing: "缺失",
    ready: "已接入",
    imported: "已导入",
    published: "已公开",
    pending_official_release: "待官方发布",
    not_applicable: "当前不适用",
    manual_review_required: "需人工核验",
    partial: "部分可用",
    waiting: "待同步",
    empty: "暂无数据",
    no_year_column: "缺年份列",
  };
  return (value ? mapping[value] : null) ?? "待确认";
}

export function shandongStatusTagType(value?: string | null): "success" | "info" | "warning" | "danger" | undefined {
  if (["ok", "ready", "success", "imported"].includes(value ?? "")) return "success";
  if (["gap", "partial", "processing", "no_year_column", "published", "manual_review_required"].includes(value ?? "")) return "warning";
  if (["waiting", "frozen", "empty", "pending_official_release", "not_applicable"].includes(value ?? "")) return "info";
  if (["failed", "missing"].includes(value ?? "")) return "danger";
  return undefined;
}

export function shandongConfidenceTagType(value?: string | null): "success" | "info" | "warning" | "danger" {
  if (value === "high") return "success";
  if (value === "medium") return "warning";
  if (value === "low") return "danger";
  return "info";
}

export function formatNullableNumber(value?: number | null): string {
  return value === null || value === undefined ? "待补" : value.toLocaleString("zh-CN");
}

export function formatPercent(value?: number | null): string {
  return value === null || value === undefined ? "待补" : `${(value * 100).toFixed(1)}%`;
}

export function formatYearList(years?: number[]): string {
  return years?.length ? years.join("、") : "无";
}

export function formatShandongSourceDocumentIds(ids?: number[]): string {
  return ids?.length ? ids.map((id) => `来源 #${id}`).join("、") : "来源待补";
}

export function formatSubjectCombination(subjects: string[]): string | undefined {
  const selected = uniqueStrings(subjects);
  return selected.length ? selected.join(" ") : undefined;
}

function normalizeOptionalString(value?: string | null): string | undefined {
  const normalized = value?.trim();
  return normalized || undefined;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function toNumber(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function toNullableNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}
