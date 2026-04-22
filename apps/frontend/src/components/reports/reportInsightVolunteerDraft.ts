import {
  buildVolunteerDraftBoundaryInsightCards,
  buildVolunteerRuleInsightCardsFromRules,
} from "../recommendations/volunteerWorkbench";
import type { VolunteerDraftDetail } from "../recommendations/types";
import type { ReportInsightCard, ReportInsightCardGroup } from "./reportInsightTypes";

const VOLUNTEER_DRAFT_RULE_CARD_KEYS = new Set([
  "baseline",
  "compatible_mode",
  "candidate_specific_rule",
  "missing_rule",
  "missing_rule_province",
  "missing_rule_year",
  "missing_rule_batch",
  "missing_rule_candidate_type",
  "missing_rule_exam_mode",
  "general_candidate_rule",
]);

const VOLUNTEER_DRAFT_BOUNDARY_CARD_KEYS = new Set([
  "college_fallback",
  "mixed_reference_years",
  "stale_reference_years",
  "cross_province",
  "stable",
]);

export function buildVolunteerDraftReportInsightCards(options: {
  rules?: VolunteerDraftDetail["applicable_rules"];
  selectedRule?: VolunteerDraftDetail["selected_rule"];
  draftItems?: VolunteerDraftDetail["items"];
  ruleAlerts?: VolunteerDraftDetail["rule_alerts"];
}): ReportInsightCard[] {
  const ruleCards = buildVolunteerRuleInsightCardsFromRules(options.rules ?? [], options.selectedRule ?? null).map((card) => {
    const factSummary = card.facts.map((item) => `${item.label}：${item.value}`).join("；");
    const noteSummary = card.notes.join("；");
    return {
      key: `rule_${card.key}`,
      title: card.isSelected ? `${card.title}（当前控制规则）` : `${card.title}（兼容预览规则）`,
      summary: card.subtitle,
      detail: noteSummary ? `${factSummary}。${noteSummary}` : factSummary,
      tone: card.isSelected ? "success" : "info",
    } satisfies ReportInsightCard;
  });

  const boundaryCards = buildVolunteerDraftBoundaryInsightCards(
    options.draftItems ?? [],
    options.selectedRule ?? null,
    options.ruleAlerts ?? [],
  );

  return [...ruleCards, ...boundaryCards];
}

export function buildVolunteerDraftReportInsightCardGroups(cards: ReportInsightCard[]): ReportInsightCardGroup[] {
  const ruleCards = cards.filter((item) => item.key.startsWith("rule_") || VOLUNTEER_DRAFT_RULE_CARD_KEYS.has(item.key));
  const boundaryCards = cards.filter((item) => VOLUNTEER_DRAFT_BOUNDARY_CARD_KEYS.has(item.key));
  const riskCards = cards.filter(
    (item) =>
      !item.key.startsWith("rule_")
      && !VOLUNTEER_DRAFT_RULE_CARD_KEYS.has(item.key)
      && !VOLUNTEER_DRAFT_BOUNDARY_CARD_KEYS.has(item.key),
  );

  const groups: ReportInsightCardGroup[] = [];
  if (ruleCards.length) {
    groups.push({
      key: "live_rule",
      title: "规则差异摘要",
      cards: ruleCards,
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
