import { describe, expect, it } from "vitest";

import {
  buildShandongCoverageRows,
  buildShandongRecommendationExportPayload,
  buildShandongRecommendationPrintPayload,
  buildShandongProjectionPayload,
  buildShandongRecommendationPayload,
  buildShandongResultGroups,
  createShandongRecommendationForm,
  formatShandongRiskFlag,
  getShandongHistoricalRankRows,
  getShandongPlanChangeSummary,
  validateShandongRecommendationForm,
} from "../src/components/recommendations/shandongRecommendationWorkbench";
import type {
  ShandongRecommendationDataHealth,
  ShandongRushStableSafeCandidate,
  ShandongRushStableSafeRecommendationResponse,
} from "../src/components/recommendations/types";

function buildCandidate(overrides: Partial<ShandongRushStableSafeCandidate> = {}): ShandongRushStableSafeCandidate {
  return {
    college_id: 1,
    college_name: "山东示例大学",
    college_code_snapshot: "A001",
    major_id: 2,
    major_name: "计算机类",
    major_code_snapshot: "0809",
    bucket: "stable",
    bucket_label: "稳",
    rank_margin: 1200,
    rank_margin_ratio: 0.08,
    score_summary: {
      reference_rank: 15000,
      latest_min_score: 612,
      latest_min_rank: 15200,
    },
    years_used: [2025, 2024, 2023],
    historical_summary: {
      weighted_reference_rank: 15000,
      rank_rows: [
        { year: 2025, min_rank: 15200, min_score: 612, plan_count: 12, source_note: "2025 投档表" },
        { year: 2024, min_rank: 15100, min_score: 609, plan_count: 10, source_note: "2024 投档表" },
      ],
      plan_change: {
        target_year_plan_count: 15,
        latest_historical_plan_count: 12,
        plan_change_factor: 1.25,
      },
    },
    plan_count: 15,
    subject_requirement: "物理 化学",
    data_confidence: "high",
    risk_flags: ["three_year_data_incomplete"],
    explanation_text: "按近三年山东普通类投档数据计算，归为稳。",
    source_document_ids: [101, 102],
    ...overrides,
  };
}

function buildResult(): ShandongRushStableSafeRecommendationResponse {
  return {
    student_id: 1,
    student_name: "张三",
    province: "山东",
    target_year: 2026,
    student_type: "general",
    source_mode: "manual_rank",
    predicted_score: 620,
    predicted_rank: 13800,
    rank_range_low: 13800,
    rank_range_high: 13800,
    rank_projection_basis: "manual_rank",
    risk_preference: "balanced",
    data_years: [2025, 2024, 2023],
    input_notes: ["当前按手动填写的全省位次作为主排序依据。"],
    summary: {
      rush_count: 1,
      stable_count: 1,
      safe_count: 0,
      watch_count: 0,
      excluded_subject_mismatch_count: 2,
    },
    rush: [buildCandidate({ bucket: "rush", bucket_label: "冲" })],
    stable: [buildCandidate()],
    safe: [],
    watch: [],
  };
}

function buildDataHealth(): ShandongRecommendationDataHealth {
  return {
    generated_at: "2026-04-25T10:00:00",
    province: "山东",
    expected_years: [2023, 2024, 2025, 2026],
    summary: "可验收但有数据警告",
    gaps: ["2026 普通类正式招生计划待官方发布"],
    coverage: [
      {
        key: "admission_record",
        label: "普通类投档/录取结果",
        status: "ok",
        total: 60000,
        years: [2023, 2024, 2025],
        missing_years: [],
        readiness: "ready",
        readiness_label: "最近三年可用",
        risk_level: "normal",
        explanation: "最近三年普通类投档结果已导入。",
        notes: [],
        student_types: [],
        batch_distribution: [],
        year_breakdown: [],
      },
      {
        key: "enrollment_plan",
        label: "招生计划",
        status: "gap",
        total: 1200,
        years: [2024, 2025],
        missing_years: [2023],
        readiness: "partial",
        readiness_label: "部分可用",
        risk_level: "warning",
        explanation: "2023 计划仍待补。",
        notes: [],
        student_types: [],
        batch_distribution: [],
        year_breakdown: [],
      },
    ],
    publication_status: [
      {
        key: "2026_plan",
        label: "2026 普通类正式招生计划",
        category: "普通类",
        target_year: 2026,
        status: "pending_official_release",
        status_label: "待官方发布",
        record_count: 0,
        source_documents: [],
        action_label: "等待山东省教育招生考试院发布后导入",
        explanation: "不能用单招/综评计划替代普通类计划。",
        notes: [],
        blocks_recommendation: true,
      },
    ],
  };
}

