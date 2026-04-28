export function recommendationPrintPreviewPath(studentId: number, schemeId: number): string {
  return `/print/recommendations/${studentId}/${schemeId}`;
}

export function growthSummaryPrintPreviewPath(studentId: number): string {
  return `/print/growth-summary/${studentId}`;
}

export function studentAnalysisPrintPreviewPath(studentId: number, examId: number): string {
  return `/print/student-analysis/${studentId}/${examId}`;
}

export function classAnalysisPrintPreviewPath(classId: number, examId: number): string {
  return `/print/class-analysis/${classId}/${examId}`;
}

export function gradeSummaryPrintPreviewPath(gradeId: number, examId: number): string {
  return `/print/grade-summary/${gradeId}/${examId}`;
}

export function teacherAnalysisPrintPreviewPath(teacherId: number, examId: number): string {
  return `/print/teacher-analysis/${teacherId}/${examId}`;
}

export function workloadPrintPreviewPath(semesterId: number, ruleVersionId?: number): string {
  return `/print/workload/${semesterId}${ruleVersionId ? `?ruleVersionId=${ruleVersionId}` : ""}`;
}

export function evaluationSummaryPrintPreviewPath(batchId: number): string {
  return `/print/evaluation-summary/${batchId}`;
}

export function adviserQuantPrintPreviewPath(semesterId: number, ruleVersionId?: number): string {
  return `/print/adviser-quant/${semesterId}${ruleVersionId ? `?ruleVersionId=${ruleVersionId}` : ""}`;
}

export function adviserWeeklySummaryPrintPreviewPath(
  classId: number,
  examId?: number,
  startDate?: string,
  endDate?: string,
): string {
  const params = new URLSearchParams();
  if (examId) params.set("examId", String(examId));
  if (startDate) params.set("startDate", startDate);
  if (endDate) params.set("endDate", endDate);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return `/print/adviser-weekly-summary/${classId}${suffix}`;
}

export function studentFollowupPackagePrintPreviewPath(
  studentId: number,
  examId?: number,
  startDate?: string,
  endDate?: string,
): string {
  const params = new URLSearchParams();
  if (examId) params.set("examId", String(examId));
  if (startDate) params.set("startDate", startDate);
  if (endDate) params.set("endDate", endDate);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return `/print/student-followup-package/${studentId}${suffix}`;
}

export function planningFollowupPrintPreviewPath(studentId: number, examId?: number): string {
  const params = new URLSearchParams();
  if (examId) params.set("examId", String(examId));
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return `/print/planning-followup/${studentId}${suffix}`;
}

export function volunteerDraftPrintPreviewPath(draftId: number): string {
  return `/print/volunteer-drafts/${draftId}`;
}

export function shandongRecommendationPrintPreviewPath(storageKey: string): string {
  return `/print/shandong-recommendation/${encodeURIComponent(storageKey)}`;
}

export function gaokaoPathwayPrintPreviewPath(storageKey: string): string {
  return `/print/gaokao-pathway-report/${encodeURIComponent(storageKey)}`;
}

export function gaokaoDataCoveragePrintPreviewPath(storageKey: string): string {
  return `/print/gaokao-data-coverage/${encodeURIComponent(storageKey)}`;
}
