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

export function volunteerDraftPrintPreviewPath(draftId: number): string {
  return `/print/volunteer-drafts/${draftId}`;
}
