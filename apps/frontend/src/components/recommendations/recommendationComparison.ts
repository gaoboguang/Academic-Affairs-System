import type { RecommendationResult, ResultGroupKey } from "./types";

export interface RecommendationComparisonEntry {
  key: string;
  label: string;
  currentType?: ResultGroupKey;
  compareType?: ResultGroupKey;
}

export interface RecommendationComparisonReferenceSummary {
  affectedCount: number;
  changedCount: number;
  staleShiftCount: number;
  staleOnlyCount: number;
  groupShiftCount: number;
  referenceRankShiftCount: number;
  latestMinRankShiftCount: number;
  latestMinScoreShiftCount: number;
  summary: string;
  detail: string;
}

export interface RecommendationSchemeComparisonSummary {
  added: RecommendationComparisonEntry[];
  removed: RecommendationComparisonEntry[];
  changed: RecommendationComparisonEntry[];
  commonCount: number;
  deltaByGroup: Array<{ key: ResultGroupKey; label: string; current: number; compare: number; delta: number }>;
  referenceSummary: RecommendationComparisonReferenceSummary | null;
}

const resultColumns: Array<{ key: ResultGroupKey; label: string }> = [
  { key: "challenge", label: "冲刺" },
  { key: "steady", label: "稳妥" },
  { key: "safe", label: "保底" },
  { key: "watch", label: "仅关注" },
];

interface RecommendationComparableScheme {
  scheme_id: number;
  student_id: number;
  generated_at: string;
}

export function findNearestRecommendationCompareScheme<T extends RecommendationComparableScheme>(
  options: T[],
  current: T | null,
): T | null {
  if (!current) {
    return null;
  }
  const currentTimestamp = Date.parse(current.generated_at);
  return options
    .filter((item) => item.student_id === current.student_id && item.scheme_id !== current.scheme_id)
    .sort((left, right) => {
      const distanceDelta =
        getRecommendationGeneratedAtDistance(left.generated_at, currentTimestamp)
        - getRecommendationGeneratedAtDistance(right.generated_at, currentTimestamp);
      if (distanceDelta !== 0) {
        return distanceDelta;
      }
      return right.generated_at.localeCompare(left.generated_at);
    })[0] ?? null;
}

