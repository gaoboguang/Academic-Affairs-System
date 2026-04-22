import { describe, expect, it } from "vitest";

import {
  buildRecommendationSchemeComparison,
  findNearestRecommendationCompareScheme,
} from "../src/components/recommendations/recommendationComparison";
import type { RecommendationHistoryItem, RecommendationResult } from "../src/components/recommendations/types";

function buildResult(overrides: Partial<RecommendationResult> = {}): RecommendationResult {
  return {
    id: 1,
    student_id: 2,
    exam_id: 3,
    scheme_id: 1,
    result_type: "steady",
    college_id: 10,
    major_id: 20,
    college_name: "测试大学",
    major_name: "软件工程",
    score_basis: "rank",
    generated_at: "2026-04-12T15:00:00",
    is_active: true,
    risk_flags_json: [],
    snapshot_json: null,
    ...overrides,
  };
}

describe("recommendation comparison", () => {
  it("picks the nearest history scheme for the same student", () => {
    const current: RecommendationHistoryItem = {
      scheme_id: 9,
      scheme_name: "当前方案",
      student_id: 7,
      student_name: "张三",
      exam_id: 3,
      province: "山东",
      target_year: 2026,
      student_type: "general",
      score_input_mode: "estimated_score_and_rank",
      score_input_label: "一模换算位次",
      use_historical_mapping: true,
      generated_at: "2026-04-16T10:00:00",
      result_count: 24,
      challenge_count: 8,
      steady_count: 8,
      safe_count: 8,
    };

    const compare = findNearestRecommendationCompareScheme(
      [
        current,
        { ...current, scheme_id: 6, scheme_name: "更早方案", generated_at: "2026-04-12T10:00:00" },
        { ...current, scheme_id: 8, scheme_name: "最近方案", generated_at: "2026-04-15T18:00:00" },
        { ...current, scheme_id: 5, student_id: 8, student_name: "李四", scheme_name: "其他学生方案", generated_at: "2026-04-16T09:30:00" },
      ],
      current,
    );

    expect(compare?.scheme_id).toBe(8);
    expect(compare?.scheme_name).toBe("最近方案");
  });

  it("explains when reference-year changes also shift result groups", () => {
    const summary = buildRecommendationSchemeComparison(
      [
        buildResult({
          result_type: "steady",
          snapshot_json: {
            reference_years: [2023],
          },
        }),
      ],
      [
        buildResult({
          id: 2,
          result_type: "challenge",
          snapshot_json: {
            reference_years: [2025],
          },
        }),
      ],
      {
        currentTargetYear: 2026,
        compareTargetYear: 2025,
        currentProvince: "广东",
        compareProvince: "河北",
      },
    );

    expect(summary.referenceSummary).toMatchObject({
      changedCount: 1,
      staleShiftCount: 1,
      groupShiftCount: 1,
    });
    expect(summary.referenceSummary?.summary).toContain("同时伴随冲稳保分组变化");
    expect(summary.referenceSummary?.detail).toContain("当前方案目标年份 2026");
    expect(summary.referenceSummary?.detail).toContain("有 1 条同时出现了冲稳保分组调整");
    expect(summary.referenceSummary?.detail).toContain("当前方案按 广东 口径，对比方案按 河北 口径");
  });

  it("explains when reference-year changes have not shifted result groups yet", () => {
    const summary = buildRecommendationSchemeComparison(
      [
        buildResult({
          reference_rank: 28000,
          snapshot_json: {
            reference_years: [2023],
            latest_min_rank: 28500,
            latest_min_score: 585,
          },
        }),
      ],
      [
        buildResult({
          id: 2,
          reference_rank: 26000,
          snapshot_json: {
            reference_years: [2025],
            latest_min_rank: 26800,
            latest_min_score: 592,
          },
        }),
      ],
      {
        currentTargetYear: 2026,
        compareTargetYear: 2025,
        currentProvince: "广东",
        compareProvince: "广东",
      },
    );

    expect(summary.referenceSummary).toMatchObject({
      changedCount: 1,
      staleShiftCount: 1,
      groupShiftCount: 0,
    });
    expect(summary.referenceSummary?.summary).toContain("目前还未直接带来冲稳保分组变化");
    expect(summary.referenceSummary?.detail).toContain("两版方案都按 广东 口径，但目标年份不同");
    expect(summary.referenceSummary?.detail).toContain("1 条参考位次变化");
    expect(summary.referenceSummary?.detail).toContain("1 条最近最低位次变化");
    expect(summary.referenceSummary?.detail).toContain("1 条最近最低分变化");
  });

  it("returns no reference summary when shared items have stable reference years", () => {
    const summary = buildRecommendationSchemeComparison(
      [
        buildResult({
          snapshot_json: {
            reference_years: [2025],
          },
        }),
      ],
      [
        buildResult({
          id: 2,
          snapshot_json: {
            reference_years: [2025],
          },
        }),
      ],
      {
        currentTargetYear: 2026,
        compareTargetYear: 2026,
      },
    );

    expect(summary.referenceSummary).toBeNull();
  });

  it("explains stale-only shifts when the same samples become outdated under a new target year", () => {
    const summary = buildRecommendationSchemeComparison(
      [
        buildResult({
          snapshot_json: {
            reference_years: [2024],
          },
        }),
      ],
      [
        buildResult({
          id: 2,
          snapshot_json: {
            reference_years: [2024],
          },
        }),
      ],
      {
        currentTargetYear: 2027,
        compareTargetYear: 2025,
        currentProvince: "广东",
        compareProvince: "广东",
      },
    );

    expect(summary.referenceSummary).toMatchObject({
      affectedCount: 1,
      changedCount: 0,
      staleShiftCount: 1,
      staleOnlyCount: 1,
      groupShiftCount: 0,
    });
    expect(summary.referenceSummary?.summary).toContain("1 条结果的“年份偏旧”状态发生变化");
    expect(summary.referenceSummary?.detail).toContain("当前没有检测到明确的参考年份切换");
    expect(summary.referenceSummary?.detail).toContain("其中 1 条只是“年份偏旧”状态切换");
    expect(summary.referenceSummary?.detail).toContain("两版方案都按 广东 口径，但目标年份不同");
  });
});