describe("shandong recommendation workbench helpers", () => {
  it("validates required inputs and builds exam projection payload", () => {
    const form = createShandongRecommendationForm();
    expect(validateShandongRecommendationForm(form)).toBe("请先选择学生，系统会用学生档案核对是否为山东普通类。");

    form.student_id = 1;
    form.selected_subjects_json = ["物理", "化学", "生物"];
    expect(validateShandongRecommendationForm(form)).toBe("选择学生与考试估算时，需要同时选择一次参考考试。");

    form.exam_id = 2;
    expect(validateShandongRecommendationForm(form)).toBeNull();
    expect(buildShandongProjectionPayload(form)).toEqual({
      student_id: 1,
      target_year: 2026,
      province: "山东",
      source_mode: "exam_projection",
      selected_exam_ids: [2],
      note: "山东普通类推荐工作台自动生成",
    });
  });

  it("builds preview payloads for manual score and projection modes", () => {
    const form = createShandongRecommendationForm();
    Object.assign(form, {
      student_id: 1,
      source_mode: "manual_score",
      manual_score: 621,
      selected_subjects_json: ["物理", "化学", "物理"],
      target_regions_json: ["济南", "青岛", "济南"],
      school_level_tags_json: ["本科", ""],
      major_keyword: " 计算机 ",
    });

    expect(buildShandongRecommendationPayload(form)).toMatchObject({
      student_id: 1,
      province: "山东",
      student_type: "general",
      source_mode: "manual_score",
      manual_score: 621,
      subject_combination: "物理 化学",
      target_regions_json: ["济南", "青岛"],
      school_level_tags_json: ["本科"],
      major_keyword: "计算机",
    });

    form.source_mode = "exam_projection";
    expect(buildShandongRecommendationPayload(form, 9).source_mode).toBe("projection");
    expect(buildShandongRecommendationPayload(form, 9).projection_id).toBe(9);
  });

  it("groups result buckets and exposes expanded candidate facts", () => {
    const groups = buildShandongResultGroups(buildResult());
    expect(groups.map((item) => `${item.label}:${item.items.length}`)).toEqual(["冲:1", "稳:1", "保:0", "仅关注:0"]);

    const rows = getShandongHistoricalRankRows(buildCandidate());
    expect(rows[0]).toMatchObject({ year: 2025, min_rank: 15200, min_score: 612 });
    expect(getShandongPlanChangeSummary(buildCandidate())).toContain("目标年份计划 15 人");
    expect(formatShandongRiskFlag("plan_missing")).toBe("目标年计划暂缺");
  });

  it("builds report export and print payloads without exposing raw risk codes", () => {
    const result = buildResult();
    const exportPayload = buildShandongRecommendationExportPayload(result);
    expect(exportPayload.report_name).toBe("张三 2026 山东普通类冲稳保推荐报告");
    expect(exportPayload.result.summary.rush_count).toBe(1);

    const printPayload = buildShandongRecommendationPrintPayload(result, null, buildDataHealth());
    expect(printPayload.result.predicted_rank).toBe(13800);
    expect(printPayload.data_health_gaps).toEqual(["2026 普通类正式招生计划待官方发布"]);
    expect(formatShandongRiskFlag(result.stable[0].risk_flags[0])).toBe("近三年样本不完整");
  });

  it("summarizes 2023-2025 data coverage for the quality board", () => {
    const rows = buildShandongCoverageRows(buildDataHealth());
    expect(rows[0]).toMatchObject({
      label: "普通类投档/录取结果",
      coveredYears: [2023, 2024, 2025],
      missingYears: [],
    });
    expect(rows[1]).toMatchObject({
      label: "招生计划",
      coveredYears: [2024, 2025],
      missingYears: [2023],
      statusLabel: "部分可用",
    });
  });
});
