import { describe, expect, it } from "vitest";

import {
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
});
