import type {
  ProvinceVolunteerRule,
  VolunteerGuideCandidateGroup,
  VolunteerGuideGroupKey,
  VolunteerGuideNextAction,
  VolunteerGuideOptionItem,
  VolunteerGuideOptions,
  VolunteerGuidePreviewResponse,
  VolunteerGuideReadiness,
  VolunteerGuideReadinessItem,
  VolunteerGuideStepCard,
} from "./types";

const GUIDE_GROUP_ORDER: VolunteerGuideGroupKey[] = ["challenge", "steady", "safe", "watch"];
const VOLUNTEER_GUIDE_STEP_ORDER: VolunteerGuideProgressStep["key"][] = ["candidate", "preference", "screening", "draft"];

export type VolunteerGuideProgressState = "pending" | "active" | "done" | "warning" | "blocked";

export interface VolunteerGuideProgressStep {
  key: "candidate" | "preference" | "screening" | "draft";
  label: string;
  summary: string;
  state: VolunteerGuideProgressState;
}

export interface VolunteerBatchOptionGroups {
  available: string[];
  needsRule: string[];
  currentUnmatched?: string;
  suggestion?: {
    title: string;
    detail: string;
  };
}

export interface VolunteerBatchOptionGroupInput {
  batchOptions: string[];
  rules: ProvinceVolunteerRule[];
  currentBatch?: string | null;
  guideOptions?: VolunteerGuideOptions | null;
}

export interface VolunteerGuideDisplaySummary {
  totalCandidateCount: number;
  displayedCandidateCount: number;
  groupedDisplayedCount: number;
  isTruncated: boolean;
  copy: string;
}

export function buildVolunteerGuideReadiness(
  guide: VolunteerGuidePreviewResponse | null,
): VolunteerGuideReadiness {
  if (guide) {
    return guide.readiness;
  }
  return {
    status: "blocked",
    blocking_count: 1,
    warning_count: 0,
    info_count: 0,
    items: [
      {
        code: "not_generated",
        level: "blocking",
        title: "尚未生成智能筛选",
        detail: "请先确认考生条件和意向偏好，再点击生成推荐。",
      },
    ],
  };
}

export function groupVolunteerGuideCandidates(
  guide: VolunteerGuidePreviewResponse | null,
): VolunteerGuideCandidateGroup[] {
  if (!guide) {
    return GUIDE_GROUP_ORDER.map((key) => ({
      key,
      label: groupLabel(key),
      count: 0,
      candidates: [],
    }));
  }
  return GUIDE_GROUP_ORDER.map((key) => guide.groups[key] ?? {
    key,
    label: groupLabel(key),
    count: 0,
    candidates: [],
  });
}

export function buildVolunteerGuideDisplaySummary(
  guide: VolunteerGuidePreviewResponse | null,
): VolunteerGuideDisplaySummary {
  const groups = groupVolunteerGuideCandidates(guide);
  const groupedDisplayedCount = groups.reduce((sum, group) => sum + group.count, 0);
  const totalCandidateCount = guide?.source_preview.candidate_count ?? 0;
  const displayedCandidateCount = guide?.source_preview.returned_candidate_count ?? groupedDisplayedCount;
  const isTruncated = Boolean(
    guide?.source_preview.is_candidate_truncated
    || (displayedCandidateCount > 0 && totalCandidateCount > displayedCandidateCount),
  );
  const rankCopy = `生效位次 ${formatGuideSummaryValue(guide?.source_preview.effective_rank)}`;
  const scoreCopy = guide?.source_preview.score_input_label ?? "成绩/位次来源待确认";
  const countCopy = isTruncated
    ? `共命中 ${totalCandidateCount} 条候选，当前展示前 ${displayedCandidateCount} 条；分组卡统计当前展示候选`
    : `共 ${totalCandidateCount} 条候选`;

  return {
    totalCandidateCount,
    displayedCandidateCount,
    groupedDisplayedCount,
    isTruncated,
    copy: `${countCopy}；${rankCopy}；${scoreCopy}。`,
  };
}

export function buildVolunteerGuideProgressSteps(
  guide: VolunteerGuidePreviewResponse | null,
  draftCount = 0,
): VolunteerGuideProgressStep[] {
  const readiness = buildVolunteerGuideReadiness(guide);
  const candidateCount = guide?.source_preview.candidate_count ?? 0;
  const hasGenerated = Boolean(guide);
  const hasBlocking = readiness.status === "blocked";
  const steps: Record<VolunteerGuideProgressStep["key"], VolunteerGuideProgressStep> = {
    candidate: {
      key: "candidate",
      label: "考生条件",
      summary: guide
        ? `${guide.student_name || "当前学生"} · ${guide.province} · ${guide.target_year}`
        : "选择学生、考试、批次和成绩/位次",
      state: hasGenerated ? (hasBlocking ? "blocked" : "done") : "active",
    },
    preference: {
      key: "preference",
      label: "意向偏好",
      summary: hasPreferenceSignal(guide) ? "已纳入偏好" : "可选填，影响同层排序",
      state: hasGenerated ? (hasBlocking ? "warning" : "done") : "pending",
    },
    screening: {
      key: "screening",
      label: "智能筛选",
      summary: candidateCount ? `${candidateCount} 条候选` : hasGenerated ? "暂无可加入候选" : "生成后展示冲稳保结果",
      state: !hasGenerated ? "pending" : hasBlocking ? "blocked" : candidateCount ? "done" : "warning",
    },
    draft: {
      key: "draft",
      label: "志愿草稿",
      summary: draftCount ? `已加入 ${draftCount} 条` : "从候选加入后保存、打印、导出",
      state: draftCount ? "done" : candidateCount ? "active" : "pending",
    },
  };
  return VOLUNTEER_GUIDE_STEP_ORDER.map((key) => steps[key]);
}

