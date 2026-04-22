import type { RecommendationResult } from "./types";

export interface RecommendationInsightContext {
  province?: string | null;
  target_year?: number | null;
  score_input_label?: string | null;
  reference_exam_name?: string | null;
  use_historical_mapping?: boolean;
  score_confidence?: string | null;
}

export const RECOMMENDATION_PATH_MISMATCH_FLAGS = [
  "postgraduate_path_mismatch",
  "certificate_path_mismatch",
  "long_training_path_mismatch",
  "public_service_path_mismatch",
] as const;

const RECOMMENDATION_RISK_FLAG_LABELS: Record<string, string> = {
  sample_insufficient: "样本不足",
  rank_missing: "缺少位次，分数参考",
  art_recommendation: "艺体推荐",
  track_unconfirmed: "艺体方向待确认",
  manual_formula_check: "需人工核对招生章程",
  whitelist_override: "白名单放宽",
  career_mapping_pending: "职业路径映射待维护",
  postgraduate_path_mismatch: "与读研接受度不匹配",
  certificate_path_mismatch: "与资格证接受度不匹配",
  long_training_path_mismatch: "与长培养周期接受度不匹配",
  public_service_path_mismatch: "与考公考编接受度不匹配",
  major_baseline_missing: "专业线缺失，按院校线参考",
  subject_requirement_check: "需复核选科要求",
};

export function getRecommendationRiskFlagText(flag: string): string {
  return RECOMMENDATION_RISK_FLAG_LABELS[flag] ?? flag;
}

export function formatRecommendationRiskFlags(flags?: string[] | null): string {
  if (!flags?.length) return "-";
  return flags.map((flag) => getRecommendationRiskFlagText(flag)).join(" / ");
}

export function countRecommendationPathMismatches(results: RecommendationResult[]): number {
  return results.filter((item) =>
    RECOMMENDATION_PATH_MISMATCH_FLAGS.some((flag) => item.risk_flags_json?.includes(flag)),
  ).length;
}

export function buildRecommendationSimulationNote(context: RecommendationInsightContext | null | undefined): string {
  if (!context) return "默认推荐链路";

  const hints: string[] = [];
  if (context.reference_exam_name?.trim()) {
    hints.push(`参考考试：${context.reference_exam_name.trim()}`);
  }
  if (context.use_historical_mapping) {
    hints.push("已启用历史映射");
  }
  if (hints.length) {
    return hints.join(" / ");
  }
  if (context.score_confidence === "official" || context.score_confidence === "actual") {
    return "当前按正式成绩/位次生成";
  }
  if (context.score_confidence === "score_only") {
    return "当前按分数模式估算";
  }
  if (context.score_confidence === "estimated" || context.score_confidence === "range_estimated") {
    return "当前结果为模拟测算";
  }
  return "默认推荐链路";
}

export function shouldShowRecommendationSimulationCard(context: RecommendationInsightContext | null | undefined): boolean {
  return Boolean(
    context?.score_input_label ||
      context?.reference_exam_name ||
      context?.use_historical_mapping ||
      (context?.score_confidence && context.score_confidence !== "actual" && context.score_confidence !== "official"),
  );
}

export function buildRecommendationStaleReferenceNote(
  snapshot?: Record<string, unknown> | null,
  targetYear?: number | null,
): string | null {
  const gap = getRecommendationReferenceYearGap(snapshot, targetYear);
  if (gap === null || gap < 2) {
    return null;
  }
  const referenceYears = getRecommendationReferenceYears(snapshot);
  if (!referenceYears.length) {
    return null;
  }
  return `当前录取参考最近只到 ${Math.max(...referenceYears)} 年，与 ${targetYear} 目标年相差 ${gap} 年；若近一年数据尚未补齐，排序和解释会偏保守。`;
}

export function getRecommendationReferenceYearGap(
  snapshot?: Record<string, unknown> | null,
  targetYear?: number | null,
): number | null {
  if (typeof targetYear !== "number") {
    return null;
  }
  const referenceYears = getRecommendationReferenceYears(snapshot);
  if (!referenceYears.length) {
    return null;
  }
  return targetYear - Math.max(...referenceYears);
}

export function getRecommendationReferenceYears(snapshot?: Record<string, unknown> | null): number[] {
  const rawYears = Array.isArray(snapshot?.reference_years) ? snapshot.reference_years : [];
  return rawYears.filter((value): value is number => typeof value === "number");
}
