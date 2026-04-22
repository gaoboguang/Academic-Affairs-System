import { describe, expect, it } from "vitest";

import {
  buildRecommendationReportInsightCardGroups,
  buildRecommendationReportInsightCards,
  buildRecommendationReportInsightCompareOption,
  buildRecommendationReportInsightOption,
  resolveRecommendationReportInsightContext,
} from "../src/components/reports/reportInsightRecommendation";
import type { RecommendationResult } from "../src/components/recommendations/types";

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

describe("report insight recommendation", () => {
  it("builds recommendation insight options from scheme metadata", () => {
    expect(
      buildRecommendationReportInsightOption({
        province: "广东",
        target_year: 2026,
        score_input_label: "一模换算位次",
        reference_exam_name: "2026届一模",
        use_historical_mapping: true,
        score_confidence: "estimated",
      }),
    ).toEqual({
      province: "广东",
      target_year: 2026,
      score_input_label: "一模换算位次",
      reference_exam_name: "2026届一模",
      use_historical_mapping: true,
      score_confidence: "estimated",
    });

    expect(
      buildRecommendationReportInsightCompareOption({
        scheme_id: 9,
        student_id: 2,
        scheme_name: "历史方案 A",
        generated_at: "2026-04-10T10:00:00",
        province: "河北",
        target_year: 2025,
      }),
    ).toEqual({
      scheme_id: 9,
      scheme_name: "历史方案 A",
      generated_at: "2026-04-10T10:00:00",
      province: "河北",
      target_year: 2025,
    });
  });

  it("resolves current and compare recommendation insight context from history", () => {
    const history = [
      {
        scheme_id: 12,
        student_id: 2,
        scheme_name: "当前方案",
        generated_at: "2026-04-12T10:00:00",
        province: "广东",
        target_year: 2026,
        score_input_label: "一模换算位次",
      },
      {
        scheme_id: 9,
        student_id: 2,
        scheme_name: "历史方案 A",
        generated_at: "2026-04-10T10:00:00",
        province: "河北",
        target_year: 2025,
      },
    ];

    expect(resolveRecommendationReportInsightContext(history, history[0])).toEqual({
      currentOption: {
        province: "广东",
        target_year: 2026,
        score_input_label: "一模换算位次",
        reference_exam_name: undefined,
        use_historical_mapping: undefined,
        score_confidence: undefined,
      },
      compareScheme: history[1],
      compareOption: {
        scheme_id: 9,
        scheme_name: "历史方案 A",
        generated_at: "2026-04-10T10:00:00",
        province: "河北",
        target_year: 2025,
      },
    });
  });

  it("includes cross-province explanation when the current scheme province is preserved", () => {
    const cards = buildRecommendationReportInsightCards(
      [
        buildResult({
          result_type: "steady",
          snapshot_json: {
            reference_years: [2023],
          },
        }),
      ],
      buildRecommendationReportInsightOption({
        province: "广东",
        target_year: 2026,
        score_input_label: "一模换算位次",
      }),
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
        scheme_id: 9,
        scheme_name: "历史方案 A",
        generated_at: "2026-04-10T10:00:00",
        province: "河北",
        target_year: 2025,
      },
    );

    const historyComparison = cards.find((item) => item.key === "history_comparison");
    expect(historyComparison).toMatchObject({
      key: "history_comparison",
    });
    const crossProvinceComparison = cards.find((item) => item.key === "cross_province_comparison");
    expect(crossProvinceComparison).toMatchObject({
      key: "cross_province_comparison",
      detail: expect.stringContaining("当前方案按 广东 口径，对比方案按 河北 口径"),
    });
    const sameProvinceComparison = cards.find((item) => item.key === "same_province_year_comparison");
    expect(sameProvinceComparison).toBeUndefined();
  });

  it("includes explicit same-province year comparison when province is the same but target year differs", () => {
    const cards = buildRecommendationReportInsightCards(
      [
        buildResult({
          result_type: "challenge",
          snapshot_json: {
            reference_years: [2025],
          },
        }),
      ],
      buildRecommendationReportInsightOption({
        province: "广东",
        target_year: 2026,
        score_input_label: "一模换算位次",
      }),
      [
        buildResult({
          id: 2,
          result_type: "challenge",
          snapshot_json: {
            reference_years: [2024],
          },
        }),
      ],
      {
        scheme_id: 9,
        scheme_name: "历史方案 B",
        generated_at: "2026-04-10T10:00:00",
        province: "广东",
        target_year: 2025,
      },
    );

    expect(cards.find((item) => item.key === "same_province_year_comparison")).toMatchObject({
      key: "same_province_year_comparison",
      title: "同省跨年份差异",
    });
  });

  it("splits recommendation cards into history, boundary and risk groups", () => {
    const cards = buildRecommendationReportInsightCards(
      [
        buildResult({
          risk_flags_json: ["sample_insufficient", "certificate_path_mismatch"],
          snapshot_json: {
            reference_years: [2023],
          },
        }),
      ],
      buildRecommendationReportInsightOption({
        province: "广东",
        target_year: 2026,
        score_input_label: "一模换算位次",
      }),
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
        scheme_id: 9,
        scheme_name: "历史方案 C",
        generated_at: "2026-04-10T10:00:00",
        province: "河北",
        target_year: 2025,
      },
    );

    expect(buildRecommendationReportInsightCardGroups(cards)).toEqual([
      {
        key: "history",
        title: "历史对照摘要",
        cards: expect.arrayContaining([
          expect.objectContaining({ key: "history_comparison" }),
          expect.objectContaining({ key: "cross_province_comparison" }),
          expect.objectContaining({ key: "history_reference_shift" }),
        ]),
      },
      {
        key: "boundary",
        title: "边界概览",
        cards: expect.arrayContaining([
          expect.objectContaining({ key: "simulation" }),
          expect.objectContaining({ key: "sample_insufficient" }),
          expect.objectContaining({ key: "stale_reference_years" }),
        ]),
      },
      {
        key: "risk",
        title: "风险概览",
        cards: expect.arrayContaining([
          expect.objectContaining({ key: "path_mismatch" }),
        ]),
      },
    ]);
  });
});
