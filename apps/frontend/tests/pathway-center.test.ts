import { describe, expect, it } from "vitest";

import {
  buildPathwayCenterActions,
  buildPathwayCenterCards,
  buildPathwayProfileSummary,
  buildPublicationStatusHighlights,
  formatPathwayStudentOption,
  type GaokaoPathwayRead,
  type PathwayCenterStudentOption,
} from "../src/components/gaokao-pathways/pathwayCenter";
import type { AggregatedPathwayGap, StudentPathwayEvaluation, StudentPathwayProfile } from "../src/components/students/studentPathwayProfile";
import type { ShandongRecommendationDataHealth } from "../src/components/recommendations/types";

function buildPathway(overrides: Partial<GaokaoPathwayRead> = {}): GaokaoPathwayRead {
  return {
    id: 1,
    province: "山东",
    pathway_code: "summer_general_regular",
    pathway_name: "普通类常规批",
    pathway_group: "夏季高考",
    student_type: "general",
    exam_type: "summer_gaokao",
    batch_name: "普通类常规批",
    volunteer_mode: "专业（专业类）+学校",
    max_volunteer_count: 96,
    recommendation_depth: "full_rank_recommendation",
    status: "active",
    source_document_id: 11,
    summary: "可接入山东普通类冲稳保推荐。",
    risk_level: "medium",
    notes_json: { official_boundary: "最终以官方发布和高校章程为准" },
    is_active: true,
    ...overrides,
  };
}

function buildEvaluation(overrides: Partial<StudentPathwayEvaluation> = {}): StudentPathwayEvaluation {
  return {
    id: null,
    student_id: 3,
    pathway_id: 1,
    target_year: 2026,
    pathway_code: "summer_general_regular",
    pathway_name: "普通类常规批",
    pathway_group: "夏季高考",
    status: "suitable",
    status_label: "适合关注",
    score: 94,
    confidence_level: "medium",
    matched_rules_json: [
      {
        rule_code: "registration",
        rule_name: "已完成高考报名",
        rule_type: "hard_gate",
        severity: "error",
        result: "passed",
        manual_review_required: false,
      },
    ],
    failed_rules_json: [],
    warning_rules_json: [],
    missing_materials_json: [],
    recommendation_depth: "full_rank_recommendation",
    summary: "普通类常规批：适合关注。",
    next_actions_json: ["可进入山东普通类推荐工作台查看冲稳保候选。"],
    ...overrides,
  };
}

function buildProfile(overrides: Partial<StudentPathwayProfile> = {}): StudentPathwayProfile {
  return {
    id: 2,
    student_id: 3,
    student_name: "张三",
    province: "山东",
    candidate_type: "general",
    exam_type: "summer_gaokao",
    subject_combination: "物理,化学,生物",
    spring_exam_category: null,
    art_track: null,
    sports_track: null,
    has_gaokao_registration: true,
    is_fresh_graduate: true,
    is_vocational_student: false,
    is_social_candidate: false,
    has_high_school_equivalent: null,
    accept_private_college: null,
    accept_sino_foreign: null,
    accept_junior_college: true,
    accept_outside_province: null,
    accept_early_batch: true,
    accept_service_commitment: null,
    accept_interview_or_physical_test: null,
    career_preferences_json: {},
    region_preferences_json: {},
    family_constraints_json: {},
    known_body_limitations_json: {},
    materials_json: {},
    note: null,
    is_active: true,
    ...overrides,
  };
}

function buildDataHealth(overrides: Partial<ShandongRecommendationDataHealth> = {}): ShandongRecommendationDataHealth {
  return {
    generated_at: "2026-04-25T12:00:00",
    province: "山东",
    expected_years: [2023, 2024, 2025],
    coverage: [],
    publication_status: [
      {
        key: "summer_general_plan",
        label: "2026 普通类正式招生计划",
        category: "普通类",
        target_year: 2026,
        status: "pending_official_release",
        status_label: "待官方发布",
        record_count: 0,
        source_documents: [],
        action_label: "等待官方发布后导入",
        explanation: "不能把单招综评材料当作普通类正式计划。",
        notes: [],
        blocks_recommendation: true,
      },
      {
        key: "single_comprehensive_policy",
        label: "单招综评政策",
        category: "单招综评",
        target_year: 2026,
        status: "published",
        status_label: "已公开",
        record_count: 1,
        source_documents: [],
        action_label: "继续核验院校章程",
        explanation: "只用于路径初筛。",
        notes: [],
        blocks_recommendation: false,
      },
    ],
    gaps: ["2026 普通类正式计划未导入"],
    summary: "可验收但有数据警告",
    ...overrides,
  };
}

