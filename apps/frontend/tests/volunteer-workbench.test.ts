import { describe, expect, it } from "vitest";

import {
  buildVolunteerCandidateExplanationNotes,
  buildVolunteerBoundaryInsightCards,
  buildVolunteerDraftBoundaryInsightCards,
  applyStudentCareerPreferenceToForm,
  appendVolunteerDraftItem,
  buildStudentCareerPreferencePayload,
  buildVolunteerDraftComparison,
  buildVolunteerDraftChecks,
  buildVolunteerCandidateLayeringCopy,
  buildVolunteerCandidateReferenceCopy,
  buildVolunteerCandidateRuleCopy,
  buildVolunteerEmploymentProfile,
  buildVolunteerDraftPayload,
  buildVolunteerRuleInsightCards,
  buildVolunteerRuleInsightCardsFromRules,
  buildVolunteerWorkbenchExplanation,
  buildVolunteerWorkbenchPayload,
  buildVolunteerDraftViewSections,
  createVolunteerWorkbenchForm,
  formatVolunteerDraftItemLabel,
  formatVolunteerDraftSummaryLabel,
  hasVolunteerCareerPreferenceContent,
  hasVolunteerWorkbenchPendingChanges,
  isSameVolunteerCareerPreference,
  moveVolunteerDraftItem,
  reorderVolunteerDraftItem,
  validateVolunteerDraftName,
  validateVolunteerWorkbenchForm,
} from "../src/components/recommendations/volunteerWorkbench";
import type {
  ProvinceVolunteerRule,
  VolunteerDraftItem,
  VolunteerWorkbenchCandidate,
  VolunteerWorkbenchFormState,
  VolunteerWorkbenchPreviewResponse,
} from "../src/components/recommendations/types";

function buildForm(overrides: Partial<VolunteerWorkbenchFormState> = {}): VolunteerWorkbenchFormState {
  return {
    student_id: 1,
    exam_id: 2,
    province: "广东",
    target_year: 2026,
    batch: "本科批",
    exam_mode: "物理类",
    candidate_type: "general",
    score_input_mode: "estimated_score_and_rank",
    score_range_min: undefined,
    score_range_max: undefined,
    rank_range_min: undefined,
    rank_range_max: undefined,
    reference_exam_name: " 2026届一模 ",
    use_historical_mapping: true,
    risk_preference: "balanced",
    target_regions_json: [" 深圳 ", "广东", "", "深圳"],
    school_level_tags_json: [" 双一流 ", "", "双一流"],
    major_keyword: " 软件工程 ",
    subject_combination: " 物理+化学 ",
    primary_direction_id: 11,
    secondary_direction_id: 12,
    alternative_direction_id: 13,
    priority_focuses_json: ["stability", "salary", "salary"],
    preferred_industries_json: [" 人工智能 ", "智能制造", "人工智能"],
    preferred_job_types_json: ["算法工程师", " 产品经理 ", "算法工程师"],
    target_employment_cities_json: ["深圳", " 广州 ", "深圳"],
    accepts_postgraduate: true,
    accepts_public_service: false,
    accepts_certificate: true,
    accepts_long_training: false,
    student_rank_override: 31000,
    comprehensive_score: 580,
    professional_score: 240,
    culture_score: 340,
    note: "  优先留在省内  ",
    ...overrides,
  };
}

function buildCandidate(planId: number, overrides: Partial<VolunteerWorkbenchCandidate> = {}): VolunteerWorkbenchCandidate {
  return {
    plan_id: planId,
    year: 2026,
    province: "广东",
    batch: "本科批",
    exam_mode: "物理类",
    college_id: 10 + planId,
    college_name: `院校 ${planId}`,
    college_code_snapshot: `C${planId.toString().padStart(3, "0")}`,
    major_id: 20 + planId,
    major_name: `专业 ${planId}`,
    major_group_code: `${planId}`,
    major_code_snapshot: `M${planId.toString().padStart(3, "0")}`,
    plan_count: 60,
    subject_requirement: "物理+化学",
    tuition_fee: "6500 元/年",
    schooling_years: "4年",
    training_location: "广州",
    student_type: "general",
    result_type: "steady",
    reference_rank: 28000,
    latest_admission_year: 2025,
    latest_min_rank: 28500,
    latest_min_score: 585,
    score_basis: "rank",
    reference_scope: "major",
    reference_years_json: [2025],
    reference_record_count: 1,
    reference_source_notes_json: ["近年数据"],
    ratio: 0.98,
    career_match_score: 52,
    career_match_strength: "medium",
    career_match_summary: "命中当前目标方向并覆盖目标岗位。",
    career_match_reasons_json: ["命中当前目标方向并覆盖目标岗位。"],
    matched_direction_names_json: ["方向匹配示例"],
    requires_postgraduate_path: false,
    requires_certificate_path: false,
    requires_long_training_path: false,
    matched_rule_exam_mode: "物理类",
    matched_rule_batch: "本科批",
    matched_rule_candidate_type: "general",
    matched_rule_is_baseline: false,
    match_tags_json: ["模式精确命中", "专业线参考", "按位次分层"],
    match_notes_json: ["当前按 广东 2026 物理类 本科批 规则解释。", "当前按“物理+化学”筛选，计划要求为“物理+化学”。"],
    reason_text: "测试候选计划",
    risk_flags_json: [],
    source_note: "测试",
    import_batch_name: "2026-广东-本科",
    major_direction: null,
    career_path: null,
    major_note: null,
    ...overrides,
  };
}

