import {
  getRecommendationReferenceYearGap,
  buildRecommendationSimulationNote,
  countRecommendationPathMismatches,
  shouldShowRecommendationSimulationCard,
} from "../recommendations/recommendationCopy";
import {
  buildRecommendationSchemeComparison,
  findNearestRecommendationCompareScheme,
} from "../recommendations/recommendationComparison";
import type { RecommendationResult } from "../recommendations/types";
import type {
  ReportInsightCardGroup,
  RecommendationReportInsightCompareOption,
  RecommendationReportInsightOption,
  ReportInsightCard,
} from "./reportInsightTypes";

const RECOMMENDATION_HISTORY_CARD_KEYS = new Set([
  "history_comparison",
  "cross_province_comparison",
  "same_province_year_comparison",
  "history_reference_shift",
]);
const RECOMMENDATION_BOUNDARY_CARD_KEYS = new Set([
  "simulation",
  "sample_insufficient",
  "rank_missing",
  "manual_formula_check",
  "stale_reference_years",
  "stable",
]);

interface RecommendationReportInsightSource {
  province?: string | null;
  target_year?: number | null;
  score_input_label?: string | null;
  reference_exam_name?: string | null;
  use_historical_mapping?: boolean;
  score_confidence?: string | null;
}

interface RecommendationReportInsightComparableSource extends RecommendationReportInsightSource {
  scheme_id: number;
  student_id: number;
  generated_at: string;
  scheme_name?: string | null;
}

export function buildRecommendationReportInsightOption(
  source: RecommendationReportInsightSource | null | undefined,
): RecommendationReportInsightOption | null {
  if (!source) {
    return null;
  }
  return {
    province: source.province,
    target_year: source.target_year,
    score_input_label: source.score_input_label,
    reference_exam_name: source.reference_exam_name,
    use_historical_mapping: source.use_historical_mapping,
    score_confidence: source.score_confidence,
  };
}

export function buildRecommendationReportInsightCompareOption(
  source: RecommendationReportInsightComparableSource | null | undefined,
): RecommendationReportInsightCompareOption | null {
  if (!source) {
    return null;
  }
  return {
    scheme_id: source.scheme_id,
    scheme_name: source.scheme_name,
    generated_at: source.generated_at,
    province: source.province,
    target_year: source.target_year,
  };
}

export function resolveRecommendationReportInsightContext<T extends RecommendationReportInsightComparableSource>(
  history: T[],
  current: T | null | undefined,
): {
  currentOption: RecommendationReportInsightOption | null;
  compareScheme: T | null;
  compareOption: RecommendationReportInsightCompareOption | null;
} {
  const compareScheme = current ? findNearestRecommendationCompareScheme(history, current) : null;
  return {
    currentOption: buildRecommendationReportInsightOption(current),
    compareScheme,
    compareOption: buildRecommendationReportInsightCompareOption(compareScheme),
  };
}