export function buildRecommendationSchemeComparison(
  currentResults: RecommendationResult[],
  compareResults: RecommendationResult[],
  options?: {
    currentTargetYear?: number | null;
    compareTargetYear?: number | null;
    currentProvince?: string | null;
    compareProvince?: string | null;
  },
): RecommendationSchemeComparisonSummary {
  const currentMap = new Map<string, RecommendationResult>();
  const compareMap = new Map<string, RecommendationResult>();
  for (const item of currentResults) currentMap.set(recommendationKey(item), item);
  for (const item of compareResults) compareMap.set(recommendationKey(item), item);

  const added: RecommendationComparisonEntry[] = [];
  const removed: RecommendationComparisonEntry[] = [];
  const changed: RecommendationComparisonEntry[] = [];
  let commonCount = 0;
  let referenceYearChangedCount = 0;
  let staleShiftCount = 0;
  let referenceAffectedCount = 0;
  let staleOnlyCount = 0;
  let referenceYearGroupShiftCount = 0;
  let referenceRankShiftCount = 0;
  let latestMinRankShiftCount = 0;
  let latestMinScoreShiftCount = 0;

  currentMap.forEach((currentItem, key) => {
    const compareItem = compareMap.get(key);
    if (!compareItem) {
      added.push({ key, label: recommendationLabel(currentItem), currentType: currentItem.result_type });
      return;
    }

    if (
      hasRecommendationMetricShift(
        readRecommendationNumber(currentItem.reference_rank),
        readRecommendationNumber(compareItem.reference_rank),
      )
    ) {
      referenceRankShiftCount += 1;
    }
    if (
      hasRecommendationMetricShift(
        getRecommendationSnapshotNumber(currentItem, "latest_min_rank"),
        getRecommendationSnapshotNumber(compareItem, "latest_min_rank"),
      )
    ) {
      latestMinRankShiftCount += 1;
    }
    if (
      hasRecommendationMetricShift(
        getRecommendationSnapshotNumber(currentItem, "latest_min_score"),
        getRecommendationSnapshotNumber(compareItem, "latest_min_score"),
      )
    ) {
      latestMinScoreShiftCount += 1;
    }

    const currentLatestReferenceYear = getRecommendationLatestReferenceYear(currentItem);
    const compareLatestReferenceYear = getRecommendationLatestReferenceYear(compareItem);
    let referenceYearChanged = false;
    if (
      currentLatestReferenceYear !== null
      && compareLatestReferenceYear !== null
      && currentLatestReferenceYear !== compareLatestReferenceYear
    ) {
      referenceYearChanged = true;
      referenceYearChangedCount += 1;
      if (compareItem.result_type !== currentItem.result_type) {
        referenceYearGroupShiftCount += 1;
      }
    }

    const currentIsStale = hasStaleRecommendationReferenceYear(currentItem, options?.currentTargetYear);
    const compareIsStale = hasStaleRecommendationReferenceYear(compareItem, options?.compareTargetYear);
    const staleStateChanged = currentIsStale !== compareIsStale;
    if (referenceYearChanged || staleStateChanged) {
      referenceAffectedCount += 1;
    }
    if (staleStateChanged) {
      staleShiftCount += 1;
      if (!referenceYearChanged) {
        staleOnlyCount += 1;
      }
    }

    if (compareItem.result_type !== currentItem.result_type) {
      changed.push({
        key,
        label: recommendationLabel(currentItem),
        currentType: currentItem.result_type,
        compareType: compareItem.result_type,
      });
      return;
    }
    commonCount += 1;
  });

  compareMap.forEach((compareItem, key) => {
    if (!currentMap.has(key)) {
      removed.push({ key, label: recommendationLabel(compareItem), compareType: compareItem.result_type });
    }
  });

  const currentGroupCounts = buildRecommendationGroupCounts(currentResults);
  const compareGroupCounts = buildRecommendationGroupCounts(compareResults);

  return {
    added,
    removed,
    changed,
    commonCount,
    deltaByGroup: resultColumns.map((column) => ({
      key: column.key,
      label: column.label,
      current: currentGroupCounts[column.key],
      compare: compareGroupCounts[column.key],
      delta: currentGroupCounts[column.key] - compareGroupCounts[column.key],
    })),
    referenceSummary: buildRecommendationReferenceSummary({
      changedCount: referenceYearChangedCount,
      affectedCount: referenceAffectedCount,
      staleShiftCount,
      staleOnlyCount,
      groupShiftCount: referenceYearGroupShiftCount,
      currentTargetYear: options?.currentTargetYear,
      compareTargetYear: options?.compareTargetYear,
      currentProvince: options?.currentProvince,
      compareProvince: options?.compareProvince,
      referenceRankShiftCount,
      latestMinRankShiftCount,
      latestMinScoreShiftCount,
    }),
  };
}

