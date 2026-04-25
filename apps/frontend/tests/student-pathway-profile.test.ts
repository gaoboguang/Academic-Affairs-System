import { describe, expect, it } from "vitest";

import {
  applyPathwayProfileToForm,
  buildPathwayMaterialChecklist,
  buildPathwayProfileReadiness,
  buildStudentPathwayProfilePayload,
  collectStudentPathwayGaps,
  createStudentPathwayProfileForm,
  formatPathwayMaterialKey,
  pathwayStatusTagType,
  summarizePathwayStatuses,
  type StudentPathwayEvaluation,
  type StudentPathwayProfile,
} from "../src/components/students/studentPathwayProfile";

function buildProfile(overrides: Partial<StudentPathwayProfile> = {}): StudentPathwayProfile {
  return {
    id: 1,
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
    accept_outside_province: false,
    accept_early_batch: true,
    accept_service_commitment: null,
    accept_interview_or_physical_test: null,
    career_preferences_json: {},
    region_preferences_json: {},
    family_constraints_json: {},
    known_body_limitations_json: { note: "色觉需逐校核对" },
    materials_json: { gaokao_registration: true, comprehensive_quality_evaluation: true },
    note: "报名材料在班主任处",
    is_active: true,
    ...overrides,
  };
}

function buildEvaluation(overrides: Partial<StudentPathwayEvaluation> = {}): StudentPathwayEvaluation {
  return {
    id: null,
    student_id: 3,
    pathway_id: 10,
    target_year: 2026,
    pathway_code: "summer_general_regular",
    pathway_name: "普通类常规批",
    pathway_group: "夏季高考",
    status: "insufficient_data",
    status_label: "信息不足",
    score: 82,
    confidence_level: "low",
    matched_rules_json: [],
    failed_rules_json: [],
    warning_rules_json: [],
    missing_materials_json: [
      {
        rule_code: "d2_general_subject_combination",
        material_key: "subject_combination",
        material_label: "选科组合",
        gap_type: "profile_field",
        next_action: "补充选科组合后重新评估该路径。",
      },
    ],
    recommendation_depth: "full_rank_recommendation",
    summary: "普通类常规批：信息不足。",
    next_actions_json: ["补充学生选科组合后，才能按专业选科要求过滤候选。"],
    ...overrides,
  };
}

describe("student pathway profile helpers", () => {
  it("applies API data to the editable form and preserves material booleans", () => {
    const form = createStudentPathwayProfileForm();
    applyPathwayProfileToForm(form, buildProfile());

    expect(form.candidate_type).toBe("general");
    expect(form.has_gaokao_registration).toBe(true);
    expect(form.materials_json.gaokao_registration).toBe(true);
    expect(form.materials_json.art_exam_score).toBe(false);
  });

  it("normalizes empty strings before saving", () => {
    const form = createStudentPathwayProfileForm();
    form.subject_combination = "  ";
    form.note = "  已电话确认  ";
    form.materials_json.gaokao_registration = true;

    const payload = buildStudentPathwayProfilePayload(form);

    expect(payload.subject_combination).toBeNull();
    expect(payload.note).toBe("已电话确认");
    expect(payload.materials_json.gaokao_registration).toBe(true);
  });

  it("builds readable readiness and material checklist rows", () => {
    const form = createStudentPathwayProfileForm();
    form.subject_combination = "物理,化学,生物";
    form.has_gaokao_registration = false;
    form.materials_json.comprehensive_quality_evaluation = true;

    const readiness = buildPathwayProfileReadiness(form);
    const materials = buildPathwayMaterialChecklist(form.materials_json);

    expect(readiness.find((item) => item.key === "subject_combination")?.ready).toBe(true);
    expect(readiness.find((item) => item.key === "has_gaokao_registration")?.value).toBe("不符合 / 不接受");
    expect(materials.find((item) => item.key === "comprehensive_quality_evaluation")?.checked).toBe(true);
    expect(materials.find((item) => item.key === "single_exam_college_chapter_plan")?.label).toBe("单招院校章程和分专业计划");
    expect(materials.find((item) => item.key === "spring_exam_score_line")?.help).toContain("本科或专科批分数线");
    expect(materials.find((item) => item.key === "art_chapter_restrictions")?.help).toContain("身高");
    expect(materials.find((item) => item.key === "sports_single_exam_arrangement")?.label).toBe("体育单招文化考试和体育专项考试安排");
    expect(materials.find((item) => item.key === "high_level_college_chapter")?.help).toContain("文化成绩");
  });

  it("aggregates missing materials across pathway evaluations", () => {
    const gaps = collectStudentPathwayGaps([
      buildEvaluation(),
      buildEvaluation({
        pathway_id: 11,
        pathway_name: "高职综评",
        missing_materials_json: [
          {
            rule_code: "d2_comprehensive_quality_record",
            material_key: "comprehensive_quality_evaluation",
            material_label: "综合素质评价材料",
            next_action: "补充综合素质评价材料后重新评估该路径。",
          },
        ],
      }),
    ]);

    expect(gaps).toHaveLength(2);
    expect(gaps.find((item) => item.key === "subject_combination")?.label).toBe("选科组合");
    expect(gaps.find((item) => item.key === "comprehensive_quality_evaluation")?.label).toBe("综合素质评价材料");
    expect(formatPathwayMaterialKey("accept_service_commitment")).toBe("定向服务约束接受度");
    expect(formatPathwayMaterialKey("comprehensive_college_chapter_plan")).toBe("综评院校章程和分专业计划");
    expect(formatPathwayMaterialKey("early_batch_physical_political_review")).toBe("提前批体检、面试、政审或背景调查材料");
    expect(formatPathwayMaterialKey("special_type_chapter_limits")).toBe("特殊类型高校章程和测试限制");
  });

  it("summarizes evaluation statuses for the teacher-facing result strip", () => {
    const summary = summarizePathwayStatuses([
      buildEvaluation({ status: "possible", status_label: "可能适合" }),
      buildEvaluation({ pathway_id: 12, status: "not_recommended", status_label: "不建议" }),
      buildEvaluation({ pathway_id: 13, status: "possible", status_label: "可能适合" }),
    ]);

    expect(summary).toEqual([
      { status: "possible", label: "可能适合", count: 2 },
      { status: "not_recommended", label: "不建议", count: 1 },
    ]);
    expect(pathwayStatusTagType("not_recommended")).toBe("danger");
  });
});