export function buildRecommendationReportInsightCards(
  results: RecommendationResult[],
  option: RecommendationReportInsightOption | null,
  compareResults: RecommendationResult[] = [],
  compareOption: RecommendationReportInsightCompareOption | null = null,
): ReportInsightCard[] {
  const cards: ReportInsightCard[] = [];

  if (shouldShowRecommendationSimulationCard(option)) {
    const simulationNote = buildRecommendationSimulationNote(option);
    cards.push({
      key: "simulation",
      title: "模拟结果",
      summary: `当前推荐结果基于“${option?.score_input_label || "默认推荐链路"}”生成`,
      detail: simulationNote === "默认推荐链路" ? "当前结果带模拟链路说明，导出前建议确认正式位次是否已更新。" : simulationNote,
      tone: "info",
    });
  }

  if (results.length && compareResults.length && compareOption) {
    const comparison = buildRecommendationSchemeComparison(results, compareResults, {
      currentTargetYear: option?.target_year,
      compareTargetYear: compareOption.target_year,
      currentProvince: option?.province,
      compareProvince: compareOption.province,
    });
    const changedCount = comparison.added.length + comparison.removed.length + comparison.changed.length;
    const currentProvince = option?.province?.trim();
    const compareProvince = compareOption.province?.trim();
    const currentTargetYear = option?.target_year;
    const compareTargetYear = compareOption.target_year;
    const hasCrossProvinceScope = Boolean(currentProvince && compareProvince && currentProvince !== compareProvince);
    const hasSameProvinceYearScope = Boolean(
      currentProvince
      && compareProvince
      && currentProvince === compareProvince
      && currentTargetYear != null
      && compareTargetYear != null
      && currentTargetYear !== compareTargetYear,
    );
    const compareLabel = buildRecommendationCompareLabel(compareOption);
    cards.push({
      key: "history_comparison",
      title: "历史方案差异",
      summary: changedCount
        ? `相对${compareLabel}，当前方案新增 ${comparison.added.length} 条、移除 ${comparison.removed.length} 条、分组调整 ${comparison.changed.length} 条`
        : `相对${compareLabel}，当前方案结构保持稳定`,
      detail: `${buildRecommendationGroupDeltaDetail(comparison.deltaByGroup)}；保留 ${comparison.commonCount} 条可比结果。`,
      tone: changedCount ? "info" : "success",
    });
    if (comparison.referenceSummary) {
      const crossProvinceSummary = comparison.referenceSummary.affectedCount;
      const sameProvinceYearImpactCount = comparison.referenceSummary.changedCount + comparison.referenceSummary.staleShiftCount;
      if (hasCrossProvinceScope && crossProvinceSummary > 0) {
        cards.push({
          key: "cross_province_comparison",
          title: "跨省口径差异",
          summary: `${crossProvinceSummary} 条可比结果受跨省口径影响`,
          detail: `当前方案按 ${currentProvince} 口径，对比方案按 ${compareProvince} 口径；同校同专业在跨省比较时，录取位次和分组变化属于正常现象。`,
          tone: "warning",
        });
      }
      if (hasSameProvinceYearScope && sameProvinceYearImpactCount > 0) {
        cards.push({
          key: "same_province_year_comparison",
          title: "同省跨年份差异",
          summary: `${sameProvinceYearImpactCount} 条可比结果受同省跨年份口径变化影响`,
          detail: buildRecommendationSameProvinceYearMetricDetail({
            referenceRankShiftCount: comparison.referenceSummary.referenceRankShiftCount,
            latestMinRankShiftCount: comparison.referenceSummary.latestMinRankShiftCount,
            latestMinScoreShiftCount: comparison.referenceSummary.latestMinScoreShiftCount,
          }),
          tone: "info",
        });
      }
      cards.push({
        key: "history_reference_shift",
        title: "历史方案参考变化",
        summary: comparison.referenceSummary.summary,
        detail: `${compareLabel}；${comparison.referenceSummary.detail}`,
        tone: "warning",
      });
    }
  }

  const sampleInsufficientCount = results.filter((item) => item.risk_flags_json?.includes("sample_insufficient")).length;
  if (sampleInsufficientCount) {
    cards.push({
      key: "sample_insufficient",
      title: "样本不足",
      summary: `${sampleInsufficientCount} 条结果存在样本不足提示`,
      detail: "这类推荐更适合作为方向性参考，建议结合近年数据和学校经验做二次判断。",
      tone: "warning",
    });
  }

  const rankMissingCount = results.filter((item) => item.risk_flags_json?.includes("rank_missing")).length;
  if (rankMissingCount) {
    cards.push({
      key: "rank_missing",
      title: "缺少位次口径",
      summary: `${rankMissingCount} 条结果已改按分数参考`,
      detail: "位次口径不完整时，结果稳定性会低于标准位次链路，建议后续用正式位次复核。",
      tone: "warning",
    });
  }

  const manualCheckCount = results.filter((item) => item.risk_flags_json?.includes("manual_formula_check")).length;
  if (manualCheckCount) {
    cards.push({
      key: "manual_formula_check",
      title: "需人工复核",
      summary: `${manualCheckCount} 条结果仍需人工核对招生章程`,
      detail: "这类推荐通常涉及规则边界、专业限制或特殊口径，不能直接作为最终填报结论。",
      tone: "warning",
    });
  }

  const pathMismatchCount = countRecommendationPathMismatches(results);
  if (pathMismatchCount) {
    cards.push({
      key: "path_mismatch",
      title: "职业路径不完全匹配",
      summary: `${pathMismatchCount} 条结果与当前可接受路径存在偏差`,
      detail: "建议结合学生对读研、资格证、长培养周期和考公考编路径的接受度再做筛选。",
      tone: "info",
    });
  }

  const staleReferenceCount = results.filter((item) => hasStaleRecommendationReferenceYears(item, option?.target_year)).length;
  if (staleReferenceCount) {
    cards.push({
      key: "stale_reference_years",
      title: "参考年份偏旧",
      summary: `${staleReferenceCount} 条结果最近录取样本与目标年份相差 2 年及以上`,
      detail: "这类推荐更适合作为方向性参考；若近一年录取数据尚未补齐，分层、排序和汇报口径都可能继续变化。",
      tone: "warning",
    });
  }

  if (!cards.length && results.length) {
    cards.push({
      key: "stable",
      title: "当前结果边界较清晰",
      summary: `${results.length} 条推荐结果当前未发现明显的全局风险提示`,
      detail: "当前结果主要可按已有位次/分数链路和职业匹配说明做进一步筛选与汇报。",
      tone: "success",
    });
  }

  return cards;
}

