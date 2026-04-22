import { describe, expect, it } from "vitest";

import {
  buildRecommendationSubmissionWarningMessage,
  buildBatchRecommendationPayload,
  buildSingleRecommendationPayload,
  createRecommendationForm,
  hasRecommendationFormPendingChanges,
  validateRecommendationSubmission,
} from "../src/components/recommendations/recommendationSubmission";
import type { RecommendationFormState } from "../src/components/recommendations/types";

function buildForm(overrides: Partial<RecommendationFormState> = {}): RecommendationFormState {
  return {
    name: "  方案 A  ",
    student_id: 1,
    student_ids: [1, 2],
    exam_id: 3,
    target_year: 2026,
    province: "广东",
    target_regions_json: [" 深圳 ", "广东", "", "深圳"],
    school_level_tags_json: [" 双一流 ", "", "双一流"],
    major_keyword: " 软件工程 ",
    subject_combination: " 物化生 ",
    obey_adjustment: false,
    score_input_mode: "estimated_score_and_rank",
    score_range_min: undefined,
    score_range_max: undefined,
    rank_range_min: undefined,
    rank_range_max: undefined,
    reference_exam_name: " 2026届一模 ",
    use_historical_mapping: true,
    risk_preference: "balanced",
    student_rank_override: 31000,
    comprehensive_score: 580,
    professional_score: 240,
    culture_score: 340,
    note: "  关注就业方向  ",
    ...overrides,
  };
}

const studentOptions = [
  { id: 1, student_no: "2026001", name: "张三", origin_province: "广东" },
  { id: 2, student_no: "2026002", name: "李四", origin_province: "湖南" },
];

describe("recommendation submission helpers", () => {
  it("validates required inputs for single and batch mode", () => {
    expect(validateRecommendationSubmission(buildForm({ student_id: undefined }), false, studentOptions)).toBe(
      "单个学生推荐需要学生和考试",
    );
    expect(validateRecommendationSubmission(buildForm({ exam_id: undefined }), true, studentOptions)).toBe(
      "批量推荐至少需要学生列表和考试",
    );
    expect(
      validateRecommendationSubmission(
        buildForm({ province: "", student_ids: [1, 2] }),
        true,
        studentOptions,
      ),
    ).toBeNull();
    expect(validateRecommendationSubmission(buildForm(), false, studentOptions)).toBeNull();
    expect(validateRecommendationSubmission(buildForm(), true, studentOptions)).toBeNull();
  });

  it("builds normalized single recommendation payloads", () => {
    expect(buildSingleRecommendationPayload(buildForm())).toEqual({
      student_id: 1,
      exam_id: 3,
      name: "方案 A",
      target_year: 2026,
      province: "广东",
      target_regions_json: ["深圳", "广东"],
      school_level_tags_json: ["双一流"],
      major_keyword: "软件工程",
      subject_combination: "物化生",
      obey_adjustment: false,
      score_input_mode: "estimated_score_and_rank",
      score_range_min: undefined,
      score_range_max: undefined,
      rank_range_min: undefined,
      rank_range_max: undefined,
      reference_exam_name: "2026届一模",
      use_historical_mapping: true,
      risk_preference: "balanced",
      student_rank_override: 31000,
      comprehensive_score: 580,
      professional_score: 240,
      culture_score: 340,
      note: "关注就业方向",
    });
  });

  it("builds batch payloads without single-student override fields", () => {
    expect(buildBatchRecommendationPayload(buildForm())).toEqual({
      student_ids: [1, 2],
      exam_id: 3,
      name: "方案 A",
      target_year: 2026,
      province: "广东",
      target_regions_json: ["深圳", "广东"],
      school_level_tags_json: ["双一流"],
      major_keyword: "软件工程",
      subject_combination: "物化生",
      obey_adjustment: false,
      note: "关注就业方向",
    });
  });

  it("detects pending recommendation form changes", () => {
    expect(hasRecommendationFormPendingChanges(createRecommendationForm())).toBe(false);
    expect(hasRecommendationFormPendingChanges(buildForm())).toBe(true);
    expect(
      hasRecommendationFormPendingChanges(
        buildForm({
          name: "  ",
          province: " 广东 ",
          target_regions_json: ["深圳", " 深圳 "],
          school_level_tags_json: ["双一流", " 双一流 "],
          major_keyword: " 软件工程 ",
          subject_combination: " 物化生 ",
          reference_exam_name: " 2026届一模 ",
          note: "  关注就业方向  ",
        }),
      ),
    ).toBe(true);
  });

  it("builds generation warnings for simulated or overridden scenarios", () => {
    expect(
      buildRecommendationSubmissionWarningMessage(
        buildForm(),
        false,
        studentOptions,
      ),
    ).toContain("当前按“预估分 + 预估位次”生成");

    expect(
      buildRecommendationSubmissionWarningMessage(
        buildForm({
          score_input_mode: "actual_rank",
          use_historical_mapping: false,
          province: "广东",
        }),
        true,
        studentOptions,
      ),
    ).toContain("统一按“广东”生成");

    expect(
      buildRecommendationSubmissionWarningMessage(
        buildForm({
          province: "",
          score_input_mode: "actual_rank",
          use_historical_mapping: false,
        }),
        true,
        studentOptions,
      ),
    ).toContain("多个生源地分别生成");

    expect(
      buildRecommendationSubmissionWarningMessage(
        buildForm({
          score_input_mode: "actual_rank",
          use_historical_mapping: false,
        }),
        false,
        studentOptions,
      ),
    ).toBeNull();
  });
});
