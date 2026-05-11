import { describe, expect, it } from "vitest";

import {
  guideToWorkbenchPreview,
} from "../src/components/recommendations/useGaokaoVolunteerWorkspace";
import {
  buildVolunteerGuideOptionItems,
  buildVolunteerBatchOptionGroups,
  calculateVolunteerArtComprehensiveScore,
  buildVolunteerGuideActionItems,
  buildVolunteerGuideProgressSteps,
  buildVolunteerGuideReadiness,
  buildVolunteerGuideStepCards,
  groupVolunteerGuideCandidates,
  summarizeVolunteerReadinessItems,
} from "../src/components/recommendations/volunteerGuide";
import type { ProvinceVolunteerRule } from "../src/components/recommendations/types";
import type { VolunteerGuidePreviewResponse } from "../src/components/recommendations/types";

function buildGuide(overrides: Partial<VolunteerGuidePreviewResponse> = {}): VolunteerGuidePreviewResponse {
  return {
    student_id: 1,
    student_name: "张三",
    exam_id: 2,
    exam_name: "2026届高一4月月考",
    province: "广东",
    target_year: 2026,
    student_type: "general",
    candidate_type: "general",
    score_input_mode: "estimated_score_and_rank",
    input_notes: ["按预估位次生成。"],
    rule_alerts: [
      {
        code: "candidate_result_truncated",
        level: "warning",
        title: "智能筛选结果已截断",
        detail: "仅展示前 300 条。",
      },
    ],
    applicable_rule_count: 1,
    applicable_rules: [
      {
        id: 1,
        province: "广东",
        year: 2026,
        exam_mode: "物理类",
        batch: "本科批",
        candidate_type: "general",
        batch_order: 1,
        total_score: 750,
        volunteer_limit: 45,
        volunteer_unit_type: "院校专业组",
        subject_requirement_mode: "first_choice_reselect",
        required_subjects_json: [],
        first_choice_subjects_json: ["物理"],
        reselect_subjects_json: ["化学"],
        score_rule_summary: "平行志愿",
        parallel_rule_mode: "group_parallel",
        max_major_per_unit: 6,
        is_parallel: true,
        allow_adjustment: true,
        support_collect_round: true,
        special_rules_json: [],
        note: null,
        created_at: "2026-01-01T00:00:00",
        updated_at: "2026-01-01T00:00:00",
        is_active: true,
      },
    ],
    readiness: {
      status: "warning",
      blocking_count: 0,
      warning_count: 1,
      info_count: 0,
      items: [
        {
          code: "missing_subject_combination",
          level: "warning",
          title: "缺少选科组合",
          detail: "未填写选科组合时，选科要求只能提示人工核对。",
        },
      ],
    },
    source_preview: {
      candidate_count: 2,
      returned_candidate_count: 2,
      applicable_rule_count: 1,
      is_candidate_truncated: false,
      score_input_label: "预估分数 + 预估位次",
      score_confidence: "estimated",
      effective_rank: 31000,
      total_score: 580,
    },
    groups: {
      challenge: { key: "challenge", label: "冲刺", count: 0, candidates: [] },
      steady: {
        key: "steady",
        label: "稳妥",
        count: 1,
        candidates: [
          {
            candidate: {
              plan_id: 1,
              year: 2026,
              province: "广东",
              batch: "本科批",
              exam_mode: "物理类",
              college_id: 1,
              college_name: "岭南科技大学",
              college_code_snapshot: "10561",
              major_id: 1,
              major_name: "软件工程",
              major_group_code: "201",
              major_code_snapshot: "080902",
              major_direction: "企业软件与平台开发",
              career_path: "企业应用开发",
              major_note: null,
              plan_count: 120,
              subject_requirement: "物理+化学",
              tuition_fee: "6850 元/年",
              schooling_years: "4年",
              training_location: "广州校区",
              student_type: "general",
              result_type: "steady",
              reference_rank: 28000,
              latest_admission_year: 2025,
              latest_min_rank: 28000,
              latest_min_score: 585,
              score_basis: "rank",
              reference_scope: "major",
              reference_years_json: [2025],
              reference_record_count: 1,
              reference_source_notes_json: ["近年数据"],
              fallback_priority_score: null,
              fallback_priority_label: null,
              fallback_priority_notes_json: [],
              fallback_category_label: null,
              fallback_review_notes_json: [],
              ratio: 1.1071,
              career_match_score: 72,
              career_match_strength: "high",
              career_match_summary: "职业方向匹配。",
              career_match_reasons_json: ["职业方向匹配。"],
              matched_direction_names_json: ["企业软件开发"],
              requires_postgraduate_path: false,
              requires_certificate_path: true,
              requires_long_training_path: false,
              matched_rule_exam_mode: "物理类",
              matched_rule_batch: "本科批",
              matched_rule_candidate_type: "general",
              matched_rule_is_baseline: false,
              chapter_url: null,
              chapter_review_status: null,
              chapter_retrieval_status: null,
              chapter_campus_note: null,
              chapter_other_risk_note: null,
              chapter_language_requirement: null,
              chapter_single_subject_requirement: null,
              chapter_gender_requirement: null,
              chapter_height_requirement: null,
              chapter_vision_requirement: null,
              chapter_color_vision_requirement: null,
              chapter_physical_exam_requirement: null,
              match_tags_json: ["专业线参考", "已带选科条件", "按位次分层"],
              match_notes_json: ["当前按 广东 2026 物理类 本科批 规则解释。"],
              reason_text: "近1年参考数据，院校/专业参考位次约为 28000。",
              risk_flags_json: [],
              source_note: "招生计划简章",
              import_batch_name: "2026-广东-本科",
            },
            evidence: {
              strength: "major_history",
              strength_label: "专业历史线",
              summary: "专业历史线；参考 2025；最低位次 28000；计划 120 人；职业匹配 职业方向匹配。",
              rank_margin: -3000,
              rank_margin_label: "比参考位次靠后 3000 名",
              reference_years: [2025],
              reference_scope: "major",
              risk_flags: [],
              source_notes: ["近年数据"],
            },
          },
        ],
      },
      safe: { key: "safe", label: "保底", count: 1, candidates: [] },
      watch: { key: "watch", label: "仅关注", count: 0, candidates: [] },
    },
    next_actions: [
      {
        code: "add_to_draft",
        level: "info",
        title: "加入志愿草稿",
        detail: "可先把稳妥和保底候选加入志愿表，再逐条复核章程。",
      },
    ],
    ...overrides,
  };
}