describe("pathway center helpers", () => {
  it("formats student options with class context", () => {
    const student: PathwayCenterStudentOption = {
      id: 3,
      student_no: "S003",
      name: "张三",
      current_grade_name: "高三",
      current_class_name: "1班",
      origin_province: "山东",
    };

    expect(formatPathwayStudentOption(student)).toBe("张三（S003 · 高三 · 1班）");
  });

  it("builds readable profile summary rows", () => {
    const summary = buildPathwayProfileSummary(buildProfile());

    expect(summary.find((item) => item.key === "candidate_type")?.value).toBe("普通类");
    expect(summary.find((item) => item.key === "gaokao_registration")?.value).toBe("已确认");
    expect(summary.find((item) => item.key === "subject_combination")?.filled).toBe(true);
  });

  it("marks ordinary regular pathway as recommendation entry and keeps screening paths bounded", () => {
    const cards = buildPathwayCenterCards([
      buildEvaluation(),
      buildEvaluation({
        pathway_id: 2,
        pathway_code: "vocational_comprehensive",
        pathway_name: "高职综合评价招生",
        pathway_group: "高职分类招生",
        status: "insufficient_data",
        status_label: "信息不足",
        recommendation_depth: "eligibility_screening",
        missing_materials_json: [
          {
            rule_code: "comprehensive_quality",
            material_key: "comprehensive_quality_evaluation",
            material_label: "综合素质评价材料",
            next_action: "补齐综合素质评价材料后重新评估该路径。",
          },
        ],
      }),
    ], [
      buildPathway(),
      buildPathway({
        id: 2,
        pathway_code: "vocational_comprehensive",
        pathway_name: "高职综合评价招生",
        pathway_group: "高职分类招生",
        student_type: "general",
        exam_type: "vocational_comprehensive",
        batch_name: "高职综合评价招生",
        volunteer_mode: "院校报名与素质测试",
        max_volunteer_count: null,
        recommendation_depth: "eligibility_screening",
        summary: "只做资格初筛。",
        risk_level: "high",
        notes_json: { boundary: "只做资格初筛和材料缺口提醒" },
      }),
    ]);

    expect(cards[0].canOpenRecommendation).toBe(true);
    expect(cards[1].canOpenRecommendation).toBe(false);
    expect(cards[1].depthLabel).toBe("资格初筛");
    expect(cards[1].missingMaterials).toContain("综合素质评价材料");
    expect(cards[1].keyRequirements).toContain("材料：综合素质评价、素质测试或面试安排");
    expect(cards[1].riskMessages).toContain("当前只做资格初筛和人工复核清单，不输出录取概率。");
    expect(cards[1].riskMessages).toContain("只做资格初筛和材料缺口提醒");
  });

  it("adds D6 screening hints for single recruitment and spring exam cards", () => {
    const cards = buildPathwayCenterCards([
      buildEvaluation({
        pathway_id: 7,
        pathway_code: "vocational_single_exam",
        pathway_name: "高职单独招生",
        pathway_group: "高职分类招生",
        status: "insufficient_data",
        status_label: "信息不足",
        recommendation_depth: "eligibility_screening",
        missing_materials_json: [
          {
            rule_code: "d6_single_chapter_plan_material",
            material_key: "single_exam_college_chapter_plan",
            material_label: "单招院校章程和分专业计划",
            next_action: "缺少目标院校单招章程或分专业计划时必须人工核验。",
          },
        ],
      }),
      buildEvaluation({
        pathway_id: 8,
        pathway_code: "spring_exam_undergrad",
        pathway_name: "春季高考本科批",
        pathway_group: "春季高考",
        status: "insufficient_data",
        status_label: "信息不足",
        recommendation_depth: "eligibility_screening",
        missing_materials_json: [
          {
            rule_code: "d6_spring_undergrad_score_line",
            material_key: "spring_exam_score_line",
            material_label: "春季高考类别分数线",
            next_action: "补充春季高考类别分数线后重新评估该路径。",
          },
        ],
      }),
    ], [
      buildPathway({
        id: 7,
        pathway_code: "vocational_single_exam",
        pathway_name: "高职单独招生",
        pathway_group: "高职分类招生",
        student_type: "vocational_or_social",
        exam_type: "vocational_single_exam",
        recommendation_depth: "eligibility_screening",
        notes_json: { boundary: "只做资格初筛，不等同于夏季普通类常规批" },
      }),
      buildPathway({
        id: 8,
        pathway_code: "spring_exam_undergrad",
        pathway_name: "春季高考本科批",
        pathway_group: "春季高考",
        student_type: "spring_exam",
        exam_type: "spring_gaokao",
        recommendation_depth: "eligibility_screening",
      }),
    ]);

    const singleCard = cards.find((item) => item.code === "vocational_single_exam");
    const springCard = cards.find((item) => item.code === "spring_exam_undergrad");

    expect(singleCard?.keyRequirements).toContain("身份：中职应届、社会人员等身份需在画像中确认");
    expect(singleCard?.missingMaterials).toContain("单招院校章程和分专业计划");
    expect(singleCard?.riskMessages[0]).toBe("当前只做资格初筛和人工复核清单，不输出录取概率。");
    expect(springCard?.keyRequirements).toContain("类别：只能在对应春考专业类别内初筛");
    expect(springCard?.missingMaterials).toContain("春季高考类别分数线");
  });

  it("builds next actions from recommendation entry, gaps, and data warnings", () => {
    const cards = buildPathwayCenterCards([buildEvaluation()], [buildPathway()]);
    const gaps: AggregatedPathwayGap[] = [
      {
        key: "subject_combination",
        label: "选科组合",
        count: 2,
        pathways: ["普通类常规批", "艺术类本科批"],
        nextAction: "补充选科组合后重新评估。",
      },
    ];
    const actions = buildPathwayCenterActions(cards, gaps, buildDataHealth());

    expect(actions.map((item) => item.key)).toEqual(["recommendation-entry", "gap-subject_combination", "data-health"]);
    expect(actions[2].detail).toContain("可验收但有数据警告");
  });

  it("prioritizes publication status highlights for 2026 data risks", () => {
    const highlights = buildPublicationStatusHighlights(buildDataHealth());

    expect(highlights[0].key).toBe("summer_general_plan");
    expect(highlights[1].key).toBe("single_comprehensive_policy");
  });
});
