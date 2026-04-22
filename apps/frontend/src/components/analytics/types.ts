export interface PanoramaExamPoint {
  exam_id: number;
  exam_name: string;
  exam_date: string;
  academic_year_id?: number | null;
  academic_year_name?: string | null;
  semester_name?: string | null;
  student_count: number;
  total_average: number;
  total_median: number;
  excellent_rate?: number | null;
  top10_count: number;
  top30_count: number;
}

export interface PanoramaYearSummary {
  academic_year_id: number;
  academic_year_name: string;
  exam_count: number;
  average_score: number;
  average_excellent_rate?: number | null;
  best_exam_name: string;
  latest_exam_name: string;
}

export interface PanoramaSubjectPoint {
  exam_id: number;
  exam_name: string;
  exam_date: string;
  academic_year_name?: string | null;
  average_score: number;
  excellent_rate: number;
  valid_count: number;
}

export interface PanoramaSubjectTrend {
  subject_id: number;
  subject_name: string;
  points: PanoramaSubjectPoint[];
}

export interface PanoramaDataset {
  academic_year_count: number;
  exam_count: number;
  year_summaries: PanoramaYearSummary[];
  exam_points: PanoramaExamPoint[];
  subject_trends: PanoramaSubjectTrend[];
}

export interface GradePanoramaResponse extends PanoramaDataset {
  grade_id: number;
  grade_name: string;
}

export interface ClassPanoramaResponse extends PanoramaDataset {
  class_id: number;
  class_name: string;
}

export interface TeacherPanoramaResponse extends PanoramaDataset {
  teacher_id: number;
  teacher_name: string;
}

export interface PanoramaMetricCard {
  label: string;
  value: string | number;
  help: string;
  tone: string;
}

export interface PanoramaSubjectTrendRow {
  subject_id: number;
  subject_name: string;
  exam_count: number;
  first_average: number | string;
  latest_average: number | string;
  delta_average: number | string;
  latest_excellent_rate: number | string;
}

export interface PanoramaInsightCard {
  label: string;
  value: string | number;
  help: string;
  tone: string;
}

export interface PanoramaYearCompetitionRow {
  academic_year_id: number;
  academic_year_name: string;
  exam_count: number;
  average_score: number;
  average_excellent_rate?: number | null;
  best_exam_name: string;
  latest_exam_name: string;
  leadLabel: string;
}

export interface PanoramaExamTimelineRow {
  exam_id: number;
  exam_name: string;
  exam_date: string;
  academic_year_name?: string | null;
  semester_name?: string | null;
  total_average: number;
  total_median: number;
  excellent_rate?: number | null;
  delta_average: number | string;
  delta_top30: number | string;
}

export interface PanoramaSubjectPriorityRow {
  subject_id: number;
  subject_name: string;
  latest_average: number | string;
  delta_average: number | string;
  latest_excellent_rate: number | string;
  delta_excellent_rate: number | string;
  swing: number | string;
  trendLabel: string;
  focusLabel: string;
  alertLevel: string;
  momentumScore: number;
  riskScore: number;
}
