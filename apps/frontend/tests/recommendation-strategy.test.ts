import { describe, expect, it } from "vitest";

import {
  buildRecommendationSettingsSnapshot,
  differsFromStrategyPreset,
  hasRecommendationSettingsPendingChanges,
} from "../src/components/recommendations/recommendationStrategy";
import type { RecommendationSettings, RecommendationStrategyPreset } from "../src/components/recommendations/types";

function buildSettings(overrides: Partial<RecommendationSettings> = {}): RecommendationSettings {
  return {
    safe_ratio_max: 0.85,
    steady_ratio_max: 1,
    rush_ratio_max: 1.15,
    whitelist_college_ids: [3, 1, 3],
    blacklist_college_ids: [8, 5, 8],
    whitelist_colleges: [],
    blacklist_colleges: [],
    strategy_presets: [],
    ...overrides,
  };
}

function buildPreset(overrides: Partial<RecommendationStrategyPreset> = {}): RecommendationStrategyPreset {
  return {
    id: "preset-a",
    name: "模板 A",
    note: null,
    safe_ratio_max: 0.85,
    steady_ratio_max: 1,
    rush_ratio_max: 1.15,
    whitelist_college_ids: [1, 3],
    blacklist_college_ids: [5, 8],
    whitelist_colleges: [],
    blacklist_colleges: [],
    created_at: "2026-04-12T15:00:00",
    ...overrides,
  };
}

describe("recommendation strategy helpers", () => {
  it("normalizes strategy snapshots before comparison", () => {
    expect(buildRecommendationSettingsSnapshot(buildSettings())).toEqual({
      safe_ratio_max: 0.85,
      steady_ratio_max: 1,
      rush_ratio_max: 1.15,
      whitelist_college_ids: [1, 3],
      blacklist_college_ids: [5, 8],
    });
  });

  it("detects pending strategy changes against saved snapshot", () => {
    const baseline = buildRecommendationSettingsSnapshot(buildSettings());
    expect(hasRecommendationSettingsPendingChanges(buildSettings(), baseline)).toBe(false);
    expect(
      hasRecommendationSettingsPendingChanges(
        buildSettings({ rush_ratio_max: 1.2 }),
        baseline,
      ),
    ).toBe(true);
  });

  it("detects whether current settings differ from selected preset", () => {
    expect(differsFromStrategyPreset(buildSettings(), buildPreset())).toBe(false);
    expect(
      differsFromStrategyPreset(
        buildSettings({ blacklist_college_ids: [5, 9] }),
        buildPreset(),
      ),
    ).toBe(true);
  });
});
