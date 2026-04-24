import { describe, expect, it } from "vitest";

import {
  buildRecommendationBoundaryNotes,
  buildRecommendationFallbackPriorityCopy,
  buildRecommendationReferenceCopy,
  buildRecommendationStaleReferenceNote,
  getRecommendationReferenceYearGap,
} from "../src/components/recommendations/recommendationCopy";

describe("recommendation copy", () => {
  it("builds stale reference notes when reference years lag behind target year", () => {
    expect(
      buildRecommendationStaleReferenceNote(
        {
          reference_years: [2023, 2022],
        },
        2026,
      ),
    ).toBe("当前录取参考最近只到 2023 年，与 2026 目标年相差 3 年；若近一年数据尚未补齐，排序和解释会偏保守。");
  });

  it("returns null when reference years are recent enough", () => {
    expect(
      buildRecommendationStaleReferenceNote(
        {
          reference_years: [2025],
        },
        2026,
      ),
    ).toBeNull();
    expect(getRecommendationReferenceYearGap({ reference_years: [2025] }, 2026)).toBe(1);
  });

  it("builds score line and plan only reference copy", () => {
    expect(
      buildRecommendationReferenceCopy({
        reference_scope: "score_line",
        reference_years_json: [2025],
        reference_record_count: 0,
        reference_source_notes_json: ["艺术类本科文化控制线"],
      } as never),
    ).toBe("省控线参考 · 2025 年 · 省级控制线口径 · 来源：艺术类本科文化控制线");

    expect(
      buildRecommendationReferenceCopy({
        reference_scope: "plan_only",
        reference_years_json: [2026],
        reference_record_count: 0,
        reference_source_notes_json: ["当年招生计划清单"],
      } as never),
    ).toBe("计划清单初筛 · 2026 年 · 当年计划口径 · 来源：当年招生计划清单");
  });

  it("builds boundary notes for plan only reference", () => {
    expect(
      buildRecommendationBoundaryNotes(
        {
          reference_scope: "plan_only",
          major_id: 1,
          snapshot_json: { reference_years: [2026] },
          fallback_priority_score: 42,
          fallback_priority_label: "重点比较",
          fallback_priority_notes_json: ["计划数 20，有一定容量"],
          fallback_category_label: "综评工科方向",
          fallback_review_notes_json: ["核对综合评价报名条件"],
        } as never,
        2026,
      ),
    ).toEqual([
      "当前结果只按当年招生计划清单做方向性初筛，不能直接作为冲稳保或录取把握判断。",
      "初筛优先级：重点比较（42）：细分类别：综评工科方向；计划数 20，有一定容量；核对清单：核对综合评价报名条件",
    ]);
  });

  it("builds fallback priority copy", () => {
    expect(
      buildRecommendationFallbackPriorityCopy({
        fallback_priority_score: 58,
        fallback_priority_label: "优先核看",
        fallback_priority_notes_json: ["有省级控制线", "计划数 30"],
        fallback_category_label: "艺术音乐类",
        fallback_review_notes_json: ["核对艺术统考类别"],
      } as never),
    ).toBe("初筛优先级：优先核看（58）：细分类别：艺术音乐类；有省级控制线；计划数 30；核对清单：核对艺术统考类别");
  });
});