describe("volunteer guide helpers", () => {
  it("builds concise progress steps for the redesigned guide", () => {
    const initial = buildVolunteerGuideProgressSteps(null, 0);
    expect(initial.map((item) => item.label)).toEqual(["考生条件", "意向偏好", "智能筛选", "志愿草稿"]);
    expect(initial[0].state).toBe("active");
    expect(initial[2].summary).toBe("生成后展示冲稳保结果");

    const blocked = buildVolunteerGuideProgressSteps(buildGuide({
      readiness: {
        status: "blocked",
        blocking_count: 1,
        warning_count: 0,
        info_count: 0,
        items: [
          {
            code: "missing_rule_batch",
            level: "blocking",
            title: "缺少目标批次规则",
            detail: "当前未找到 山东 2026 年“艺术本科批”批次规则。",
          },
        ],
      },
      source_preview: {
        ...buildGuide().source_preview,
        candidate_count: 0,
        returned_candidate_count: 0,
      },
    }), 0);
    expect(blocked[0].state).toBe("blocked");
    expect(blocked[2].state).toBe("blocked");

    const completed = buildVolunteerGuideProgressSteps(buildGuide(), 2);
    expect(completed[0].state).toBe("done");
    expect(completed[2].summary).toBe("2 条候选");
    expect(completed[3].state).toBe("done");
  });

  it("groups batch options by backend canonical rules and normalizes aliases", () => {
    const rules: ProvinceVolunteerRule[] = [
      buildGuide().applicable_rules[0],
      {
        ...buildGuide().applicable_rules[0],
        id: 2,
        batch: "艺术类本科批统考",
        exam_mode: "3+3",
      },
    ];

    const groups = buildVolunteerBatchOptionGroups({
      batchOptions: ["艺术本科批", "本科批", "专科批"],
      rules,
      currentBatch: "艺术本科批",
      guideOptions: {
        province: "山东",
        year: 2026,
        candidate_types: [{ value: "general", label: "普通类" }, { value: "art", label: "艺术类" }],
        art_tracks: [{ value: "music", label: "音乐类" }],
        batches: [{ value: "本科批", label: "本科批" }, { value: "艺术类本科批统考", label: "艺术类本科批统考" }],
        batch_aliases: { 艺术本科批: "艺术类本科批统考" },
        score_input_modes: [{ value: "estimated_score", label: "校内分数估算" }],
        art_score_formulas: {},
        maintained_rule_batches: ["本科批", "艺术类本科批统考"],
      },
    });

    expect(groups.available).toEqual(["本科批", "艺术类本科批统考"]);
    expect(groups.needsRule).toEqual(["专科批"]);
    expect(groups.currentUnmatched).toBeUndefined();
    expect(groups.suggestion).toBeUndefined();
  });

  it("uses backend option items and art score formulas before local fallbacks", () => {
    expect(buildVolunteerGuideOptionItems([{ value: "art", label: "艺术类" }], [{ value: "music", label: "音乐类" }])).toEqual([
      { value: "art", label: "艺术类" },
    ]);
    expect(calculateVolunteerArtComprehensiveScore(
      {
        province: "山东",
        year: 2026,
        candidate_types: [],
        art_tracks: [],
        batches: [],
        batch_aliases: {},
        score_input_modes: [],
        maintained_rule_batches: [],
        art_score_formulas: {
          music: {
            art_track: "music",
            label: "音乐类",
            culture_weight: 0.5,
            professional_weight: 0.5,
            professional_full_score: 300,
            formula_text: "文化成绩 * 50% + 专业成绩 * 750 / 300 * 50%",
            requires_manual_review: false,
          },
        },
      },
      "music",
      370,
      240,
    )).toBe(485);
  });

  it("summarizes readiness blockers into short actionable items", () => {
    const summary = summarizeVolunteerReadinessItems([
      {
        code: "missing_subject_combination",
        level: "warning",
        title: "缺少选科组合",
        detail: "未填写选科组合时，选科要求只能提示人工核对。",
      },
      {
        code: "missing_rule_batch",
        level: "blocking",
        title: "缺少目标批次规则",
        detail: "当前未找到 山东 2026 年“艺术本科批”批次规则；已维护批次：本科批 / 艺术类本科批统考。",
      },
      {
        code: "no_candidates",
        level: "blocking",
        title: "暂无可推荐候选",
        detail: "当前条件没有匹配到可加入志愿表的计划。",
      },
      {
        code: "missing_target_year_enrollment_plan",
        level: "blocking",
        title: "缺少目标年份招生计划",
        detail: "山东 2026 年正式招生计划尚未导入（艺术类“艺术类本科批统考”）；当前不能按目标年份生成可加入志愿表的正式候选。",
      },
      {
        code: "chapter_pending",
        level: "warning",
        title: "章程待核",
        detail: "部分学校章程未人工复核。",
      },
    ]);

    expect(summary).toHaveLength(3);
    expect(summary[0].title).toBe("先处理招生计划");
    expect(summary[0].detail).toContain("2026 年正式招生计划");
    expect(summary.map((item) => item.title)).toContain("先处理批次规则");
    expect(summary.map((item) => item.title)).toContain("补充选科组合");
  });

  it("keeps guide next actions short for the main screen", () => {
    const actions = buildVolunteerGuideActionItems(buildGuide({
      readiness: {
        status: "blocked",
        blocking_count: 1,
        warning_count: 0,
        info_count: 0,
        items: [
          {
            code: "missing_rule_batch",
            level: "blocking",
            title: "缺少目标批次规则",
            detail: "当前未找到 山东 2026 年“艺术本科批”批次规则。",
          },
        ],
      },
      next_actions: [
        {
          code: "fix_blocking_items",
          level: "warning",
          title: "先补齐阻断项",
          detail: "补齐位次、规则或候选数据后再生成志愿草稿。",
        },
        {
          code: "no_candidates",
          level: "warning",
          title: "暂无可加入候选",
          detail: "当前不能直接加入志愿表。",
        },
      ],
    }));

    expect(actions.map((item) => item.title)).toEqual(["先补齐阻断项", "暂无可加入候选"]);
  });

  it("builds four guide steps with readiness state", () => {
    const cards = buildVolunteerGuideStepCards(buildGuide());

    expect(cards.map((item) => item.title)).toEqual(["考生条件", "意向偏好", "智能筛选", "志愿草稿"]);
    expect(cards[0].status).toBe("warning");
    expect(cards[2].summary).toContain("2 条候选");
  });

  it("summarizes blocking readiness before generation", () => {
    const readiness = buildVolunteerGuideReadiness(null);

    expect(readiness.status).toBe("blocked");
    expect(readiness.items.map((item) => item.code)).toContain("not_generated");
  });

  it("keeps candidates grouped by rush steady safe and watch", () => {
    const groups = groupVolunteerGuideCandidates(buildGuide());

    expect(groups.map((item) => item.key)).toEqual(["challenge", "steady", "safe", "watch"]);
    expect(groups[1].candidates[0].evidence.strength_label).toBe("专业历史线");
  });

  it("keeps workbench rule and score context when adapting guide preview", () => {
    const preview = guideToWorkbenchPreview(buildGuide());

    expect(preview.student_type).toBe("general");
    expect(preview.candidate_type).toBe("general");
    expect(preview.score_input_mode).toBe("estimated_score_and_rank");
    expect(preview.applicable_rules[0].volunteer_limit).toBe(45);
    expect(preview.rule_alerts[0].code).toBe("candidate_result_truncated");
    expect(preview.input_notes).toContain("按预估位次生成。");
  });
});