export function buildVolunteerGuideStepCards(
  guide: VolunteerGuidePreviewResponse | null,
  draftCount = 0,
): VolunteerGuideStepCard[] {
  const readiness = buildVolunteerGuideReadiness(guide);
  const candidateCount = guide?.source_preview.candidate_count ?? 0;
  const preferenceStatus = hasPreferenceSignal(guide) ? "已纳入偏好" : "可继续补充";
  return [
    {
      key: "candidate",
      title: "考生条件",
      summary: guide
        ? `${guide.student_name || "当前学生"} · ${guide.province} · ${guide.target_year} · ${guide.source_preview.score_input_label}`
        : "选择学生、考试、年份、批次、科类、成绩/位次和选科组合",
      status: readiness.status,
    },
    {
      key: "preference",
      title: "意向偏好",
      summary: preferenceStatus,
      status: readiness.status === "blocked" ? "blocked" : "ready",
    },
    {
      key: "screening",
      title: "智能筛选",
      summary: candidateCount ? `${candidateCount} 条候选，按冲稳保分组` : "生成后展示冲刺、稳妥、保底和仅关注",
      status: candidateCount ? readiness.status : "blocked",
    },
    {
      key: "draft",
      title: "志愿草稿",
      summary: draftCount ? `已加入 ${draftCount} 条志愿` : "从候选加入草稿后排序、复核、保存和导出",
      status: draftCount ? "ready" : "warning",
    },
  ];
}

export function buildVolunteerBatchOptionGroups(input: VolunteerBatchOptionGroupInput): VolunteerBatchOptionGroups {
  const guideBatches = input.guideOptions?.batches.map((item) => item.value) ?? [];
  const maintainedRuleBatches = input.guideOptions?.maintained_rule_batches ?? [];
  const ruleBatches = uniqueOrderedStrings([
    ...guideBatches,
    ...maintainedRuleBatches,
    ...input.rules.map((item) => item.batch),
  ]);
  const normalizedCurrent = normalizeVolunteerBatchAlias(input.currentBatch, input.guideOptions);
  const allBatches = uniqueOrderedStrings([...ruleBatches, ...input.batchOptions, normalizedCurrent ?? "", input.currentBatch ?? ""]);
  const available = allBatches.filter((item) => ruleBatches.includes(item));
  const needsRule = allBatches.filter((item) => item && !ruleBatches.includes(item) && !isKnownBatchAlias(item, ruleBatches, input.guideOptions));
  const currentBatch = (normalizedCurrent ?? "").trim();
  const currentUnmatched = currentBatch && !ruleBatches.includes(currentBatch) ? currentBatch : undefined;
  const suggestionTarget = currentUnmatched ? findSimilarBatch(currentUnmatched, ruleBatches) : undefined;
  return {
    available,
    needsRule,
    currentUnmatched,
    suggestion: currentUnmatched
      ? {
          title: "当前批次还缺规则",
          detail: suggestionTarget
            ? `“${currentUnmatched}”暂未维护规则，可尝试选择已维护的“${suggestionTarget}”，或先到数据与规则补齐批次规则。`
            : `“${currentUnmatched}”暂未维护规则，请先到数据与规则补齐批次规则，或改选已维护批次。`,
        }
      : undefined,
  };
}

export function normalizeVolunteerBatchAlias(
  batch?: string | null,
  guideOptions?: VolunteerGuideOptions | null,
): string | undefined {
  const normalized = (batch ?? "").trim();
  if (!normalized) return undefined;
  return guideOptions?.batch_aliases[normalized] || normalized;
}

function isKnownBatchAlias(
  batch: string,
  ruleBatches: string[],
  guideOptions?: VolunteerGuideOptions | null,
): boolean {
  const normalized = normalizeVolunteerBatchAlias(batch, guideOptions);
  return Boolean(normalized && normalized !== batch && ruleBatches.includes(normalized));
}

export function buildVolunteerGuideOptionItems(
  backendOptions: ReadonlyArray<VolunteerGuideOptionItem> | undefined,
  fallbackOptions: ReadonlyArray<VolunteerGuideOptionItem>,
): VolunteerGuideOptionItem[] {
  return [...(backendOptions?.length ? backendOptions : fallbackOptions)];
}

