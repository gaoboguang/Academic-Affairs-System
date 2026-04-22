import { describe, expect, it } from "vitest";

import { buildGaokaoOverviewGapCards } from "../src/utils/gaokaoOverview";

describe("gaokaoOverview", () => {
  it("builds gap cards for empty app-side tables with raw data available", () => {
    const cards = buildGaokaoOverviewGapCards([
      {
        key: "enrollment_plan",
        label: "应用侧招生计划",
        record_total: 0,
        latest_updated_at: null,
        latest_batch_label: null,
        status: "partial",
        notes: ["独立 gaokao 只读表 gaokao_admission_plan 已有 12 条原始记录。"],
      },
      {
        key: "gaokao_college",
        label: "高校主档",
        record_total: 10,
        latest_updated_at: "2026-04-21 10:00:00",
        latest_batch_label: "DB RC1",
        status: "ready",
        notes: [],
      },
    ]);

    expect(cards).toHaveLength(1);
    expect(cards[0]?.key).toBe("enrollment_plan");
    expect(cards[0]?.summary).toBe("独立只读库已有原始数据，但应用模型还没接上当前链路。");
  });

  it("marks waiting app-side tables as handoff-dependent", () => {
    const cards = buildGaokaoOverviewGapCards([
      {
        key: "admission_record",
        label: "应用侧录取结果",
        record_total: 0,
        latest_updated_at: null,
        latest_batch_label: null,
        status: "waiting",
        notes: ["当前应用模型仍为 0 条，且本地 gaokao 只读库未暴露 gaokao_admission_result。"],
      },
    ]);

    expect(cards).toHaveLength(1);
    expect(cards[0]?.summary).toBe("应用模型为空，且本地只读库还没暴露对应原始表。");
  });
});
