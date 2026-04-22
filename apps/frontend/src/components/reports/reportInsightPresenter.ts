import type { ReportInsightDataState } from "./reportInsightLoader";
import {
  buildAdviserQuantInsightCards,
  buildClassAnalysisInsightCards,
  buildEvaluationInsightCards,
  buildGradeAnalysisInsightCards,
  buildRecommendationReportInsightCardGroups,
  buildGrowthInsightCards,
  buildRecommendationReportInsightCards,
  buildStudentAnalysisInsightCards,
  buildTeacherAnalysisInsightCards,
  buildVolunteerDraftReportInsightCardGroups,
  buildVolunteerDraftReportInsightCards,
  buildWorkloadInsightCards,
  type RecommendationReportInsightCompareOption,
  type RecommendationReportInsightOption,
  type ReportInsightCard,
  type ReportInsightCardGroup,
} from "./reportInsights";

export function buildReportInsightCards(
  reportType: string,
  data: ReportInsightDataState,
  recommendationOption: RecommendationReportInsightOption | null,
  recommendationCompareOption: RecommendationReportInsightCompareOption | null = null,
): ReportInsightCard[] {
  if (reportType === "student_analysis" && data.studentAnalysis) {
    return buildStudentAnalysisInsightCards(data.studentAnalysis);
  }
  if (reportType === "class_analysis" && data.classAnalysis) {
    return buildClassAnalysisInsightCards(data.classAnalysis);
  }
  if (reportType === "grade_summary" && data.gradeAnalysis) {
    return buildGradeAnalysisInsightCards(data.gradeAnalysis);
  }
  if (reportType === "teacher_analysis" && data.teacherAnalysis) {
    return buildTeacherAnalysisInsightCards(data.teacherAnalysis);
  }
  if (reportType === "teacher_workload" && data.workloadResults.length) {
    return buildWorkloadInsightCards(data.workloadResults);
  }
  if (reportType === "evaluation_summary" && data.evaluationOverview) {
    return buildEvaluationInsightCards(data.evaluationOverview);
  }
  if (reportType === "adviser_quant_summary" && data.adviserSummary.length) {
    return buildAdviserQuantInsightCards(data.adviserSummary);
  }
  if (reportType === "growth_summary" && data.growthInsight) {
    return buildGrowthInsightCards(data.growthInsight);
  }
  if (reportType === "recommendation_summary" && data.recommendationResults.length) {
    return buildRecommendationReportInsightCards(
      data.recommendationResults,
      recommendationOption,
      data.recommendationCompareResults,
      recommendationCompareOption,
    );
  }
  if (reportType === "volunteer_draft_summary" && data.volunteerDraftDetail) {
    return buildVolunteerDraftReportInsightCards({
      rules: data.volunteerDraftDetail.applicable_rules ?? [],
      selectedRule: data.volunteerDraftDetail.selected_rule ?? null,
      draftItems: data.volunteerDraftDetail.items,
      ruleAlerts: data.volunteerDraftDetail.rule_alerts ?? [],
    });
  }
  return [];
}

export function buildReportInsightGroups(
  reportType: string,
  cards: ReportInsightCard[],
): ReportInsightCardGroup[] {
  if (reportType === "recommendation_summary") {
    return buildRecommendationReportInsightCardGroups(cards);
  }
  if (reportType === "volunteer_draft_summary") {
    return buildVolunteerDraftReportInsightCardGroups(cards);
  }
  return [];
}

export function getReportInsightDescription(reportType: string): string {
  if (["student_analysis", "class_analysis", "grade_summary", "teacher_analysis"].includes(reportType)) {
    return "基于当前选中的分析对象和考试参数，先确认核心数字、趋势和重点学科，再决定导出或打印。";
  }
  if (["teacher_workload", "evaluation_summary", "adviser_quant_summary", "growth_summary"].includes(reportType)) {
    return "基于当前报表所依赖的学期、批次或学生档案，先确认汇总范围和关键摘要，再决定导出或打印。";
  }
  if (["recommendation_summary", "volunteer_draft_summary"].includes(reportType)) {
    return "基于当前选中的推荐方案或志愿草稿，先看清材料里的风险提示和解释范围，再决定导出或打印。";
  }
  return "基于当前报表参数先做一轮导出前复核，避免把错误对象、考试或规则版本带入正式输出。";
}

export function shouldShowReportInsightSection(options: {
  loading: boolean;
  error: string;
  loaded: boolean;
  cards: ReportInsightCard[];
}): boolean {
  return options.loading || Boolean(options.error) || options.loaded || options.cards.length > 0;
}
