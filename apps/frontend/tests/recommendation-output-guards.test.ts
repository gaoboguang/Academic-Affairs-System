import { describe, expect, it } from "vitest";

import {
  buildRecommendationSchemeOutputWarningMessage,
  buildVolunteerDraftOutputWarningMessage,
} from "../src/components/recommendations/recommendationOutputGuards";
import type {
  RecommendationHistoryItem,
  RecommendationResult,
  VolunteerDraftCheckItem,
} from "../src/components/recommendations/types";

function buildScheme(overrides: Partial<RecommendationHistoryItem> = {}): RecommendationHistoryItem {
  return {
    scheme_id: 1,
    scheme_name: "方案 A",
    student_id: 2,
    student_name: "张三",
    exam_id: 3,
    province: "广东",
    target_year: 2026,
    student_type: "general",
    score_input_mode: "estimated_score_and_rank",
    score_input_label: "预估分 + 预估位次",
    score_confidence: "estimated",
    reference_exam_name: "2026届一模",
    use_historical_mapping: true,
    generated_at: "2026-04-12T15:00:00",
    result_count: 2,
    challenge_count: 1,
    steady_count: 1,
    safe_count: 0,
    ...overrides,
  };
}

function buildResult(overrides: Partial<RecommendationResult> = {}): RecommendationResult {
  return {
    id: 1,
    student_id: 2,
    exam_id: 3,
    scheme_id: 1,
    result_type: "steady",
    college_id: 10,
    score_basis: "rank",
    generated_at: "2026-04-12T15:00:00",
    is_active: true,
    risk_flags_json: [],
    ...overrides,
  };
}

describe("recommendation output guards", () => {
  it("builds draft output warnings from warning-level checks", () => {
    const checks: VolunteerDraftCheckItem[] = [
      { level: "success", title: "已包含保底志愿", detail: "ok" },
      { level: "warning", title: "还有 3 个志愿位待补齐", detail: "补齐" },
      { level: "warning", title: "2 条志愿仍需复核选科要求", detail: "复核" },
    ];

    expect(buildVolunteerDraftOutputWarningMessage(checks)).toContain("还有 3 个志愿位待补齐");
    expect(buildVolunteerDraftOutputWarningMessage([{ level: "info", title: "提示", detail: "x" }])).toBeNull();
  });

  it("builds scheme output warnings from simulation mode and risk flags", () => {
    const message = buildRecommendationSchemeOutputWarningMessage(buildScheme(), [
      buildResult({ risk_flags_json: ["manual_formula_check"] }),
      buildResult({ id: 2, risk_flags_json: ["sample_insufficient", "rank_missing"] }),
    ]);

    expect(message).toContain("当前推荐结果基于“预估分 + 预估位次”生成");
    expect(message).toContain("需人工核对招生章程");
    expect(message).toContain("样本不足");
    expect(message).toContain("已改按分数参考");
  });

  it("includes history comparison warnings when comparison context is available", () => {
    const currentScheme = buildScheme();
    const compareScheme = buildScheme({
      scheme_id: 9,
      scheme_name: "历史方案 A",
      generated_at: "2026-04-10T10:00:00",
      province: "河北",
      target_year: 2025,
    });

    const message = buildRecommendationSchemeOutputWarningMessage(
      currentScheme,
      [
        buildResult({
          result_type: "steady",
          snapshot_json: {
            reference_years: [2023],
          },
        }),
      ],
      {
        history: [currentScheme, compareScheme],
        compareResults: [
          buildResult({
            id: 2,
            scheme_id: 9,
            result_type: "challenge",
            snapshot_json: {
              reference_years: [2025],
            },
          }),
        ],
      },
    );

    expect(message).toContain("相对“历史方案 A”");
    expect(message).toContain("跨省口径影响");
    expect(message).toContain("最近录取样本年份发生变化");
  });

  it("returns null when scheme output has no extra warnings", () => {
    expect(
      buildRecommendationSchemeOutputWarningMessage(
        buildScheme({ score_confidence: "actual", use_historical_mapping: false }),
        [buildResult()],
      ),
    ).toBeNull();
  });
});
