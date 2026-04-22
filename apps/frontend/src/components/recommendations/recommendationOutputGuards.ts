import {
  buildRecommendationReportInsightCards,
  resolveRecommendationReportInsightContext,
} from "../reports/reportInsightRecommendation";
import type {
  RecommendationHistoryItem,
  RecommendationResult,
  VolunteerDraftCheckItem,
} from "./types";

export function buildVolunteerDraftOutputWarningMessage(checks: VolunteerDraftCheckItem[]): string | null {
  const warningTitles = checks.filter((item) => item.level === "warning").map((item) => item.title);
  if (!warningTitles.length) {
    return null;
  }
  return `当前草稿仍有这些提示：${warningTitles.slice(0, 3).join("；")}。建议先复核，再决定是否继续输出。`;
}

interface RecommendationSchemeOutputWarningOptions {
  history?: RecommendationHistoryItem[];
  compareResults?: RecommendationResult[];
}

export function buildRecommendationSchemeOutputWarningMessage(
  scheme: RecommendationHistoryItem,
  results: RecommendationResult[],
  options: RecommendationSchemeOutputWarningOptions = {},
): string | null {
  const insightContext = resolveRecommendationReportInsightContext(options.history ?? [], scheme);
  const segments = buildRecommendationReportInsightCards(
    results,
    insightContext.currentOption,
    options.compareResults ?? [],
    insightContext.compareOption,
  )
    .filter((card) => {
      if (card.key === "stable") {
        return false;
      }
      if (
        card.key === "simulation" &&
        (scheme.score_confidence === "actual" || scheme.score_confidence === "official")
      ) {
        return false;
      }
      return true;
    })
    .map((card) => card.summary);

  if (!segments.length) {
    return null;
  }
  return `${segments.join("；")}。建议先复核这些提醒，再决定是否继续打印或导出。`;
}
