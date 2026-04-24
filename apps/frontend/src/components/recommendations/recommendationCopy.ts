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
  general_reference_fallback: "缺少专门录取结果，按普通类参考",
  score_line_reference_only: "缺少专门录取结果，按省控线初筛",
  cross_year_score_line_reference: "省控线按跨年份参考",
  plan_only_reference: "缺少专门结果，仅按计划清单初筛",
  chapter_pending_review: "章程待补链",
  chapter_special_requirement: "章程限制已提取",
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

export function formatRecommendationReferenceScope(scope?: string | null): string {
  if (scope === "college") return "院校线参考";
  if (scope === "score_line") return "省控线参考";
  if (scope === "plan_only") return "计划清单初筛";
  if (scope === "major") return "专业线参考";
  return "参考口径待补";
}

export function buildRecommendationReferenceCopy(item: RecommendationResult): string | null {
  if (!item.reference_scope && !item.reference_record_count) {
    return null;
  }
  const scopeLabel = formatRecommendationReferenceScope(item.reference_scope);
  const yearLabel = item.reference_years_json.length ? `${item.reference_years_json.join(" / ")} 年` : "年份待补";
  const sampleLabel = item.reference_scope === "score_line"
    ? "省级控制线口径"
    : item.reference_scope === "plan_only"
      ? "当年计划口径"
      : `${item.reference_record_count} 条样本`;
  const sourceLabel = item.reference_source_notes_json.length
    ? `来源：${item.reference_source_notes_json.join("；")}`
    : null;
  return [scopeLabel, yearLabel, sampleLabel, sourceLabel].filter(Boolean).join(" · ");
}

export function buildRecommendationFallbackPriorityCopy(item: RecommendationResult): string | null {
  const label = item.fallback_priority_label?.trim();
  if (!label || item.fallback_priority_score === null || item.fallback_priority_score === undefined) {
    return null;
  }
  const notes = item.fallback_priority_notes_json?.filter(Boolean) ?? [];
  const category = item.fallback_category_label?.trim();
  const reviewNotes = item.fallback_review_notes_json?.filter(Boolean) ?? [];
  const detailParts = [
    category ? `细分类别：${category}` : null,
    notes.length ? notes.join("；") : null,
    reviewNotes.length ? `核对清单：${reviewNotes.join("；")}` : null,
  ].filter(Boolean);
  const detailText = detailParts.length ? `：${detailParts.join("；")}` : "";
  return `初筛优先级：${label}（${item.fallback_priority_score}）${detailText}`;
}

export function buildRecommendationBoundaryNotes(
  item: RecommendationResult,
  targetYear?: number | null,
): string[] {
  const notes: string[] = [];
  if (item.reference_scope === "college" && item.major_id) {
    notes.push("当前专业缺少专业线，先回退到院校线参考；同校不同专业结果仍可能继续变化。");
  }
  if (item.reference_scope === "score_line") {
    notes.push("当前结果只按省级控制线做资格初筛，不能直接视作院校或专业录取把握。");
  }
  if (item.reference_scope === "plan_only") {
    notes.push("当前结果只按当年招生计划清单做方向性初筛，不能直接作为冲稳保或录取把握判断。");
  }
  const priorityCopy = buildRecommendationFallbackPriorityCopy(item);
  if (priorityCopy) {
    notes.push(priorityCopy);
  }
  const snapshot = item.snapshot_json ?? null;
  if (typeof snapshot?.batch_dict_note === "string" && snapshot.batch_dict_note.trim()) {
    notes.push(`批次词典：${snapshot.batch_dict_note.trim()}`);
  }
  if (typeof snapshot?.province_policy_summary === "string" && snapshot.province_policy_summary.trim()) {
    notes.push(`政策摘要：${snapshot.province_policy_summary.trim()}`);
  } else if (typeof snapshot?.province_policy_title === "string" && snapshot.province_policy_title.trim()) {
    notes.push(`省级政策：${snapshot.province_policy_title.trim()}`);
  }
  const staleNote = buildRecommendationStaleReferenceNote(item.snapshot_json ?? null, targetYear);
  if (staleNote) {
    notes.push(staleNote);
  }
  return notes;
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