export function calculateVolunteerArtComprehensiveScore(
  guideOptions: VolunteerGuideOptions | null,
  artTrack?: string | null,
  cultureScore?: number,
  professionalScore?: number,
): number | null {
  const normalizedTrack = (artTrack ?? "").trim();
  if (!normalizedTrack || cultureScore === undefined || professionalScore === undefined) return null;
  const formula = guideOptions?.art_score_formulas[normalizedTrack];
  if (
    !formula
    || formula.requires_manual_review
    || typeof formula.culture_weight !== "number"
    || typeof formula.professional_weight !== "number"
  ) {
    return null;
  }
  const fullScore = formula.professional_full_score && formula.professional_full_score > 0 ? formula.professional_full_score : 300;
  const value = cultureScore * formula.culture_weight + professionalScore * 750 / fullScore * formula.professional_weight;
  return Math.round(value * 100) / 100;
}

export function summarizeVolunteerReadinessItems(items: VolunteerGuideReadinessItem[], limit = 3): VolunteerGuideReadinessItem[] {
  return [...items]
    .sort((left, right) => readinessPriority(left) - readinessPriority(right))
    .slice(0, limit)
    .map((item) => ({
      ...item,
      title: readinessActionTitle(item),
      detail: readinessActionDetail(item),
    }));
}

export function buildVolunteerGuideActionItems(
  guide: VolunteerGuidePreviewResponse | null,
  limit = 2,
): VolunteerGuideNextAction[] {
  if (!guide) {
    return [
      {
        code: "start_from_candidate",
        level: "info",
        title: "先确认考生条件",
        detail: "选择学生和参考考试后，系统会自动带入可用的考试成绩。",
      },
    ];
  }
  return guide.next_actions.slice(0, limit);
}

function hasPreferenceSignal(guide: VolunteerGuidePreviewResponse | null): boolean {
  if (!guide) return false;
  return groupVolunteerGuideCandidates(guide).some((group) =>
    group.candidates.some((item) => Boolean(item.candidate.career_match_summary || item.candidate.matched_direction_names_json.length)),
  );
}

function groupLabel(key: VolunteerGuideGroupKey): string {
  const labels: Record<VolunteerGuideGroupKey, string> = {
    challenge: "冲刺",
    steady: "稳妥",
    safe: "保底",
    watch: "仅关注",
  };
  return labels[key];
}

function formatGuideSummaryValue(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === "") return "暂无";
  return String(value);
}

function uniqueOrderedStrings(values: Array<string | null | undefined>): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const value of values) {
    const normalized = (value ?? "").trim();
    if (!normalized || seen.has(normalized)) continue;
    seen.add(normalized);
    result.push(normalized);
  }
  return result;
}

function findSimilarBatch(current: string, candidates: string[]): string | undefined {
  const currentTokens = batchTokens(current);
  let best: { value: string; score: number } | undefined;
  for (const candidate of candidates) {
    const candidateTokens = batchTokens(candidate);
    const overlap = [...currentTokens].filter((token) => candidateTokens.has(token)).length;
    const score = overlap * 2 + (candidate.includes(current) || current.includes(candidate) ? 1 : 0);
    if (score <= 0) continue;
    if (!best || score > best.score) {
      best = { value: candidate, score };
    }
  }
  return best?.value;
}

function batchTokens(value: string): Set<string> {
  const compact = value.replace(/[（）()·\s]/g, "");
  const tokens = new Set<string>();
  for (const token of ["艺术", "本科", "专科", "统考", "普通", "常规", "提前", "春季", "高职", "专项"]) {
    if (compact.includes(token)) tokens.add(token);
  }
  return tokens;
}

function readinessPriority(item: VolunteerGuideReadinessItem): number {
  if (item.level === "blocking") {
    if (item.code.includes("target_year_enrollment_plan")) return -1;
    if (item.code.includes("rule")) return 0;
    if (item.code.includes("rank")) return 1;
    if (item.code.includes("score")) return 1;
    if (item.code.includes("candidate")) return 4;
    return 1;
  }
  if (item.code.includes("subject")) return 3;
  return item.level === "warning" ? 5 : 6;
}

function readinessActionTitle(item: VolunteerGuideReadinessItem): string {
  if (item.code.includes("target_year_enrollment_plan")) return "先处理招生计划";
  if (item.code.includes("rule")) return "先处理批次规则";
  if (item.code.includes("subject")) return "补充选科组合";
  if (item.code.includes("candidate")) return "调整条件或补充数据";
  if (item.code.includes("rank")) return "补充位次";
  if (item.code.includes("score")) return "补充分数";
  return item.title;
}

function readinessActionDetail(item: VolunteerGuideReadinessItem): string {
  const detail = item.detail.trim();
  if (detail.length <= 90) return detail;
  return `${detail.slice(0, 88)}...`;
}