function buildRule(overrides: Partial<ProvinceVolunteerRule> = {}): ProvinceVolunteerRule {
  return {
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
    first_choice_subjects_json: ["物理", "历史"],
    reselect_subjects_json: ["化学", "生物", "政治", "地理"],
    score_rule_summary: "再选科目按等级赋分",
    parallel_rule_mode: "group_parallel",
    max_major_per_unit: 6,
    is_parallel: true,
    allow_adjustment: true,
    support_collect_round: true,
    special_rules_json: ["需核对选科要求"],
    note: "测试规则",
    is_active: true,
    created_at: "2026-04-09T10:00:00",
    updated_at: "2026-04-09T10:00:00",
    ...overrides,
  };
}

function buildPreview(overrides: Partial<VolunteerWorkbenchPreviewResponse> = {}): VolunteerWorkbenchPreviewResponse {
  return {
    student_id: 1,
    student_name: "张三",
    exam_id: 2,
    exam_name: "2026届高一4月月考",
    province: "广东",
    target_year: 2026,
    student_type: "general",
    candidate_type: "general",
    total_score: 580,
    snapshot_rank: 32000,
    effective_rank: 31000,
    score_input_mode: "estimated_score_and_rank",
    score_input_label: "预估分数 + 预估位次",
    score_confidence: "estimated",
    input_notes: ["当前按预估位次为主、预估分数为辅的模拟模式生成。", "参考考试：2026届一模。"],
    rule_alerts: [],
    applicable_rule_count: 1,
    applicable_rules: [buildRule()],
    candidate_count: 2,
    returned_candidate_count: 2,
    is_candidate_truncated: false,
    candidates: [buildCandidate(1), buildCandidate(2)],
    ...overrides,
  };
}

