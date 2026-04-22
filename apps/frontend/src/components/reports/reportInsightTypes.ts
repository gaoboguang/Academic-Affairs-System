export type ReportInsightTone = "success" | "warning" | "info";

export interface ReportInsightCard {
  key: string;
  title: string;
  summary: string;
  detail: string;
  tone: ReportInsightTone;
}

export interface ReportInsightCardGroup {
  key: string;
  title: string;
  cards: ReportInsightCard[];
}

export interface RecommendationReportInsightOption {
  province?: string | null;
  target_year?: number | null;
  score_input_label?: string | null;
  reference_exam_name?: string | null;
  use_historical_mapping?: boolean;
  score_confidence?: string | null;
}

export interface RecommendationReportInsightCompareOption {
  scheme_id: number;
  scheme_name?: string | null;
  generated_at?: string | null;
  province?: string | null;
  target_year?: number | null;
}

export interface StudentAnalysisSubjectInsight {
  subject_id: number;
  subject_name: string;
  score: number | null;
  class_rank?: number | null;
  grade_rank?: number | null;
  class_percentile?: number | null;
  grade_percentile?: number | null;
  score_delta?: number | null;
}

export interface StudentAnalysisInsightData {
  student_name: string;
  exam_name: string;
  total_score: number;
  class_rank?: number | null;
  grade_rank?: number | null;
  class_percentile?: number | null;
  grade_percentile?: number | null;
  previous_exam_name?: string | null;
  total_score_delta?: number | null;
  subjects: StudentAnalysisSubjectInsight[];
}

export interface ClassAnalysisSubjectInsight {
  subject_id: number;
  subject_name: string;
  average_score: number;
  excellent_rate: number;
  pass_rate: number;
  valid_count?: number;
}

export interface ClassAnalysisInsightData {
  class_name: string;
  exam_name: string;
  student_count: number;
  total_average: number;
  total_median: number;
  grade_average?: number | null;
  subject_breakdown: ClassAnalysisSubjectInsight[];
}

export interface GradeAnalysisClassInsight {
  class_id?: number | null;
  class_name: string;
  student_count: number;
  average_score: number;
  excellent_rate?: number | null;
}

export interface GradeAnalysisSubjectInsight {
  subject_id: number;
  subject_name: string;
  average_score: number;
  excellent_rate: number;
  pass_rate: number;
  contribution_rate?: number | null;
}

export interface GradeAnalysisInsightData {
  grade_name: string;
  exam_name: string;
  student_count: number;
  total_average: number;
  total_median: number;
  excellent_rate?: number | null;
  class_breakdown: GradeAnalysisClassInsight[];
  subject_breakdown: GradeAnalysisSubjectInsight[];
}

export interface TeacherAssignmentInsight {
  assignment_id: number;
  class_name?: string | null;
  subject_name?: string | null;
  average_score: number;
  excellent_rate: number;
  pass_rate: number;
  valid_count: number;
}

export interface TeacherAnalysisInsightData {
  teacher_name: string;
  exam_name: string;
  overall_average?: number | null;
  assignment_breakdown: TeacherAssignmentInsight[];
}

export interface WorkloadInsightData {
  semester_name?: string | null;
  rule_version_name?: string | null;
  teacher_name?: string | null;
  weekly_hours: number;
  semester_hours: number;
  semester_workload: number;
  monthly_hours_json?: Record<string, number> | null;
}

export interface EvaluationTeacherInsight {
  teacher_id: number;
  teacher_name: string;
  overall_avg_score: number;
  response_count: number;
  rank?: number | null;
  dimension_scores_json?: Record<string, number> | null;
}

export interface EvaluationInsightData {
  batch_id: number;
  template_name: string;
  semester_name?: string | null;
  teacher_count: number;
  teacher_summaries: EvaluationTeacherInsight[];
}

export interface AdviserQuantInsightData {
  teacher_id: number;
  teacher_name: string;
  semester_name?: string | null;
  rule_version_name?: string | null;
  total_score: number;
  positive_score: number;
  negative_score: number;
  record_count: number;
  class_names: string[];
  category_scores_json?: Record<string, number> | null;
}

export interface GrowthAttachmentInsight {
  id: number;
}

export interface GrowthRecordInsight {
  id: number;
  occurred_on: string;
  record_type: string;
  title: string;
  owner_name?: string | null;
  attachments: GrowthAttachmentInsight[];
}

export interface GrowthProfileInsightData {
  student: {
    student_no: string;
    name: string;
    current_grade_name?: string | null;
    current_class_name?: string | null;
  };
}

export interface GrowthInsightData {
  profile: GrowthProfileInsightData;
  records: GrowthRecordInsight[];
}
