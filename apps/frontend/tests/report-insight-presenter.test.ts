import { describe, expect, it } from "vitest";

import { createEmptyReportInsightDataState } from "../src/components/reports/reportInsightLoader";
import {
  buildReportInsightCards,
  buildReportInsightGroups,
  getReportInsightDescription,
  shouldShowReportInsightSection,
} from "../src/components/reports/reportInsightPresenter";

describe("report insight presenter", () => {
  it("builds cards for analysis reports from the unified state", () => {
    const data = createEmptyReportInsightDataState();
    data.studentAnalysis = {
      student_name: "张三",
      exam_name: "高三一模",
      total_score: 612,
      total_score_delta: 12,
      subjects: [
        { subject_id: 1, subject_name: "语文", score: 121, grade_percentile: 88 },
        { subject_id: 2, subject_name: "数学", score: 96, grade_percentile: 41 },
      ],
    };

    const cards = buildReportInsightCards("student_analysis", data, null);

    expect(cards).toHaveLength(4);
    expect(cards[0]?.summary).toContain("张三");
    expect(cards[1]?.summary).toContain("提升 12 分");
  });

  it("builds recommendation cards with the current recommendation option", () => {
    const data = createEmptyReportInsightDataState();
    data.recommendationResults = [
      {
        id: 1,
        student_id: 8,
        exam_id: 2,
        scheme_id: 5,
        result_type: "steady",
        college_id: 11,
        score_basis: "rank",
        snapshot_json: {
          reference_years: [2023],
        },
        generated_at: "2026-04-12T10:00:00",
        is_active: true,
        risk_flags_json: ["sample_insufficient"],
      },
    ];

    data.recommendationCompareResults = [
      {
        id: 2,
        student_id: 8,
        exam_id: 2,
        scheme_id: 4,
        result_type: "challenge",
        college_id: 11,
        score_basis: "rank",
        snapshot_json: {
          reference_years: [2025],
        },
        generated_at: "2026-04-10T10:00:00",
        is_active: true,
        risk_flags_json: [],
      },
    ];

    const cards = buildReportInsightCards("recommendation_summary", data, {
      target_year: 2026,
      score_input_label: "高三一模换算位次",
      reference_exam_name: "高三一模",
      use_historical_mapping: true,
    }, {
      scheme_id: 4,
      scheme_name: "历史方案 A",
      generated_at: "2026-04-10T10:00:00",
      target_year: 2025,
    });

    expect(cards).toHaveLength(5);
    expect(cards[0]?.summary).toContain("高三一模换算位次");
    expect(cards[1]).toMatchObject({
      key: "history_comparison",
      summary: expect.stringContaining("历史方案 A"),
    });
    expect(cards[2]).toMatchObject({
      key: "history_reference_shift",
      summary: expect.stringContaining("最近录取样本年份发生变化"),
    });
    expect(cards[3]?.summary).toContain("样本不足");
    expect(cards[4]).toMatchObject({
      key: "stale_reference_years",
      summary: "1 条结果最近录取样本与目标年份相差 2 年及以上",
    });
  });

  it("builds volunteer draft boundary cards from the unified state", () => {
    const data = createEmptyReportInsightDataState();
    data.volunteerDraftDetail = {
      id: 7,
      name: "草稿 A",
      student_id: 1,
      exam_id: 2,
      province: "上海",
      target_year: 2026,
      candidate_type: "general",
      score_input_mode: "score",
      item_count: 1,
      created_at: "2026-04-12T10:00:00",
      updated_at: "2026-04-12T10:00:00",
      is_active: true,
      use_historical_mapping: false,
      risk_preference: "balanced",
      target_regions_json: [],
      school_level_tags_json: [],
      priority_focuses_json: [],
      preferred_industries_json: [],
      preferred_job_types_json: [],
      target_employment_cities_json: [],
      accepts_postgraduate: true,
      accepts_public_service: true,
      accepts_certificate: true,
      accepts_long_training: true,
      selected_rule: {
        id: 11,
        province: "上海",
        year: 2026,
        exam_mode: "3+3",
        batch: "本科批",
        candidate_type: "general",
        total_score: 660,
        volunteer_limit: 24,
        volunteer_unit_type: "院校专业组",
        subject_requirement_mode: "group_required_subjects",
        required_subjects_json: ["物理"],
        first_choice_subjects_json: [],
        reselect_subjects_json: ["化学"],
        is_parallel: true,
        allow_adjustment: true,
        support_collect_round: true,
        special_rules_json: [],
        is_active: true,
      } as any,
      applicable_rules: [
        {
          id: 11,
          province: "上海",
          year: 2026,
          exam_mode: "3+3",
          batch: "本科批",
          candidate_type: "general",
          total_score: 660,
          volunteer_limit: 24,
          volunteer_unit_type: "院校专业组",
          subject_requirement_mode: "group_required_subjects",
          required_subjects_json: ["物理"],
          first_choice_subjects_json: [],
          reselect_subjects_json: ["化学"],
          is_parallel: true,
          allow_adjustment: true,
          support_collect_round: true,
          special_rules_json: [],
          is_active: true,
        } as any,
      ],
      items: [
        {
          id: 1,
          order: 1,
          candidate: {
            plan_id: 21,
            year: 2026,
            province: "上海",
            college_id: 8,
            college_name: "某大学",
            plan_count: 1,
            major_name: "计算机科学与技术",
            result_type: "steady",
            batch: "本科批",
            exam_mode: "3+3",
            student_type: "general",
            score_basis: "rank",
            reference_years_json: [2025],
            reference_record_count: 1,
            reference_source_notes_json: [],
            career_match_reasons_json: [],
            matched_direction_names_json: [],
            matched_rule_is_baseline: false,
            matched_rule_candidate_type: null,
            match_tags_json: ["待核对选科"],
            match_notes_json: [],
            reason_text: "待核对选科要求",
            risk_flags_json: ["subject_requirement_check"],
            reference_scope: "major",
            major_id: 12,
          } as any,
          created_at: "2026-04-12T10:00:00",
          updated_at: "2026-04-12T10:00:00",
          is_active: true,
        },
      ],
    };

    const cards = buildReportInsightCards("volunteer_draft_summary", data, null);

    expect(cards.length).toBeGreaterThan(0);
    expect(cards.some((card) => card.title.includes("当前控制规则"))).toBe(true);
    expect(cards.some((card) => card.title.includes("选科") || card.detail.includes("选科"))).toBe(true);
  });

  it("surfaces missing-rule draft alerts in report insight cards", () => {
    const data = createEmptyReportInsightDataState();
    data.volunteerDraftDetail = {
      id: 8,
      name: "草稿 B",
      student_id: 1,
      exam_id: 2,
      province: "海南",
      target_year: 2026,
      candidate_type: "general",
      score_input_mode: "score",
      item_count: 1,
      created_at: "2026-04-12T10:00:00",
      updated_at: "2026-04-12T10:00:00",
      is_active: true,
      use_historical_mapping: false,
      risk_preference: "balanced",
      target_regions_json: [],
      school_level_tags_json: [],
      priority_focuses_json: [],
      preferred_industries_json: [],
      preferred_job_types_json: [],
      target_employment_cities_json: [],
      accepts_postgraduate: false,
      accepts_public_service: false,
      accepts_certificate: false,
      accepts_long_training: false,
      rule_alerts: [
        {
          code: "missing_rule_year",
          level: "warning",
          title: "缺少目标年份规则",
          detail: "当前未找到 海南 2026 年省份规则；该省现有 2025 年规则，志愿上限与单位类型需按当年公告人工复核。",
        },
      ],
      selected_rule: null,
      items: [
        {
          id: 1,
          order: 1,
          candidate: {
            plan_id: 21,
            year: 2026,
            province: "海南",
            college_id: 8,
            college_name: "某大学",
            plan_count: 1,
            major_name: "计算机科学与技术",
            result_type: "steady",
            batch: "本科批",
            exam_mode: "3+3",
            student_type: "general",
            score_basis: "rank",
            reference_years_json: [2025],
            reference_record_count: 1,
            reference_source_notes_json: [],
            career_match_reasons_json: [],
            matched_direction_names_json: [],
            matched_rule_exam_mode: null,
            matched_rule_batch: null,
            matched_rule_candidate_type: null,
            matched_rule_is_baseline: false,
            match_tags_json: ["专业线参考"],
            match_notes_json: [],
            reason_text: "当前缺少规则快照",
            risk_flags_json: [],
            reference_scope: "major",
            major_id: 12,
          } as any,
          created_at: "2026-04-12T10:00:00",
          updated_at: "2026-04-12T10:00:00",
          is_active: true,
        },
      ],
    };

    const cards = buildReportInsightCards("volunteer_draft_summary", data, null);

    expect(cards).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          key: "missing_rule_year",
          summary: "1 条已选志愿当前缺少目标年份规则支撑",
        }),
      ]),
    );
  });

  it("returns grouped report descriptions and section visibility", () => {
    const recommendationGroups = buildReportInsightGroups("recommendation_summary", [
      { key: "history_comparison", title: "历史方案差异", summary: "s", detail: "d", tone: "info" },
      { key: "sample_insufficient", title: "样本不足", summary: "s", detail: "d", tone: "warning" },
    ]);
    expect(recommendationGroups.map((group) => group.title)).toEqual(["历史对照摘要", "边界概览"]);

    const volunteerDraftGroups = buildReportInsightGroups("volunteer_draft_summary", [
      { key: "rule_scope", title: "当前控制规则", summary: "s", detail: "d", tone: "info" },
      { key: "subject_requirement_check", title: "待核对选科", summary: "s", detail: "d", tone: "warning" },
    ]);
    expect(volunteerDraftGroups.map((group) => group.title)).toEqual(["规则差异摘要", "风险概览"]);

    expect(buildReportInsightGroups("student_analysis", [])).toEqual([]);
    expect(getReportInsightDescription("student_analysis")).toContain("分析对象");
    expect(getReportInsightDescription("teacher_workload")).toContain("学期");
    expect(getReportInsightDescription("recommendation_summary")).toContain("推荐方案");
    expect(getReportInsightDescription("unknown_report")).toContain("导出前复核");

    expect(shouldShowReportInsightSection({ loading: false, error: "", loaded: false, cards: [] })).toBe(false);
    expect(shouldShowReportInsightSection({ loading: true, error: "", loaded: false, cards: [] })).toBe(true);
  });
});
