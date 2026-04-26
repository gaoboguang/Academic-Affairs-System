import { describe, expect, it } from "vitest";

import {
  buildCoverageMatrixRows,
  buildDataCompletionPrintPayload,
  buildDataCompletionResultCards,
  type DataCompletionHealthInput,
} from "../src/components/gaokao-data/dataCompletionReport";

function buildDataHealth(): DataCompletionHealthInput {
  return {
    db_path: "/tmp/app.db",
    exists: true,
    generated_at: "2026-04-26 15:30:00",
    schema_version: "20260426_0019",
    province: "山东",
    expected_years: [2020, 2021, 2022, 2023, 2024, 2025, 2026],
    summary: "核心表缺失 0 个，空表 0 个，需关注表 2 个，P0 缺口 4 条",
    delivery_assessment: {
      status: "warning",
      label: "可验收但有数据警告",
      summary: "P0 安全底座可继续验收，但数据可用性仍需补齐和人工复核。",
      pass_items: [],
      warning_items: [],
      blocking_items: [],
    },
    coverage: [
      {
        key: "score_rank_segment",
        label: "一分一段",
        status: "ok",
        total: 22388,
        years: [2020, 2021, 2022, 2023, 2024, 2025],
        missing_years: [2026],
        readiness: "ready",
        readiness_label: "已补齐",
        risk_level: "normal",
        explanation: "用于分数换位次。",
        notes: ["2026 年数据按官方发布时间继续等待。"],
        student_types: [],
        batch_distribution: [],
        year_breakdown: [2020, 2021, 2022, 2023, 2024, 2025].map((year) => ({
          year,
          total: year === 2020 ? 3769 : 3600,
          student_types: [],
          batches: [],
          status: "ok",
        })),
      },
      {
        key: "gaokao_score_line",
        label: "raw 省控线/批次线",
        status: "ok",
        total: 74,
        years: [2020, 2021, 2022, 2023, 2024, 2025],
        missing_years: [2026],
        readiness: "ready",
        readiness_label: "已补齐",
        risk_level: "normal",
        explanation: "用于资格线初筛。",
        notes: [],
        student_types: [],
        batch_distribution: [],
        year_breakdown: [2020, 2021, 2022, 2023, 2024, 2025].map((year) => ({
          year,
          total: year === 2022 ? 11 : 10,
          student_types: [],
          batches: [],
          status: "ok",
        })),
      },
      {
        key: "enrollment_plan",
        label: "应用侧招生计划",
        status: "ok",
        total: 6338,
        years: [2024, 2025],
        missing_years: [2020, 2021, 2022, 2023, 2026],
        readiness: "partial",
        readiness_label: "部分补齐",
        risk_level: "warning",
        explanation: "用于候选池。",
        notes: ["招生计划说明可报方向和容量，不等同于录取把握。"],
        student_types: [],
        batch_distribution: [],
        year_breakdown: [
          { year: 2024, total: 592, student_types: [], batches: [], status: "ok" },
          { year: 2025, total: 5601, student_types: [], batches: [], status: "ok" },
        ],
      },
      {
        key: "gaokao_policy_reference",
        label: "raw 政策参考",
        status: "gap",
        total: 4,
        years: [2026],
        missing_years: [2020, 2021, 2022, 2023, 2024, 2025],
        readiness: "partial",
        readiness_label: "部分补齐",
        risk_level: "warning",
        explanation: "用于政策说明。",
        notes: [],
        student_types: [],
        batch_distribution: [],
        year_breakdown: [{ year: 2026, total: 4, student_types: [], batches: [], status: "ok" }],
      },
      {
        key: "gaokao_college_chapter_rule",
        label: "raw 招生章程限制链",
        status: "gap",
        total: 2052,
        years: [2025],
        missing_years: [2020, 2021, 2022, 2023, 2024, 2026],
        readiness: "partial",
        readiness_label: "部分补齐",
        risk_level: "warning",
        explanation: "用于章程风险。",
        notes: [],
        student_types: [],
        batch_distribution: [],
        year_breakdown: [{ year: 2025, total: 2052, student_types: [], batches: [], status: "ok" }],
      },
    ],
    publication_status: [
      {
        key: "general_admission_plan",
        label: "普通类正式招生计划",
        category: "普通类夏季高考",
        target_year: 2026,
        status: "pending_official_release",
        status_label: "待官方发布",
        record_count: 0,
        action_label: "待山东省教育招生考试院发布后再导入",
        explanation: "不能用单招/综评计划替代。",
        notes: [],
        blocks_recommendation: false,
      },
      {
        key: "score_rank_segment",
        label: "一分一段表",
        category: "成绩换算",
        target_year: 2026,
        status: "pending_official_release",
        status_label: "待官方发布",
        record_count: 0,
        action_label: "待 2026 成绩公布后导入",
        explanation: "未发布时只能估算。",
        notes: [],
        blocks_recommendation: false,
      },
    ],
    audit_summary: [
      {
        key: "gaokao_college_chapter_rule",
        label: "raw 招生章程限制链",
        status: "gap",
        created: 0,
        updated: 2052,
        duplicates: 0,
        conflicts: 0,
        pending_review: 1748,
        notes: ["待人工复核 1748 条"],
      },
    ],
    gaps: [
      "山东招生计划 2024 年数量偏少：592 条，需继续核验完整性",
      "政策参考数量偏少：4 条，交付前需补山东官方政策和填报规则",
    ],
  };
}

describe("data completion report helpers", () => {
  it("builds teacher-readable result cards from data health", () => {
    const cards = buildDataCompletionResultCards(buildDataHealth());

    expect(cards[0]).toMatchObject({
      key: "history-covered",
      statusLabel: "已补齐",
      tone: "success",
    });
    expect(cards.map((item) => item.statusLabel)).toContain("官方未发布");
    expect(cards.find((item) => item.key === "chapter-review")?.detail).toContain("1748");
  });

  it("builds a 2020-2026 matrix without hiding pending 2026 data", () => {
    const rows = buildCoverageMatrixRows(buildDataHealth());
    const rankRow = rows.find((item) => item.key === "score_rank_segment");
    const planRow = rows.find((item) => item.key === "enrollment_plan");

    expect(rankRow?.cells.map((item) => item.label)).toEqual([
      "已补齐",
      "已补齐",
      "已补齐",
      "已补齐",
      "已补齐",
      "已补齐",
      "待官方发布",
    ]);
    expect(planRow?.cells.find((item) => item.year === 2024)?.label).toBe("部分补齐");
    expect(planRow?.cells.find((item) => item.year === 2026)?.label).toBe("待官方发布");
  });

  it("builds print payload with matrix, gaps and delivery judgement", () => {
    const payload = buildDataCompletionPrintPayload(buildDataHealth());

    expect(payload.report_name).toBe("山东高考数据覆盖报告");
    expect(payload.delivery_label).toBe("可验收但有数据警告");
    expect(payload.coverage_matrix.length).toBeGreaterThan(0);
    expect(payload.gaps).toContain("政策参考数量偏少：4 条，交付前需补山东官方政策和填报规则");
  });
});