describe("volunteer workbench helpers", () => {
  it("validates required fields and builds normalized preview payload", () => {
    expect(validateVolunteerWorkbenchForm(buildForm({ student_id: undefined }))).toBe(
      "学生志愿工作台至少需要选择学生和参考考试",
    );
    expect(
      validateVolunteerWorkbenchForm(buildForm({ score_input_mode: "score_range", score_range_min: 580, score_range_max: undefined })),
    ).toBe("分数区间模式需要填写上下限");
    expect(buildVolunteerWorkbenchPayload(buildForm())).toEqual({
      student_id: 1,
      exam_id: 2,
      province: "广东",
      target_year: 2026,
      batch: "本科批",
      exam_mode: "物理类",
      candidate_type: "general",
      score_input_mode: "estimated_score_and_rank",
      score_range_min: undefined,
      score_range_max: undefined,
      rank_range_min: undefined,
      rank_range_max: undefined,
      reference_exam_name: "2026届一模",
      use_historical_mapping: true,
      risk_preference: "balanced",
      target_regions_json: ["深圳", "广东"],
      school_level_tags_json: ["双一流"],
      major_keyword: "软件工程",
      subject_combination: "物理+化学",
      primary_direction_id: 11,
      secondary_direction_id: 12,
      alternative_direction_id: 13,
      priority_focuses_json: ["stability", "salary"],
      preferred_industries_json: ["人工智能", "智能制造"],
      preferred_job_types_json: ["算法工程师", "产品经理"],
      target_employment_cities_json: ["深圳", "广州"],
      accepts_postgraduate: true,
      accepts_public_service: false,
      accepts_certificate: true,
      accepts_long_training: false,
      student_rank_override: 31000,
      comprehensive_score: 580,
      professional_score: 240,
      culture_score: 340,
      note: "优先留在省内",
    });
  });

  it("adds candidates into draft and enforces limit", () => {
    const first = appendVolunteerDraftItem([], buildCandidate(1), 2);
    expect(first.added).toBe(true);
    expect(first.items).toHaveLength(1);

    const duplicate = appendVolunteerDraftItem(first.items, buildCandidate(1), 2);
    expect(duplicate.added).toBe(false);
    expect(duplicate.reason).toBe("duplicate");

    const second = appendVolunteerDraftItem(first.items, buildCandidate(2), 2);
    const limited = appendVolunteerDraftItem(second.items, buildCandidate(3), 2);
    expect(limited.added).toBe(false);
    expect(limited.reason).toBe("limit");
  });

  it("detects pending workbench changes and formats draft labels", () => {
    expect(hasVolunteerWorkbenchPendingChanges(createVolunteerWorkbenchForm(), [], null)).toBe(false);
    expect(hasVolunteerWorkbenchPendingChanges(buildForm(), [], null)).toBe(true);
    expect(hasVolunteerWorkbenchPendingChanges(buildForm({ student_id: undefined, exam_id: undefined }), [
      { order: 1, plan_id: 1, candidate: buildCandidate(1) },
    ], null)).toBe(true);
    expect(formatVolunteerDraftItemLabel({ order: 1, plan_id: 1, candidate: buildCandidate(1) })).toBe("院校 1 / 专业 1");
    expect(
      formatVolunteerDraftSummaryLabel({
        name: "第一版",
        batch: "本科批",
        exam_mode: "物理类",
      }),
    ).toBe("第一版 / 本科批 / 物理类");
  });

  it("normalizes and compares career preference content", () => {
    const current = buildForm();
    const saved = {
      id: 1,
      student_id: 1,
      primary_direction_id: 11,
      secondary_direction_id: 12,
      alternative_direction_id: 13,
      priority_focuses_json: ["stability", "salary", "salary"] as const,
      preferred_industries_json: ["人工智能", "智能制造", "人工智能"],
      preferred_job_types_json: ["算法工程师", "产品经理", "算法工程师"],
      target_employment_cities_json: ["深圳", "广州", "深圳"],
      accepts_postgraduate: true,
      accepts_public_service: false,
      accepts_certificate: true,
      accepts_long_training: false,
      created_at: "2026-04-12T10:00:00",
      updated_at: "2026-04-12T10:00:00",
      is_active: true,
    };

    expect(hasVolunteerCareerPreferenceContent(current)).toBe(true);
    expect(
      isSameVolunteerCareerPreference(
        current,
        saved,
      ),
    ).toBe(true);
    expect(
      isSameVolunteerCareerPreference(
        current,
        {
          ...saved,
          preferred_job_types_json: ["算法工程师"],
        },
      ),
    ).toBe(false);
    expect(hasVolunteerCareerPreferenceContent(buildForm({
      primary_direction_id: undefined,
      secondary_direction_id: undefined,
      alternative_direction_id: undefined,
      priority_focuses_json: [],
      preferred_industries_json: [],
      preferred_job_types_json: [],
      target_employment_cities_json: [],
      accepts_postgraduate: false,
      accepts_public_service: false,
      accepts_certificate: false,
      accepts_long_training: false,
    }))).toBe(false);
  });

  it("validates draft name and builds draft save payload", () => {
    const items: VolunteerDraftItem[] = [{ order: 1, plan_id: 1, candidate: buildCandidate(1) }];
    expect(validateVolunteerDraftName("", items)).toBe("草稿名称不能为空");
    expect(validateVolunteerDraftName("第一版", [])).toBe("至少加入 1 条志愿后才能保存草稿");
    expect(buildVolunteerDraftPayload("  第一版  ", buildForm(), items, buildRule())).toEqual({
      name: "第一版",
      student_id: 1,
      exam_id: 2,
      province: "广东",
      target_year: 2026,
      batch: "本科批",
      exam_mode: "物理类",
      candidate_type: "general",
      score_input_mode: "estimated_score_and_rank",
      score_range_min: undefined,
      score_range_max: undefined,
      rank_range_min: undefined,
      rank_range_max: undefined,
      reference_exam_name: "2026届一模",
      use_historical_mapping: true,
      risk_preference: "balanced",
      target_regions_json: ["深圳", "广东"],
      school_level_tags_json: ["双一流"],
      major_keyword: "软件工程",
      subject_combination: "物理+化学",
      primary_direction_id: 11,
      secondary_direction_id: 12,
      alternative_direction_id: 13,
      priority_focuses_json: ["stability", "salary"],
      preferred_industries_json: ["人工智能", "智能制造"],
      preferred_job_types_json: ["算法工程师", "产品经理"],
      target_employment_cities_json: ["深圳", "广州"],
      accepts_postgraduate: true,
      accepts_public_service: false,
      accepts_certificate: true,
      accepts_long_training: false,
      student_rank_override: 31000,
      comprehensive_score: 580,
      professional_score: 240,
      culture_score: 340,
      note: "优先留在省内",
      selected_rule: buildRule(),
      items: [
        {
          order: 1,
          plan_id: 1,
          candidate: buildCandidate(1),
        },
      ],
    });
  });

  it("builds and applies student career preference payload", () => {
    const form = buildForm();
    expect(buildStudentCareerPreferencePayload(form)).toEqual({
      primary_direction_id: 11,
      secondary_direction_id: 12,
      alternative_direction_id: 13,
      priority_focuses_json: ["stability", "salary"],
      preferred_industries_json: ["人工智能", "智能制造"],
      preferred_job_types_json: ["算法工程师", "产品经理"],
      target_employment_cities_json: ["深圳", "广州"],
      accepts_postgraduate: true,
      accepts_public_service: false,
      accepts_certificate: true,
      accepts_long_training: false,
    });

    const target = buildForm({
      primary_direction_id: undefined,
      secondary_direction_id: undefined,
      alternative_direction_id: undefined,
      priority_focuses_json: [],
      preferred_industries_json: [],
      preferred_job_types_json: [],
      target_employment_cities_json: [],
      accepts_postgraduate: false,
      accepts_public_service: false,
      accepts_certificate: false,
      accepts_long_training: false,
    });
    applyStudentCareerPreferenceToForm(target, buildStudentCareerPreferencePayload(form));
    expect(target.primary_direction_id).toBe(11);
    expect(target.priority_focuses_json).toEqual(["stability", "salary"]);
    expect(target.preferred_industries_json).toEqual(["人工智能", "智能制造"]);
    expect(target.accepts_certificate).toBe(true);
  });

  it("reorders volunteer draft items", () => {
    const items: VolunteerDraftItem[] = [
      { order: 1, plan_id: 1, candidate: buildCandidate(1) },
      { order: 2, plan_id: 2, candidate: buildCandidate(2) },
      { order: 3, plan_id: 3, candidate: buildCandidate(3) },
    ];

    expect(moveVolunteerDraftItem(items, 3, "up").map((item) => item.plan_id)).toEqual([1, 3, 2]);
    expect(moveVolunteerDraftItem(items, 1, "up").map((item) => item.plan_id)).toEqual([1, 2, 3]);
    expect(moveVolunteerDraftItem(items, 1, "down").map((item) => item.plan_id)).toEqual([2, 1, 3]);
    expect(reorderVolunteerDraftItem(items, 3, 1).map((item) => item.plan_id)).toEqual([3, 1, 2]);
    expect(reorderVolunteerDraftItem(items, 1, 3).map((item) => item.plan_id)).toEqual([2, 3, 1]);
  });

  it("builds draft comparison summary for added removed reordered and regrouped items", () => {
    const compareItems: VolunteerDraftItem[] = [
      { order: 1, plan_id: 1, candidate: buildCandidate(1, { result_type: "challenge" }) },
      { order: 2, plan_id: 2, candidate: buildCandidate(2, { result_type: "steady" }) },
      { order: 3, plan_id: 4, candidate: buildCandidate(4, { result_type: "safe" }) },
    ];
    const currentItems: VolunteerDraftItem[] = [
      { order: 1, plan_id: 2, candidate: buildCandidate(2, { result_type: "safe" }) },
      { order: 2, plan_id: 1, candidate: buildCandidate(1, { result_type: "challenge" }) },
      { order: 3, plan_id: 3, candidate: buildCandidate(3, { result_type: "steady" }) },
    ];

    const summary = buildVolunteerDraftComparison(currentItems, compareItems);
    expect(summary.commonCount).toBe(2);
    expect(summary.added.map((item) => item.key)).toEqual(["3"]);
    expect(summary.removed.map((item) => item.key)).toEqual(["4"]);
    expect(summary.reordered.map((item) => item.key)).toEqual(["2", "1"]);
    expect(summary.regrouped.map((item) => item.key)).toEqual(["2"]);
    expect(summary.reordered[0]).toMatchObject({
      currentOrder: 1,
      compareOrder: 2,
    });
    expect(summary.regrouped[0]).toMatchObject({
      currentType: "safe",
      compareType: "steady",
    });
  });

  it("builds employment profile from major direction, career path and note", () => {
    const completeProfile = buildVolunteerEmploymentProfile(
      buildCandidate(1, {
        matched_direction_names_json: ["人工智能研发"],
        career_match_strength: "high",
        career_match_summary: "命中首选方向“人工智能研发”，并覆盖算法工程岗位。",
        requires_postgraduate_path: true,
        requires_certificate_path: true,
        major_direction: "智能制造与算法应用",
        career_path: "算法工程、机器视觉，读研后竞争力更强，部分岗位需资格证",
        major_note: "建议关注机器人工程方向",
      }),
    );
    expect(completeProfile).toEqual({
      targetDirection: "人工智能研发",
      matchStrength: "high",
      needsPostgraduate: "yes",
      needsCertificate: "yes",
      summary: "命中首选方向“人工智能研发”，并覆盖算法工程岗位。",
    });

    const fallbackProfile = buildVolunteerEmploymentProfile(
      buildCandidate(2, {
        matched_direction_names_json: [],
        career_match_strength: null,
        career_match_summary: null,
        requires_postgraduate_path: null,
        requires_certificate_path: null,
        major_direction: null,
        career_path: "数据分析、商业智能",
        major_note: null,
      }),
    );
    expect(fallbackProfile.targetDirection).toBe("数据分析");
    expect(fallbackProfile.matchStrength).toBe("transferable");
    expect(fallbackProfile.needsPostgraduate).toBe("not_explicit");
    expect(fallbackProfile.needsCertificate).toBe("not_explicit");

    const pendingProfile = buildVolunteerEmploymentProfile(buildCandidate(3));
    expect(pendingProfile.targetDirection).toBe("方向匹配示例");
    expect(pendingProfile.matchStrength).toBe("medium");
    expect(pendingProfile.needsPostgraduate).toBe("not_explicit");
    expect(pendingProfile.needsCertificate).toBe("not_explicit");
    expect(pendingProfile.summary).toContain("命中当前目标方向");
  });

  it("builds candidate layering summary for rank and score based paths", () => {
    expect(buildVolunteerCandidateLayeringCopy(buildCandidate(1))).toContain(
      "稳妥判断：按位次分层：当前位次与参考位次比值约为 0.9800，参考位次 28000。",
    );

    expect(
      buildVolunteerCandidateLayeringCopy(
        buildCandidate(2, {
          result_type: "safe",
          score_basis: "score",
          latest_min_score: 545,
          ratio: undefined,
          reference_rank: null,
          risk_flags_json: ["rank_missing", "sample_insufficient"],
        }),
      ),
    ).toContain("保底判断：按分数参考：最近最低分 545，当前结果按分数差额落层。当前缺少稳定位次口径，已改按分数参考。当前位次样本偏少，分层稳定性有限。");
  });

  it("builds candidate rule, reference and explanation copy for baseline and cross-province cases", () => {
    const candidate = buildCandidate(3, {
      matched_rule_is_baseline: true,
      matched_rule_candidate_type: "",
      match_tags_json: ["兼容模式命中", "院校线参考", "待核对选科"],
      reference_scope: "college",
      reference_years_json: [2025, 2024],
      reference_record_count: 2,
      subject_requirement: "物理+化学",
    });

    expect(buildVolunteerCandidateRuleCopy(candidate)).toBe("命中规则：广东 / 2026 / 物理类 / 本科批 · 系统基线");
    expect(buildVolunteerCandidateReferenceCopy(candidate)).toBe("院校线参考 · 2025 / 2024 年 · 2 条样本 · 来源：近年数据");
    expect(buildVolunteerCandidateExplanationNotes(candidate)).toEqual(
      expect.arrayContaining([
        "当前只命中系统基线，说明该省该年缺少更细规则，志愿上限、单位结构和征集志愿仍需按当年公告复核。",
        "当前请求模式与计划模式不完全一致，系统按“物理类”兼容口径预览，填报前需复核该省当年模式细则。",
        "当前专业缺少专业线，先回退到院校线参考；同校不同专业结果仍可能继续变化。",
        "录取参考只取 广东 2025 / 2024 年 样本，同校跨省结果不同属于正常口径差异。",
        "该计划要求“物理+化学”，最终填报前仍需核对选科限制。",
      ]),
    );
  });

  it("explains candidate-specific rule usage when a dedicated category rule is matched", () => {
    expect(
      buildVolunteerCandidateExplanationNotes(
        buildCandidate(4, {
          matched_rule_candidate_type: "general",
          match_tags_json: ["模式精确命中", "专业线参考"],
        }),
      ),
    ).toEqual(
      expect.arrayContaining([
        "当前命中普通类专用规则；同省同年其他类别可能适用不同志愿结构。",
        "录取参考只取 广东 2025 年 样本，同校跨省结果不同属于正常口径差异。",
      ]),
    );
  });

  it("explains when reference samples are older than the target year by two years or more", () => {
    expect(
      buildVolunteerCandidateExplanationNotes(
        buildCandidate(5, {
          year: 2026,
          reference_years_json: [2023, 2022],
          reference_record_count: 2,
        }),
      ),
    ).toEqual(
      expect.arrayContaining([
        "当前录取参考最近只到 2023 年，与 2026 目标年相差 3 年；若近一年数据尚未补齐，排序和解释会偏保守。",
      ]),
    );
  });

  it("explains when a special category falls back to general admission records", () => {
    expect(
      buildVolunteerCandidateExplanationNotes(
        buildCandidate(6, {
          student_type: "spring_exam",
          risk_flags_json: ["general_reference_fallback"],
        }),
      ),
    ).toEqual(
      expect.arrayContaining([
        "当前缺少该类别专门录取结果，先按普通类录取结果做方向性参考；这不是该类别专门录取把握，正式填报前仍需结合类别公告、批次规则和学校章程复核。",
      ]),
    );
  });

  it("builds boundary insight cards from rule alerts and candidate fallbacks", () => {
    const cards = buildVolunteerBoundaryInsightCards(
      buildPreview({
        rule_alerts: [
          {
            code: "baseline_rule_matched",
            level: "info",
            title: "当前命中系统基线规则",
            detail: "当前命中的省份规则为系统基线，志愿上限、单位类型和征集志愿规则仍需按当年公告复核。",
          },
          {
            code: "compatible_exam_mode_fallback",
            level: "info",
            title: "已回退到兼容模式规则",
            detail: "当前未配置“3+1+2”精确规则，先按兼容模式 物理类 预览。",
          },
        ],
        candidates: [
          buildCandidate(1, {
            matched_rule_is_baseline: true,
            match_tags_json: ["兼容模式命中", "院校线参考", "待核对选科"],
            reference_scope: "college",
            risk_flags_json: ["subject_requirement_check"],
          }),
          buildCandidate(2, {
            matched_rule_is_baseline: true,
            match_tags_json: ["专业线参考"],
          }),
        ],
      }),
    );

    expect(cards).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          key: "baseline",
          summary: "2 条候选仍按系统基线解释",
          tone: "info",
        }),
        expect.objectContaining({
          key: "compatible_mode",
          summary: "1 条候选走兼容模式命中",
          tone: "warning",
        }),
        expect.objectContaining({
          key: "college_fallback",
          summary: "1 条候选缺少专业线，只能先按院校线参考",
        }),
        expect.objectContaining({
          key: "subject_check",
          summary: "1 条候选仍需逐条核对选科限制",
        }),
      ]),
    );
  });

  it("builds stale-reference boundary cards when candidate samples are older than the target year", () => {
    const cards = buildVolunteerBoundaryInsightCards(
      buildPreview({
        candidates: [
          buildCandidate(1, {
            year: 2026,
            reference_years_json: [2023],
            reference_record_count: 1,
          }),
        ],
      }),
    );

    expect(cards).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          key: "stale_reference_years",
          title: "参考年份偏旧",
          summary: "1 条候选最近录取样本与目标年份相差 2 年及以上",
          tone: "warning",
        }),
      ]),
    );
  });

  it("builds boundary cards for candidate-specific rules and mixed reference years", () => {
    const cards = buildVolunteerBoundaryInsightCards(
      buildPreview({
        candidates: [
          buildCandidate(1, {
            matched_rule_candidate_type: "general",
            reference_years_json: [2025],
          }),
          buildCandidate(2, {
            matched_rule_candidate_type: "general",
            reference_years_json: [2024],
          }),
        ],
      }),
    );

    expect(cards).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          key: "candidate_specific_rule",
          title: "类别专用规则口径",
          summary: "2 条候选当前按普通类专用规则解释",
          tone: "info",
        }),
        expect.objectContaining({
          key: "mixed_reference_years",
          title: "跨年份参考样本",
          summary: "2 条候选最近录取样本分布在 2025 / 2024 年",
          tone: "info",
        }),
      ]),
    );
  });

  it("builds cross-province boundary card for mixed province candidates", () => {
    const cards = buildVolunteerBoundaryInsightCards(
      buildPreview({
        candidates: [
          buildCandidate(1, {
            province: "广东",
            reference_years_json: [2025],
          }),
          buildCandidate(2, {
            province: "北京",
            reference_years_json: [2025],
          }),
        ],
      }),
    );

    expect(cards).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          key: "cross_province",
          title: "跨省口径差异",
          summary: "2 个省份口径混合",
          tone: "info",
        }),
      ]),
    );
  });

  it("includes province-missing and general-rule fallback alerts in boundary cards", () => {
    const cards = buildVolunteerBoundaryInsightCards(
      buildPreview({
        candidate_count: 0,
        candidates: [],
        rule_alerts: [
          {
            code: "missing_rule_province",
            level: "warning",
            title: "缺少省份规则",
            detail: "当前未找到 海南 的省份规则；志愿上限与单位类型需先人工确认。",
          },
          {
            code: "fallback_general_candidate_rule",
            level: "info",
            title: "已回退到通用考生规则",
            detail: "当前未配置“艺术类”专用规则，先按通用考生规则预览。",
          },
        ],
      }),
    );

    expect(cards).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          key: "missing_rule_province",
          title: "缺少省份规则",
          summary: "当前省份规则尚未入库",
          tone: "warning",
        }),
        expect.objectContaining({
          key: "fallback_general_candidate_rule",
          title: "已回退到通用考生规则",
          summary: "当前先按通用类别规则预览",
          tone: "info",
        }),
      ]),
    );
  });

  it("uses candidate counts for preview missing-rule summaries when unmatched candidates exist", () => {
    const cards = buildVolunteerBoundaryInsightCards(
      buildPreview({
        candidates: [
          buildCandidate(1, {
            matched_rule_exam_mode: null,
            matched_rule_batch: null,
            matched_rule_candidate_type: null,
            matched_rule_is_baseline: false,
            match_tags_json: ["专业线参考"],
            match_notes_json: [],
          }),
        ],
        rule_alerts: [
          {
            code: "missing_rule_year",
            level: "warning",
            title: "缺少目标年份规则",
            detail: "当前未找到 广东 2025 年省份规则；该省现有 2026 年规则，志愿上限与单位类型需按当年公告人工复核。",
          },
        ],
      }),
    );

    expect(cards).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          key: "missing_rule_year",
          title: "缺少目标年份规则",
          summary: "1 条候选当前缺少目标年份规则支撑",
          tone: "warning",
        }),
      ]),
    );
  });

  it("uses candidate counts for preview general-rule summaries when preview falls back to general candidate rules", () => {
    const cards = buildVolunteerBoundaryInsightCards(
      buildPreview({
        candidates: [
          buildCandidate(1, {
            matched_rule_candidate_type: "",
          }),
        ],
        rule_alerts: [
          {
            code: "fallback_general_candidate_rule",
            level: "info",
            title: "已回退到通用考生规则",
            detail: "当前未配置“艺术类”专用规则，先按通用考生规则预览。",
          },
        ],
      }),
    );

    expect(cards).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          key: "fallback_general_candidate_rule",
          title: "已回退到通用考生规则",
          summary: "1 条候选当前按通用考生规则解释",
          tone: "info",
        }),
      ]),
    );
  });

  it("builds a stable boundary card when current preview has no major fallback alerts", () => {
    const cards = buildVolunteerBoundaryInsightCards(
      buildPreview({
        rule_alerts: [],
        candidates: [
          buildCandidate(1, {
            matched_rule_is_baseline: false,
            matched_rule_candidate_type: "",
            match_tags_json: ["模式精确命中", "专业线参考"],
            reference_scope: "major",
            risk_flags_json: [],
          }),
        ],
      }),
    );

    expect(cards).toEqual([
      expect.objectContaining({
        key: "stable",
        title: "当前结果边界较清晰",
        tone: "success",
      }),
    ]);
  });

  it("builds preview boundary card for general admission reference fallback", () => {
    const cards = buildVolunteerBoundaryInsightCards(
      buildPreview({
        candidates: [
          buildCandidate(1, {
            student_type: "spring_exam",
            risk_flags_json: ["general_reference_fallback"],
          }),
        ],
        rule_alerts: [
          {
            code: "fallback_general_reference_data",
            level: "info",
            title: "已回退到普通类录取参考",
            detail: "当前缺少“spring_exam”专门录取结果，已先回退参考普通类录取结果；正式填报前建议结合学校公告和类别专门批次再复核。",
          },
        ],
      }),
    );

    expect(cards).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          key: "general_reference_fallback",
          title: "已回退到普通类录取参考",
          summary: "1 条候选当前按普通类录取结果参考",
          tone: "info",
        }),
      ]),
    );
  });

  it("builds draft boundary insight cards for selected items", () => {
    const cards = buildVolunteerDraftBoundaryInsightCards(
      [
        {
          order: 1,
          plan_id: 1,
          candidate: buildCandidate(1, {
            matched_rule_is_baseline: true,
            match_tags_json: ["兼容模式命中", "院校线参考", "待核对选科"],
            reference_scope: "college",
            risk_flags_json: ["subject_requirement_check"],
          }),
        },
        {
          order: 2,
          plan_id: 2,
          candidate: buildCandidate(2, {
            matched_rule_is_baseline: false,
            matched_rule_candidate_type: "",
            match_tags_json: ["专业线参考"],
          }),
        },
      ],
      buildRule({ note: "系统基线初始化生成" }),
    );

    expect(cards).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ key: "baseline", summary: "1 条已选志愿仍按系统基线解释" }),
        expect.objectContaining({ key: "compatible_mode", summary: "1 条已选志愿按兼容模式预览命中" }),
        expect.objectContaining({ key: "general_candidate_rule", summary: "1 条已选志愿当前按通用考生规则解释" }),
        expect.objectContaining({ key: "college_fallback", summary: "1 条已选志愿缺少专业线，只能先按院校线参考" }),
        expect.objectContaining({ key: "subject_check", summary: "1 条已选志愿仍需逐条核对选科限制" }),
      ]),
    );
  });

  it("builds draft boundary cards for special-category fallback scopes", () => {
    const cards = buildVolunteerDraftBoundaryInsightCards(
      [
        {
          order: 1,
          plan_id: 1,
          candidate: buildCandidate(1, {
            student_type: "spring_exam",
            risk_flags_json: ["general_reference_fallback"],
          }),
        },
        {
          order: 2,
          plan_id: 2,
          candidate: buildCandidate(2, {
            student_type: "art",
            reference_scope: "score_line",
            risk_flags_json: ["score_line_reference_only"],
          }),
        },
        {
          order: 3,
          plan_id: 3,
          candidate: buildCandidate(3, {
            student_type: "comprehensive_evaluation",
            reference_scope: "plan_only",
            risk_flags_json: ["plan_only_reference"],
          }),
        },
      ],
      buildRule(),
      [
        {
          code: "fallback_general_reference_data",
          level: "info",
          title: "已回退到普通类录取参考",
          detail: "当前缺少“spring_exam”专门录取结果，已先回退参考普通类录取结果；正式填报前建议结合学校公告和类别专门批次再复核。",
        },
      ],
    );

    expect(cards).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          key: "general_reference_fallback",
          title: "已回退到普通类录取参考",
          summary: "1 条已选志愿当前按普通类录取结果参考",
        }),
        expect.objectContaining({
          key: "score_line_reference",
          title: "草稿内含省控线初筛",
          summary: "1 条已选志愿当前仅按省控线做资格参考",
        }),
        expect.objectContaining({
          key: "plan_only_reference",
          title: "草稿内含计划清单初筛",
          summary: "1 条已选志愿当前仅按当年招生计划做方向性初筛",
        }),
      ]),
    );
  });

  it("does not misclassify unmatched draft items as general candidate rules", () => {
    const cards = buildVolunteerDraftBoundaryInsightCards(
      [
        {
          order: 1,
          plan_id: 1,
          candidate: buildCandidate(1, {
            matched_rule_exam_mode: null,
            matched_rule_batch: null,
            matched_rule_candidate_type: null,
            matched_rule_is_baseline: false,
            match_tags_json: ["专业线参考"],
            match_notes_json: [],
          }),
        },
      ],
      null,
    );

    expect(cards).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          key: "missing_rule",
          title: "草稿内缺少明确规则",
          summary: "1 条已选志愿当前缺少明确省份规则支撑",
          tone: "warning",
        }),
      ]),
    );
    expect(cards.some((card) => card.key === "general_candidate_rule")).toBe(false);
  });

  it("uses specific rule alerts for unmatched draft items when available", () => {
    const cards = buildVolunteerDraftBoundaryInsightCards(
      [
        {
          order: 1,
          plan_id: 1,
          candidate: buildCandidate(1, {
            matched_rule_exam_mode: null,
            matched_rule_batch: null,
            matched_rule_candidate_type: null,
            matched_rule_is_baseline: false,
            match_tags_json: ["专业线参考"],
            match_notes_json: [],
          }),
        },
      ],
      null,
      [
        {
          code: "missing_rule_year",
          level: "warning",
          title: "缺少目标年份规则",
          detail: "当前未找到 广东 2025 年省份规则；该省现有 2026 年规则，志愿上限与单位类型需按当年公告人工复核。",
        },
      ],
    );

    expect(cards).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          key: "missing_rule_year",
          title: "缺少目标年份规则",
          summary: "1 条已选志愿当前缺少目标年份规则支撑",
          tone: "warning",
        }),
      ]),
    );
    expect(cards.some((card) => card.key === "missing_rule")).toBe(false);
  });

  it("builds stale-reference draft boundary cards for selected items", () => {
    const cards = buildVolunteerDraftBoundaryInsightCards(
      [
        {
          order: 1,
          plan_id: 1,
          candidate: buildCandidate(1, {
            year: 2026,
            reference_years_json: [2023],
            reference_record_count: 1,
          }),
        },
      ],
      buildRule(),
    );

    expect(cards).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          key: "stale_reference_years",
          title: "草稿内含偏旧年份样本",
          summary: "1 条已选志愿最近录取样本与目标年份相差 2 年及以上",
          tone: "warning",
        }),
      ]),
    );
  });

  it("builds draft boundary cards for candidate-specific rules and mixed reference years", () => {
    const cards = buildVolunteerDraftBoundaryInsightCards(
      [
        {
          order: 1,
          plan_id: 1,
          candidate: buildCandidate(1, {
            matched_rule_candidate_type: "general",
            reference_years_json: [2025],
          }),
        },
        {
          order: 2,
          plan_id: 2,
          candidate: buildCandidate(2, {
            matched_rule_candidate_type: "general",
            reference_years_json: [2024],
          }),
        },
      ],
      buildRule(),
    );

    expect(cards).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          key: "candidate_specific_rule",
          title: "草稿内含类别专用规则口径",
          summary: "2 条已选志愿当前按普通类专用规则解释",
          tone: "info",
        }),
        expect.objectContaining({
          key: "mixed_reference_years",
          title: "草稿内含跨年份参考样本",
          summary: "2 条已选志愿最近录取样本分布在 2025 / 2024 年",
          tone: "info",
        }),
      ]),
    );
  });

  it("builds cross-province boundary cards for draft items", () => {
    const cards = buildVolunteerDraftBoundaryInsightCards(
      [
        {
          order: 1,
          plan_id: 1,
          candidate: buildCandidate(1, {
            province: "广东",
            reference_years_json: [2025],
          }),
        },
        {
          order: 2,
          plan_id: 2,
          candidate: buildCandidate(2, {
            province: "四川",
            reference_years_json: [2025],
          }),
        },
      ],
      buildRule(),
    );

    expect(cards).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          key: "cross_province",
          title: "草稿内含跨省口径",
          summary: "2 个省份口径混合",
          tone: "info",
        }),
      ]),
    );
  });

  it("builds explanation summary for current filters and empty state", () => {
    const explanation = buildVolunteerWorkbenchExplanation(
      buildForm(),
      buildPreview({ candidate_count: 0, candidates: [] }),
      buildRule(),
    );

    expect(explanation.items).toEqual(
      expect.arrayContaining([
        { label: "省份", value: "广东" },
        { label: "批次", value: "本科批" },
        { label: "模式", value: "物理类" },
        { label: "类别", value: "普通类" },
        { label: "分数模式", value: "预估分 + 预估位次" },
        { label: "专业", value: "软件工程" },
        { label: "选科", value: "物理+化学" },
        { label: "参考考试", value: "2026届一模" },
        { label: "首选方向", value: "方向 11" },
        { label: "偏好重点", value: "稳定性 / 薪酬" },
        { label: "位次", value: "31000" },
      ]),
    );
    expect(explanation.notes.some((item) => item.includes("本次附加筛选包含 选科组合、目标地区、院校层级、专业关键词"))).toBe(true);
    expect(explanation.notes.some((item) => item.includes("当前分数输入模式为“预估分 + 预估位次”"))).toBe(true);
    expect(explanation.notes.some((item) => item.includes("历年映射估算提示"))).toBe(true);
    expect(explanation.notes.some((item) => item.includes("当前命中 广东 2026 物理类 本科批 规则"))).toBe(true);
    expect(explanation.notes.some((item) => item.includes("当前职业意向已记录到工作台和草稿中"))).toBe(true);
    expect(explanation.notes.some((item) => item.includes("当前按预估位次为主、预估分数为辅"))).toBe(true);
    expect(explanation.notes.some((item) => item.includes("建议优先放宽 选科组合、目标地区、院校层级、专业关键词"))).toBe(true);
  });

  it("builds structured rule insight cards for selected and compatible rules", () => {
    const cards = buildVolunteerRuleInsightCards(
      buildPreview({
        applicable_rule_count: 2,
        applicable_rules: [
          buildRule(),
          buildRule({
            id: 2,
            exam_mode: "历史类",
            volunteer_limit: 30,
            is_parallel: false,
            parallel_rule_mode: "ordered_sequential",
            max_major_per_unit: null,
            score_rule_summary: "按历史类顺序志愿说明执行",
            note: "兼容模式预览",
          }),
        ],
      }),
      buildRule(),
    );

    expect(cards).toHaveLength(2);
    expect(cards[0]).toMatchObject({
      title: "广东 2026 物理类 · 本科批",
      isSelected: true,
    });
    expect(cards[0].facts).toEqual(
      expect.arrayContaining([
        { label: "总分口径", value: "750 分" },
        { label: "志愿单位", value: "院校专业组" },
        { label: "平行方式", value: "院校专业组平行" },
        { label: "每单位专业数", value: "6 个" },
      ]),
    );
    expect(cards[0].notes).toEqual(
      expect.arrayContaining([
        "选科细则：首选 物理 / 历史；再选 化学 / 生物 / 政治 / 地理",
        "赋分摘要：再选科目按等级赋分",
        "附加要求：需核对选科要求",
      ]),
    );

    expect(cards[1]).toMatchObject({
      title: "广东 2026 历史类 · 本科批",
      isSelected: false,
    });
    expect(cards[1].facts).toEqual(
      expect.arrayContaining([
        { label: "平行方式", value: "顺序志愿" },
        { label: "每单位专业数", value: "未设" },
      ]),
    );
    expect(cards[1].notes).toEqual(
      expect.arrayContaining([
        "赋分摘要：按历史类顺序志愿说明执行",
        "备注：兼容模式预览",
      ]),
    );
  });

  it("builds structured rule insight cards directly from rule arrays", () => {
    const cards = buildVolunteerRuleInsightCardsFromRules(
      [
        buildRule(),
        buildRule({
          id: 2,
          exam_mode: "历史类",
          volunteer_limit: 30,
        }),
      ],
      buildRule(),
    );

    expect(cards).toHaveLength(2);
    expect(cards[0]).toMatchObject({ isSelected: true });
    expect(cards[1]).toMatchObject({ isSelected: false, title: "广东 2026 历史类 · 本科批" });
  });

  it("builds draft checks for remaining slots, safe coverage and risk flags", () => {
    const items: VolunteerDraftItem[] = [
      {
        order: 1,
        plan_id: 1,
        candidate: buildCandidate(1, { result_type: "steady", risk_flags_json: ["subject_requirement_check"] }),
      },
      {
        order: 2,
        plan_id: 2,
        candidate: buildCandidate(2, { result_type: "challenge", risk_flags_json: ["major_baseline_missing"] }),
      },
    ];

    const checks = buildVolunteerDraftChecks(items, buildRule(), 2);
    expect(checks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ level: "warning", title: "还有 2 个志愿位待补齐" }),
        expect.objectContaining({ level: "warning", title: "当前草稿暂未包含保底志愿" }),
        expect.objectContaining({ level: "warning", title: "1 条志愿仍需复核选科要求" }),
        expect.objectContaining({ level: "info", title: "1 条志愿按院校线做了专业参考" }),
      ]),
    );
  });

  it("builds risk-group view sections while preserving draft order inside each group", () => {
    const items: VolunteerDraftItem[] = [
      { order: 1, plan_id: 1, candidate: buildCandidate(1, { result_type: "challenge" }) },
      { order: 2, plan_id: 2, candidate: buildCandidate(2, { result_type: "safe" }) },
      { order: 3, plan_id: 3, candidate: buildCandidate(3, { result_type: "challenge" }) },
      { order: 4, plan_id: 4, candidate: buildCandidate(4, { result_type: "steady" }) },
    ];

    const sections = buildVolunteerDraftViewSections(items);
    expect(sections.map((item) => [item.label, item.items.length])).toEqual([
      ["冲刺志愿", 2],
      ["稳妥志愿", 1],
      ["保底志愿", 1],
    ]);
    expect(sections[0].items.map((item) => item.order)).toEqual([1, 3]);
    expect(sections[0].items.map((item) => item.plan_id)).toEqual([1, 3]);
    expect(sections[2].description).toContain("保留足够数量");
  });
});
