export interface StudentTargetLineGap {
  line_id: number;
  line_name: string;
  threshold_label: string;
  gap_score?: number | null;
  gap_rank?: number | null;
  status: string;
}

export interface StudentSubjectEffectiveTarget {
  line_id: number;
  line_name: string;
  target_score: number;
  actual_score?: number | null;
  gap_score?: number | null;
}

export interface StudentSubjectAnalyticsV1 {
  subject_id: number;
  subject_name: string;
  score: number | null;
  grade_rank?: number | null;
  grade_percentile?: number | null;
  z_score?: number | null;
  t_score?: number | null;
  rank_deviation?: number | null;
  peer_average_score?: number | null;
  peer_average_delta?: number | null;
  trend_rank_stddev?: number | null;
  primary_effective_line_name?: string | null;
  primary_effective_score?: number | null;
  primary_effective_score_gap?: number | null;
  effective_score_targets?: StudentSubjectEffectiveTarget[];
  diagnosis?: string;
  diagnosis_tags?: string[];
}

export interface StudentTotalTrendPoint {
  exam_id: number;
  exam_name: string;
  exam_date: string;
  total_score?: number | null;
  class_rank?: number | null;
  grade_rank?: number | null;
  grade_percentile?: number | null;
}

export interface StudentSubjectTrendSeries {
  subject_id: number;
  subject_name: string;
  points: Array<{
    exam_id: number;
    exam_name: string;
    exam_date: string;
    score?: number | null;
    grade_rank?: number | null;
    grade_percentile?: number | null;
  }>;
}

export interface StudentActionSuggestion {
  category: string;
  title: string;
  summary: string;
  subject_names?: string[];
  priority: number;
}

export interface StudentAnalyticsReportV1 {
  student_name: string;
  exam_name: string;
  total_score: number;
  class_rank?: number | null;
  grade_rank?: number | null;
  grade_percentile?: number | null;
  total_score_delta?: number | null;
  grade_rank_delta?: number | null;
  overview_sentence?: string;
  target_line_gaps?: StudentTargetLineGap[];
  subjects: StudentSubjectAnalyticsV1[];
  trend_points?: StudentTotalTrendPoint[];
  subject_trends?: StudentSubjectTrendSeries[];
  action_suggestions?: StudentActionSuggestion[];
}

export type RadarMetric = "pr" | "t_score";

export interface StudentRadarRow {
  subject: string;
  value: number;
  label: string;
}

export function formatPercentValue(value?: number | null): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return `${(value * 100).toFixed(1)}%`;
}

export function formatSignedNumber(value?: number | null, unit = ""): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${Number.isInteger(value) ? value.toFixed(0) : value.toFixed(2).replace(/\.?0+$/, "")}${unit}`;
}

export function formatDiagnosisTags(tags?: string[] | null): string {
  return tags?.length ? tags.join(" / ") : "正常";
}

export function buildStudentRadarRows(subjects: StudentSubjectAnalyticsV1[], metric: RadarMetric): StudentRadarRow[] {
  return subjects
    .map((item) => {
      const rawValue = metric === "pr" ? item.grade_percentile : item.t_score;
      if (typeof rawValue !== "number") return null;
      const value = metric === "pr" ? Math.round(rawValue * 1000) / 10 : Math.round(rawValue * 10) / 10;
      return {
        subject: item.subject_name,
        value,
        label: metric === "pr" ? `${value}%` : `${value}`,
      };
    })
    .filter((item): item is StudentRadarRow => item !== null);
}

export function pickPrimaryTargetGap(gaps?: StudentTargetLineGap[] | null): StudentTargetLineGap | null {
  if (!gaps?.length) return null;
  return gaps.find((item) => item.status === "near_below") ?? gaps.find((item) => !item.status.includes("reached")) ?? gaps[0] ?? null;
}

export function getTargetGapSummary(gaps?: StudentTargetLineGap[] | null): string {
  const primary = pickPrimaryTargetGap(gaps);
  if (!primary) return "未设置目标线";
  const scoreGap = formatSignedNumber(primary.gap_score, "分");
  const rankGap = formatSignedNumber(primary.gap_rank, "名");
  return `${primary.line_name}：${scoreGap}${rankGap !== "-" ? ` / ${rankGap}` : ""}`;
}

export function getSuggestionTone(category: string): "success" | "warning" | "info" {
  if (category === "keep_strength") return "success";
  if (category === "fix_weakness" || category === "target_warning") return "warning";
  return "info";
}