export function buildRecommendationReportInsightCardGroups(
  cards: ReportInsightCard[],
): ReportInsightCardGroup[] {
  const historyCards = cards.filter((item) => RECOMMENDATION_HISTORY_CARD_KEYS.has(item.key));
  const boundaryCards = cards.filter((item) => RECOMMENDATION_BOUNDARY_CARD_KEYS.has(item.key));
  const riskCards = cards.filter(
    (item) => !RECOMMENDATION_HISTORY_CARD_KEYS.has(item.key) && !RECOMMENDATION_BOUNDARY_CARD_KEYS.has(item.key),
  );
  const groups: ReportInsightCardGroup[] = [];
  if (historyCards.length) {
    groups.push({
      key: "history",
      title: "历史对照摘要",
      cards: historyCards,
    });
  }
  if (boundaryCards.length) {
    groups.push({
      key: "boundary",
      title: "边界概览",
      cards: boundaryCards,
    });
  }
  if (riskCards.length) {
    groups.push({
      key: "risk",
      title: "风险概览",
      cards: riskCards,
    });
  }
  return groups;
}

function hasStaleRecommendationReferenceYears(
  item: RecommendationResult,
  targetYear?: number | null,
): boolean {
  const gap = getRecommendationReferenceYearGap(item.snapshot_json ?? null, targetYear);
  return gap !== null && gap >= 2;
}

function buildRecommendationCompareLabel(option: RecommendationReportInsightCompareOption): string {
  const schemeLabel = option.scheme_name?.trim() || "最近历史方案";
  const generatedDate = option.generated_at?.slice(0, 10);
  return generatedDate ? `“${schemeLabel}”（${generatedDate}）` : `“${schemeLabel}”`;
}

function buildRecommendationGroupDeltaDetail(
  deltas: Array<{ label: string; current: number; compare: number; delta: number }>,
): string {
  return deltas
    .map((item) => `${item.label} ${item.current} 对 ${item.compare}（${formatSignedDelta(item.delta)}）`)
    .join("；");
}

function buildRecommendationSameProvinceYearMetricDetail(options: {
  referenceRankShiftCount: number;
  latestMinRankShiftCount: number;
  latestMinScoreShiftCount: number;
}): string {
  const segments: string[] = [];
  if (options.referenceRankShiftCount) {
    segments.push(`${options.referenceRankShiftCount} 条参考位次变化`);
  }
  if (options.latestMinRankShiftCount) {
    segments.push(`${options.latestMinRankShiftCount} 条最近最低位次变化`);
  }
  if (options.latestMinScoreShiftCount) {
    segments.push(`${options.latestMinScoreShiftCount} 条最近最低分变化`);
  }
  if (!segments.length) {
    return "当前至少有参考年份或“年份偏旧”状态切换，即使位次/分数口径暂未明显变化，解释口径也已经按不同年份样本重算。";
  }
  return `当前可比结果里，${segments.join("，")}，说明同省跨年份对照下录取样本和参考口径本身已经更新，分组和排序变化属于正常现象。`;
}

function formatSignedDelta(value: number): string {
  if (value > 0) return `+${value}`;
  if (value < 0) return `${value}`;
  return "0";
}