function buildRecommendationReferenceSummary(options: {
  changedCount: number;
  affectedCount: number;
  staleShiftCount: number;
  staleOnlyCount: number;
  groupShiftCount: number;
  currentTargetYear?: number | null;
  compareTargetYear?: number | null;
  currentProvince?: string | null;
  compareProvince?: string | null;
  referenceRankShiftCount: number;
  latestMinRankShiftCount: number;
  latestMinScoreShiftCount: number;
}): RecommendationComparisonReferenceSummary | null {
  const {
    changedCount,
    affectedCount,
    staleShiftCount,
    staleOnlyCount,
    groupShiftCount,
    currentTargetYear,
    compareTargetYear,
    currentProvince,
    compareProvince,
    referenceRankShiftCount,
    latestMinRankShiftCount,
    latestMinScoreShiftCount,
  } = options;
  if (!changedCount && !staleShiftCount) {
    return null;
  }

  const yearSummary =
    typeof currentTargetYear === "number" && typeof compareTargetYear === "number" && currentTargetYear !== compareTargetYear
      ? `当前方案目标年份 ${currentTargetYear}，对比方案目标年份 ${compareTargetYear}`
      : "两版方案的可比推荐在近年样本上出现了变化";

  const summarySegments: string[] = [];
  if (changedCount) {
    const groupImpactText =
      groupShiftCount > 0
        ? `其中 ${groupShiftCount} 条同时伴随冲稳保分组变化`
        : "目前还未直接带来冲稳保分组变化";
    summarySegments.push(`${changedCount} 条保留院校/专业的最近录取样本年份发生变化，${groupImpactText}`);
  }
  if (staleShiftCount) {
    summarySegments.push(`${staleShiftCount} 条结果的“年份偏旧”状态发生变化`);
  }

  const groupImpactDetail =
    changedCount && groupShiftCount === 0
      ? "这些变化当前更多影响解释口径和排序，不一定会直接改动冲稳保分组。"
      : changedCount
        ? `在参考年份发生变化的保留结果里，有 ${groupShiftCount} 条同时出现了冲稳保分组调整。`
        : "当前没有检测到明确的参考年份切换，但“年份偏旧”状态已经发生变化。";

  const provinceSummary =
    currentProvince && compareProvince && currentProvince !== compareProvince
      ? `当前方案按 ${currentProvince} 口径，对比方案按 ${compareProvince} 口径；同校同专业在跨省比较时，录取位次和分组变化属于正常现象。`
      : null;
  const sameProvinceYearSummary =
    currentProvince
      && compareProvince
      && currentProvince === compareProvince
      && typeof currentTargetYear === "number"
      && typeof compareTargetYear === "number"
      && currentTargetYear !== compareTargetYear
      ? `两版方案都按 ${currentProvince} 口径，但目标年份不同；${buildRecommendationSameProvinceYearMetricDetail({
        referenceRankShiftCount,
        latestMinRankShiftCount,
        latestMinScoreShiftCount,
      })}`
      : null;
  const staleOnlySummary =
    staleOnlyCount > 0
      ? `其中 ${staleOnlyCount} 条只是“年份偏旧”状态切换，最近录取样本年份本身未变化，通常意味着目标年份切换后，旧样本是否仍算“偏旧”的判断发生了变化。`
      : null;

  return {
    affectedCount,
    changedCount,
    staleShiftCount,
    staleOnlyCount,
    groupShiftCount,
    referenceRankShiftCount,
    latestMinRankShiftCount,
    latestMinScoreShiftCount,
    summary: summarySegments.join("，"),
    detail: [
      yearSummary,
      groupImpactDetail,
      staleOnlySummary,
      provinceSummary,
      sameProvinceYearSummary,
      "若同校同专业的参考年份被补新或回退，分组、排序和汇报口径出现变化属于正常现象。",
    ]
      .filter(Boolean)
      .join("；"),
  };
}

function buildRecommendationGroupCounts(results: RecommendationResult[]): Record<ResultGroupKey, number> {
  return results.reduce<Record<ResultGroupKey, number>>(
    (accumulator, item) => {
      accumulator[item.result_type] += 1;
      return accumulator;
    },
    { challenge: 0, steady: 0, safe: 0, watch: 0 },
  );
}

function recommendationKey(item: RecommendationResult): string {
  return `${item.college_id}-${item.major_id ?? 0}`;
}

function recommendationLabel(item: RecommendationResult): string {
  return [item.college_name, item.major_name || "院校级推荐"].filter(Boolean).join(" / ");
}

function hasStaleRecommendationReferenceYear(item: RecommendationResult, targetYear?: number | null): boolean {
  if (typeof targetYear !== "number") {
    return false;
  }
  const latestReferenceYear = getRecommendationLatestReferenceYear(item);
  if (latestReferenceYear === null) {
    return false;
  }
  return targetYear - latestReferenceYear >= 2;
}

function getRecommendationLatestReferenceYear(item: RecommendationResult): number | null {
  const snapshot = item.snapshot_json;
  const referenceYears = Array.isArray(snapshot?.reference_years)
    ? snapshot.reference_years.filter((value): value is number => typeof value === "number")
    : [];
  if (!referenceYears.length) {
    return null;
  }
  return Math.max(...referenceYears);
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

function getRecommendationSnapshotNumber(item: RecommendationResult, key: string): number | null {
  const snapshot = item.snapshot_json;
  if (!snapshot || typeof snapshot !== "object") {
    return null;
  }
  return readRecommendationNumber(snapshot[key]);
}

function hasRecommendationMetricShift(currentValue: number | null, compareValue: number | null): boolean {
  return currentValue !== null && compareValue !== null && currentValue !== compareValue;
}

function readRecommendationNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function getRecommendationGeneratedAtDistance(value: string, targetTimestamp: number): number {
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp) || Number.isNaN(targetTimestamp)) {
    return Number.MAX_SAFE_INTEGER;
  }
  return Math.abs(timestamp - targetTimestamp);
}
