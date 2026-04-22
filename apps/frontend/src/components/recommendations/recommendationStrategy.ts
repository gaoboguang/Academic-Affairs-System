import type { RecommendationSettings, RecommendationStrategyPreset } from "./types";

export interface RecommendationSettingsSnapshot {
  safe_ratio_max: number;
  steady_ratio_max: number;
  rush_ratio_max: number;
  whitelist_college_ids: number[];
  blacklist_college_ids: number[];
}

function normalizeIdList(values: number[]): number[] {
  return Array.from(new Set(values)).sort((left, right) => left - right);
}

export function buildRecommendationSettingsSnapshot(
  value: RecommendationSettings | RecommendationStrategyPreset,
): RecommendationSettingsSnapshot {
  return {
    safe_ratio_max: Number(value.safe_ratio_max),
    steady_ratio_max: Number(value.steady_ratio_max),
    rush_ratio_max: Number(value.rush_ratio_max),
    whitelist_college_ids: normalizeIdList(value.whitelist_college_ids),
    blacklist_college_ids: normalizeIdList(value.blacklist_college_ids),
  };
}

export function hasRecommendationSettingsPendingChanges(
  current: RecommendationSettings,
  baseline: RecommendationSettingsSnapshot | null | undefined,
): boolean {
  if (!baseline) {
    return true;
  }
  return JSON.stringify(buildRecommendationSettingsSnapshot(current)) !== JSON.stringify(baseline);
}

export function differsFromStrategyPreset(
  current: RecommendationSettings,
  preset: RecommendationStrategyPreset | null | undefined,
): boolean {
  if (!preset) {
    return false;
  }
  return JSON.stringify(buildRecommendationSettingsSnapshot(current)) !== JSON.stringify(buildRecommendationSettingsSnapshot(preset));
}
