import { describe, expect, it } from "vitest";

import {
  buildVolunteerDraftReportInsightCardGroups,
  buildVolunteerDraftReportInsightCards,
} from "../src/components/reports/reportInsightVolunteerDraft";

describe("report insight volunteer draft", () => {
  it("groups live-rule, boundary and risk cards for volunteer draft summary", () => {
    const groups = buildVolunteerDraftReportInsightCardGroups([
      {
        key: "rule_selected",
        title: "上海 2026 3+3 · 本科批（当前控制规则）",
        summary: "当前控制规则",
        detail: "测试规则",
        tone: "success",
      },
      {
        key: "missing_rule_year",
        title: "缺少目标年份规则",
        summary: "1 条已选志愿当前缺少目标年份规则支撑",
        detail: "测试缺口",
        tone: "warning",
      },
      {
        key: "cross_province",
        title: "草稿内含跨省口径",
        summary: "2 个省份口径混合",
        detail: "测试跨省说明",
        tone: "info",
      },
      {
        key: "general_reference_fallback",
        title: "草稿内含普通类录取参考回退",
        summary: "1 条已选志愿当前按普通类录取结果参考",
        detail: "测试普通类回退说明",
        tone: "info",
      },
      {
        key: "subject_check",
        title: "草稿内仍有选科待核对项",
        summary: "1 条已选志愿仍需逐条核对选科限制",
        detail: "测试选科风险",
        tone: "warning",
      },
    ]);

    expect(groups).toEqual([
      {
        key: "live_rule",
        title: "规则差异摘要",
        cards: expect.arrayContaining([
          expect.objectContaining({ key: "rule_selected" }),
          expect.objectContaining({ key: "missing_rule_year" }),
        ]),
      },
      {
        key: "boundary",
        title: "边界概览",
        cards: expect.arrayContaining([
          expect.objectContaining({ key: "cross_province" }),
          expect.objectContaining({ key: "general_reference_fallback" }),
        ]),
      },
      {
        key: "risk",
        title: "风险概览",
        cards: [expect.objectContaining({ key: "subject_check" })],
      },
    ]);
  });

  it("builds shared volunteer draft report cards from rules and boundary insights", () => {
    const cards = buildVolunteerDraftReportInsightCards({
      rules: [
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
          reselect_subjects_json: [],
          is_parallel: true,
          allow_adjustment: true,
          support_collect_round: true,
          special_rules_json: [],
          is_active: true,
        } as any,
      ],
      selectedRule: {
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
        reselect_subjects_json: [],
        is_parallel: true,
        allow_adjustment: true,
        support_collect_round: true,
        special_rules_json: [],
        is_active: true,
      } as any,
      draftItems: [
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
        } as any,
      ],
      ruleAlerts: [],
    });

    expect(cards).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          key: expect.stringMatching(/^rule_/),
          title: expect.stringContaining("当前控制规则"),
        }),
        expect.objectContaining({
          key: "subject_check",
          summary: "1 条已选志愿仍需逐条核对选科限制",
        }),
      ]),
    );
  });
});
