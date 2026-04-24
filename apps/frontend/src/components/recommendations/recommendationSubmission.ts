import { uniqueStrings } from "./helpers";
import {
  buildScoreInputPayload,
  normalizeOptionalString,
  validateScoreInputFields,
} from "./scoreInput";
import type { RecommendationFormState, StudentOption } from "./types";

export function createRecommendationForm(): RecommendationFormState {
  return {
    name: "",
    student_id: undefined,
    student_ids: [],
    exam_id: undefined,
    target_year: new Date().getFullYear(),
    province: "山东",
    target_regions_json: [],
    school_level_tags_json: [],
    major_keyword: "",
    subject_combination: "",
    obey_adjustment: false,
    score_input_mode: "actual_rank",
    score_range_min: undefined,
    score_range_max: undefined,
    rank_range_min: undefined,
    rank_range_max: undefined,
    reference_exam_name: "",
    use_historical_mapping: false,
    risk_preference: "balanced",
    student_rank_override: undefined,
    comprehensive_score: undefined,
    professional_score: undefined,
    culture_score: undefined,
    note: "",
  };
}

export interface RecommendationSinglePayload {
  student_id: number;
  exam_id: number;
  name?: string;
  target_year?: number;
  province?: string;
  target_regions_json: string[];
  school_level_tags_json: string[];
  major_keyword?: string;
  subject_combination?: string;
  obey_adjustment: boolean;
  score_input_mode: string;
  score_range_min?: number;
  score_range_max?: number;
  rank_range_min?: number;
  rank_range_max?: number;
  reference_exam_name?: string;
  use_historical_mapping: boolean;
  risk_preference: string;
  student_rank_override?: number;
  comprehensive_score?: number;
  professional_score?: number;
  culture_score?: number;
  note?: string;
}

export interface RecommendationBatchPayload {
  student_ids: number[];
  exam_id: number;
  name?: string;
  target_year?: number;
  province?: string;
  target_regions_json: string[];
  school_level_tags_json: string[];
  major_keyword?: string;
  subject_combination?: string;
  obey_adjustment: boolean;
  note?: string;
}

function hasStudentOriginProvince(studentOptions: StudentOption[], studentId: number | undefined): boolean {
  if (!studentId) return false;
  return Boolean(studentOptions.find((item) => item.id === studentId)?.origin_province?.trim());
}

export function validateRecommendationSubmission(
  form: RecommendationFormState,
  isBatchMode: boolean,
  studentOptions: StudentOption[],
): string | null {
  if (isBatchMode) {
    if (!form.student_ids.length || !form.exam_id) {
      return "批量推荐至少需要学生列表和考试";
    }
    if (!form.province.trim()) {
      const missingProvinceStudents = form.student_ids.filter((studentId) => !hasStudentOriginProvince(studentOptions, studentId));
      if (missingProvinceStudents.length) {
        return "批量推荐未设置统一生源地，且所选学生中仍有未维护生源地档案的记录";
      }
    }
    return null;
  }
  if (!form.student_id || !form.exam_id) {
    return "单个学生推荐需要学生和考试";
  }
  if (!form.province.trim() && !hasStudentOriginProvince(studentOptions, form.student_id)) {
    return "请先选择生源地，或在学生档案中维护生源地省份";
  }
  return validateScoreInputFields(form);
}

export function buildSingleRecommendationPayload(form: RecommendationFormState): RecommendationSinglePayload {
  return {
    student_id: form.student_id as number,
    exam_id: form.exam_id as number,
    name: normalizeOptionalString(form.name),
    target_year: form.target_year,
    province: normalizeOptionalString(form.province),
    target_regions_json: uniqueStrings(form.target_regions_json),
    school_level_tags_json: uniqueStrings(form.school_level_tags_json),
    major_keyword: normalizeOptionalString(form.major_keyword),
    subject_combination: normalizeOptionalString(form.subject_combination),
    obey_adjustment: form.obey_adjustment,
    ...buildScoreInputPayload(form),
    student_rank_override: form.student_rank_override,
    comprehensive_score: form.comprehensive_score,
    professional_score: form.professional_score,
    culture_score: form.culture_score,
    note: normalizeOptionalString(form.note),
  };
}

export function buildBatchRecommendationPayload(form: RecommendationFormState): RecommendationBatchPayload {
  return {
    student_ids: [...form.student_ids],
    exam_id: form.exam_id as number,
    name: normalizeOptionalString(form.name),
    target_year: form.target_year,
    province: normalizeOptionalString(form.province),
    target_regions_json: uniqueStrings(form.target_regions_json),
    school_level_tags_json: uniqueStrings(form.school_level_tags_json),
    major_keyword: normalizeOptionalString(form.major_keyword),
    subject_combination: normalizeOptionalString(form.subject_combination),
    obey_adjustment: form.obey_adjustment,
    note: normalizeOptionalString(form.note),
  };
}

export function hasRecommendationFormPendingChanges(form: RecommendationFormState): boolean {
  const initial = createRecommendationForm();
  return JSON.stringify({
    ...form,
    name: normalizeOptionalString(form.name) ?? "",
    province: normalizeOptionalString(form.province) ?? "",
    target_regions_json: uniqueStrings(form.target_regions_json),
    school_level_tags_json: uniqueStrings(form.school_level_tags_json),
    major_keyword: normalizeOptionalString(form.major_keyword) ?? "",
    subject_combination: normalizeOptionalString(form.subject_combination) ?? "",
    reference_exam_name: normalizeOptionalString(form.reference_exam_name) ?? "",
    note: normalizeOptionalString(form.note) ?? "",
  }) !== JSON.stringify(initial);
}

export function buildRecommendationSubmissionWarningMessage(
  form: RecommendationFormState,
  isBatchMode: boolean,
  studentOptions: StudentOption[],
): string | null {
  const segments: string[] = [];

  if (isBatchMode) {
    const selectedStudents = studentOptions.filter((item) => form.student_ids.includes(item.id));
    const studentProvinces = Array.from(
      new Set(selectedStudents.map((item) => item.origin_province?.trim()).filter(Boolean)),
    ) as string[];
    if (form.province.trim()) {
      if (studentProvinces.length > 1) {
        segments.push(`当前会统一按“${form.province.trim()}”生成，覆盖所选学生原本不同的生源地档案`);
      } else {
        segments.push(`当前会统一按“${form.province.trim()}”生成批量方案`);
      }
    } else if (studentProvinces.length > 1) {
      segments.push(`当前会按学生档案中的多个生源地分别生成：${studentProvinces.join(" / ")}`);
    }
  } else {
    const scoreModeLabel = {
      actual_rank: "正式位次",
      actual_score: "正式分数",
      estimated_score: "预估分数",
      estimated_score_and_rank: "预估分 + 预估位次",
      score_range: "分数区间",
      rank_range: "位次区间",
    }[form.score_input_mode] ?? form.score_input_mode;

    if (form.score_input_mode !== "actual_rank" && form.score_input_mode !== "actual_score") {
      segments.push(`当前按“${scoreModeLabel}”生成，结果更适合做方向性参考`);
    }
    if (form.use_historical_mapping) {
      segments.push("当前启用了历年映射估算，正式出分后建议重新复核");
    }
  }

  if (!segments.length) {
    return null;
  }
  return `${segments.join("；")}。是否继续生成？`;
}
