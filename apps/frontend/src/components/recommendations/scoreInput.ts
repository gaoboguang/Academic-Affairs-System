import type { RiskPreference, ScoreInputMode } from "./types";

export interface RecommendationScoreInputFields {
  score_input_mode: ScoreInputMode;
  score_range_min?: number;
  score_range_max?: number;
  rank_range_min?: number;
  rank_range_max?: number;
  reference_exam_name: string;
  use_historical_mapping: boolean;
  risk_preference: RiskPreference;
  student_rank_override?: number;
  comprehensive_score?: number;
  culture_score?: number;
}

export function normalizeOptionalString(value?: string | null): string | undefined {
  const normalized = (value ?? "").trim();
  return normalized || undefined;
}

export function validateScoreInputFields(form: RecommendationScoreInputFields): string | null {
  if (form.score_input_mode === "estimated_score" && form.comprehensive_score === undefined && form.culture_score === undefined) {
    return "预估分模式至少需要填写预估总分或文化分";
  }
  if (
    form.score_input_mode === "estimated_score_and_rank"
    && (form.student_rank_override === undefined || (form.comprehensive_score === undefined && form.culture_score === undefined))
  ) {
    return "预估分+位次模式需要同时填写预估分数和预估位次";
  }
  if (
    form.score_input_mode === "score_range"
    && (form.score_range_min === undefined || form.score_range_max === undefined)
  ) {
    return "分数区间模式需要填写上下限";
  }
  if (
    form.score_input_mode === "score_range"
    && form.score_range_min !== undefined
    && form.score_range_max !== undefined
    && form.score_range_min > form.score_range_max
  ) {
    return "分数区间下限不能大于上限";
  }
  if (
    form.score_input_mode === "rank_range"
    && (form.rank_range_min === undefined || form.rank_range_max === undefined)
  ) {
    return "位次区间模式需要填写上下限";
  }
  if (
    form.score_input_mode === "rank_range"
    && form.rank_range_min !== undefined
    && form.rank_range_max !== undefined
    && form.rank_range_min > form.rank_range_max
  ) {
    return "位次区间下限不能大于上限";
  }
  return null;
}

export function buildScoreInputPayload(form: RecommendationScoreInputFields) {
  return {
    score_input_mode: form.score_input_mode,
    score_range_min: form.score_range_min,
    score_range_max: form.score_range_max,
    rank_range_min: form.rank_range_min,
    rank_range_max: form.rank_range_max,
    reference_exam_name: normalizeOptionalString(form.reference_exam_name),
    use_historical_mapping: form.use_historical_mapping,
    risk_preference: form.risk_preference,
  };
}
