import type {
  RecommendationResult,
  VolunteerDraftDetail,
} from "../recommendations/types";
import type {
  AdviserQuantInsightData,
  ClassAnalysisInsightData,
  EvaluationInsightData,
  GradeAnalysisInsightData,
  GrowthInsightData,
  StudentAnalysisInsightData,
  TeacherAnalysisInsightData,
  WorkloadInsightData,
} from "./reportInsights";

export interface ReportInsightFormState {
  report_type: string;
  exam_id?: number;
  student_id?: number;
  scheme_id?: number;
  draft_id?: number;
  batch_id?: number;
  class_id?: number;
  grade_id?: number;
  teacher_id?: number;
  semester_id?: number;
  rule_version_id?: number;
}

export interface ReportInsightDataState {
  recommendationResults: RecommendationResult[];
  recommendationCompareResults: RecommendationResult[];
  volunteerDraftDetail: VolunteerDraftDetail | null;
  studentAnalysis: StudentAnalysisInsightData | null;
  classAnalysis: ClassAnalysisInsightData | null;
  gradeAnalysis: GradeAnalysisInsightData | null;
  teacherAnalysis: TeacherAnalysisInsightData | null;
  workloadResults: WorkloadInsightData[];
  evaluationOverview: EvaluationInsightData | null;
  adviserSummary: AdviserQuantInsightData[];
  growthInsight: GrowthInsightData | null;
}

export type ReportInsightRequest = <T>(url: string) => Promise<T>;

export interface ReportInsightFetchOptions {
  recommendationCompareSchemeId?: number;
}

export function createEmptyReportInsightDataState(): ReportInsightDataState {
  return {
    recommendationResults: [],
    recommendationCompareResults: [],
    volunteerDraftDetail: null,
    studentAnalysis: null,
    classAnalysis: null,
    gradeAnalysis: null,
    teacherAnalysis: null,
    workloadResults: [],
    evaluationOverview: null,
    adviserSummary: [],
    growthInsight: null,
  };
}

export async function fetchReportInsightData(
  form: ReportInsightFormState,
  request: ReportInsightRequest,
  options: ReportInsightFetchOptions = {},
): Promise<ReportInsightDataState> {
  if (form.report_type === "recommendation_summary" && form.scheme_id && form.student_id) {
    const [recommendationResults, recommendationCompareResults] = await Promise.all([
      request<RecommendationResult[]>(
        `/api/recommendations/history/${form.scheme_id}/results?student_id=${form.student_id}`,
      ),
      options.recommendationCompareSchemeId
        ? request<RecommendationResult[]>(
          `/api/recommendations/history/${options.recommendationCompareSchemeId}/results?student_id=${form.student_id}`,
        ).catch(() => [] as RecommendationResult[])
        : Promise.resolve([] as RecommendationResult[]),
    ]);
    return {
      ...createEmptyReportInsightDataState(),
      recommendationResults,
      recommendationCompareResults,
    };
  }

  if (form.report_type === "volunteer_draft_summary" && form.draft_id) {
    return {
      ...createEmptyReportInsightDataState(),
      volunteerDraftDetail: await request<VolunteerDraftDetail>(`/api/recommendations/volunteer-drafts/${form.draft_id}`),
    };
  }

  if (form.report_type === "student_analysis" && form.student_id && form.exam_id) {
    return {
      ...createEmptyReportInsightDataState(),
      studentAnalysis: await request<StudentAnalysisInsightData>(`/api/analytics/students/${form.student_id}?exam_id=${form.exam_id}`),
    };
  }

  if (form.report_type === "class_analysis" && form.class_id && form.exam_id) {
    return {
      ...createEmptyReportInsightDataState(),
      classAnalysis: await request<ClassAnalysisInsightData>(`/api/analytics/classes/${form.class_id}?exam_id=${form.exam_id}`),
    };
  }

  if (form.report_type === "grade_summary" && form.grade_id && form.exam_id) {
    return {
      ...createEmptyReportInsightDataState(),
      gradeAnalysis: await request<GradeAnalysisInsightData>(`/api/analytics/grades/${form.grade_id}?exam_id=${form.exam_id}`),
    };
  }

  if (form.report_type === "teacher_analysis" && form.teacher_id && form.exam_id) {
    return {
      ...createEmptyReportInsightDataState(),
      teacherAnalysis: await request<TeacherAnalysisInsightData>(`/api/analytics/teachers/${form.teacher_id}?exam_id=${form.exam_id}`),
    };
  }

  if (form.report_type === "teacher_workload" && form.semester_id) {
    const query = new URLSearchParams({ semester_id: String(form.semester_id) });
    if (form.rule_version_id) {
      query.set("rule_version_id", String(form.rule_version_id));
    }
    return {
      ...createEmptyReportInsightDataState(),
      workloadResults: await request<WorkloadInsightData[]>(`/api/workload/results?${query.toString()}`),
    };
  }

  if (form.report_type === "evaluation_summary" && form.batch_id) {
    return {
      ...createEmptyReportInsightDataState(),
      evaluationOverview: await request<EvaluationInsightData>(`/api/evaluation/batches/${form.batch_id}/overview`),
    };
  }

  if (form.report_type === "adviser_quant_summary" && form.semester_id) {
    const query = new URLSearchParams({ semester_id: String(form.semester_id) });
    if (form.rule_version_id) {
      query.set("rule_version_id", String(form.rule_version_id));
    }
    return {
      ...createEmptyReportInsightDataState(),
      adviserSummary: await request<AdviserQuantInsightData[]>(`/api/adviser-quant/summary?${query.toString()}`),
    };
  }

  if (form.report_type === "growth_summary" && form.student_id) {
    const [profile, timeline] = await Promise.all([
      request<GrowthInsightData["profile"]>(`/api/students/${form.student_id}/profile`),
      request<{ items: GrowthInsightData["records"]; total: number }>(`/api/archives/students/${form.student_id}/records`),
    ]);
    return {
      ...createEmptyReportInsightDataState(),
      growthInsight: {
        profile,
        records: timeline.items,
      },
    };
  }

  return createEmptyReportInsightDataState();
}
