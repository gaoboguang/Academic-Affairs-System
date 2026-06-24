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

export interface StudentKnowledgePointAnalytics {
  subject_id: number;
  subject_name: string;
  knowledge_point_id: number;
  knowledge_point_name: string;
  knowledge_path?: string | null;
  score: number;
  full_score: number;
  score_rate?: number | null;
  grade_average_rate?: number | null;
  grade_gap_rate?: number | null;
  lost_score: number;
  priority_score: number;
  diagnosis_label: string;
  error_tag_stats?: Array<{ tag?: string; name?: string; count?: number }>;
  dominant_error_tag?: string | null;
  question_count: number;
  question_numbers?: string[];
  suggestion?: string | null;
}

export interface StudentKnowledgeTrendPoint {
  exam_id: number;
  exam_name: string;
  exam_date: string;
  score_rate?: number | null;
  grade_average_rate?: number | null;
  grade_gap_rate?: number | null;
  full_score: number;
  lost_score: number;
  diagnosis_label: string;
  question_numbers?: string[];
}

export interface StudentKnowledgeTrendAnalytics {
  subject_id: number;
  subject_name: string;
  knowledge_point_id: number;
  knowledge_point_name: string;
  knowledge_path?: string | null;
  trend_exam_count: number;
  weak_exam_count: number;
  latest_score_rate?: number | null;
  average_score_rate?: number | null;
  latest_grade_gap_rate?: number | null;
  average_grade_gap_rate?: number | null;
  trend_delta?: number | null;
  total_full_score: number;
  total_lost_score: number;
  priority_score: number;
  trend_label: string;
  error_tag_stats?: Array<{ tag?: string; name?: string; count?: number }>;
  dominant_error_tag?: string | null;
  points: StudentKnowledgeTrendPoint[];
  suggestion?: string | null;
}

export interface ExamAnalyzableStudentOption {
  id: number;
  student_no: string;
  name: string;
  current_class_name?: string | null;
  total_score?: number | null;
  grade_rank?: number | null;
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
  knowledge_points?: StudentKnowledgePointAnalytics[];
  knowledge_trends?: StudentKnowledgeTrendAnalytics[];
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
  if (category === "fix_weakness" || category === "target_warning" || category === "knowledge_focus" || category === "knowledge_trend_focus") return "warning";
  return "info";
}

export function getKnowledgeDiagnosisTone(label?: string | null): "success" | "warning" | "info" {
  if (label === "正常") return "success";
  if (label === "优先补弱" || label === "需要巩固" || label === "低于年级") return "warning";
  return "info";
}

export function getKnowledgeTrendTone(label?: string | null): "success" | "warning" | "info" {
  if (label === "正在改善" || label === "保持观察") return "success";
  if (label === "持续薄弱" || label === "波动反复") return "warning";
  return "info";
}

export function filterKnowledgePointsBySubject(
  points: StudentKnowledgePointAnalytics[],
  subjectId?: number | null,
): StudentKnowledgePointAnalytics[] {
  if (!subjectId) return points;
  return points.filter((item) => item.subject_id === subjectId);
}

export function filterKnowledgeTrendsBySubject(
  points: StudentKnowledgeTrendAnalytics[],
  subjectId?: number | null,
): StudentKnowledgeTrendAnalytics[] {
  if (!subjectId) return points;
  return points.filter((item) => item.subject_id === subjectId);
}

export function formatQuestionNumbers(values?: string[] | null): string {
  return values?.length ? values.join("、") : "-";
}

export function formatKnowledgeTrendTrack(points?: StudentKnowledgeTrendPoint[] | null): string {
  if (!points?.length) return "-";
  return points
    .map((item) => `${item.exam_name} ${formatPercentValue(item.score_rate)}`)
    .join(" / ");
}

export function formatErrorTagStats(values?: Array<{ tag?: string; name?: string; count?: number }> | null): string {
  if (!values?.length) return "-";
  return values
    .map((item) => {
      const tag = item.tag ?? item.name;
      return tag ? `${tag}${item.count ? `×${item.count}` : ""}` : "";
    })
    .filter(Boolean)
    .join("、") || "-";
}

export function knowledgeDisplayName(item: { knowledge_point_name: string; knowledge_path?: string | null }): string {
  return item.knowledge_path || item.knowledge_point_name;
}

export function getBriefingPriorityTone(label?: string | null): "success" | "warning" | "danger" | "info" {
  if (label === "高") return "danger";
  if (label === "中") return "warning";
  if (label === "低") return "info";
  return "info";
}

export function formatTaskPreviewSummary(createCount: number, skipCount: number): string {
  if (!createCount && !skipCount) return "暂无可生成任务";
  return `可生成 ${createCount} 项，已存在 ${skipCount} 项`;
}

export function pickExamStudentSelection(
  students: ExamAnalyzableStudentOption[],
  currentStudentId?: number | null,
): number | null {
  if (currentStudentId && students.some((item) => item.id === currentStudentId)) {
    return currentStudentId;
  }
  return students[0]?.id ?? null;
}

export function formatExamStudentOptionLabel(student: ExamAnalyzableStudentOption): string {
  const details = [
    student.current_class_name,
    typeof student.grade_rank === "number" ? `校内${student.grade_rank}名` : null,
  ].filter(Boolean);
  const suffix = details.length ? `（${details.join(" / ")}）` : "";
  return `${student.student_no} - ${student.name}${suffix}`;
}
