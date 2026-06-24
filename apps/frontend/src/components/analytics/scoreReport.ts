export interface ExamScoreReportSubject {
  subject_id: number;
  subject_name: string;
  full_score?: number | null;
  sort_order: number;
  is_in_total: boolean;
}

export interface ExamScoreReportSubjectScore {
  subject_id: number;
  subject_name: string;
  score?: number | null;
  original_score?: number | null;
  converted_score?: number | null;
  score_value_type: string;
  score_value_label: string;
  class_rank?: number | null;
  grade_rank?: number | null;
  grade_percentile?: number | null;
  excellent_flag: boolean;
  pass_flag: boolean;
}

export interface ExamScoreReportRow {
  student_id: number;
  student_no: string;
  student_name: string;
  class_id?: number | null;
  class_name?: string | null;
  total_score?: number | null;
  score_value_type: string;
  score_value_label: string;
  class_rank?: number | null;
  grade_rank?: number | null;
  grade_percentile?: number | null;
  subject_scores: ExamScoreReportSubjectScore[];
}

export interface NormalizedExamScoreReportRow extends ExamScoreReportRow {
  subjectScoreById: Record<number, ExamScoreReportSubjectScore>;
}

export interface ExamScoreReportSummary {
  student_count: number;
  subject_count: number;
  total_average?: number | null;
  total_max?: number | null;
  total_min?: number | null;
}

export interface ExamScoreReportResponse {
  exam_id: number;
  exam_name: string;
  rank_scope_label: string;
  subjects: ExamScoreReportSubject[];
  summary: ExamScoreReportSummary;
  rows: ExamScoreReportRow[];
  total: number;
  page: number;
  page_size: number;
}

export interface ExamScoreReportQuery {
  classId?: number | null;
  keyword?: string | null;
  sortBy?: string;
  sortOrder?: string;
  page?: number;
  pageSize?: number;
}

export function buildExamScoreReportQuery(query: ExamScoreReportQuery): string {
  const params = new URLSearchParams();
  if (query.classId) params.set("class_id", String(query.classId));
  if (query.keyword?.trim()) params.set("keyword", query.keyword.trim());
  if (query.sortBy) params.set("sort_by", query.sortBy);
  if (query.sortOrder) params.set("sort_order", query.sortOrder);
  if (query.page) params.set("page", String(query.page));
  if (query.pageSize) params.set("page_size", String(query.pageSize));
  const value = params.toString();
  return value ? `?${value}` : "";
}

export function buildVisibleSubjectIds(
  subjects: ExamScoreReportSubject[],
  selectedSubjectIds: number[],
): number[] {
  if (!selectedSubjectIds.length) {
    return subjects.map((item) => item.subject_id);
  }
  const selected = new Set(selectedSubjectIds);
  return subjects.filter((item) => selected.has(item.subject_id)).map((item) => item.subject_id);
}

export function normalizeExamScoreReportRows(rows: ExamScoreReportRow[]): NormalizedExamScoreReportRow[] {
  return rows.map((row) => ({
    ...row,
    subjectScoreById: Object.fromEntries(row.subject_scores.map((item) => [item.subject_id, item])),
  }));
}

export function getSubjectScore(
  row: NormalizedExamScoreReportRow,
  subjectId: number,
): ExamScoreReportSubjectScore | null {
  return row.subjectScoreById[subjectId] ?? null;
}

export function formatScoreCell(value?: number | null): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return Number.isInteger(value) ? value.toFixed(0) : value.toFixed(2).replace(/\.?0+$/, "");
}

export function formatPercentCell(value?: number | null): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return `${(value * 100).toFixed(1)}%`;
}
