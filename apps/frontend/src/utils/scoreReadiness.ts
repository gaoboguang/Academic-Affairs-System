export interface ScoreReadinessContext {
  examCount: number;
  scoreRecordTotal: number;
  selectedExamName?: string | null;
}

export function buildScoreReadinessMessages(context: ScoreReadinessContext): string[] {
  const messages: string[] = [];
  if (context.examCount <= 0) {
    messages.push("当前还没有考试，请先在考试成绩中心创建考试并配置科目。");
  }
  if (context.scoreRecordTotal <= 0) {
    messages.push("当前成绩记录为 0，学生、班级、年级和教师分析会显示空态；请先导入成绩表。");
  }
  if (context.examCount === 1 && context.scoreRecordTotal > 0) {
    messages.push("当前只有 1 场考试，趋势变化只能作为单次快照，不宜解读为升降趋势。");
  }
  if (context.selectedExamName && context.scoreRecordTotal > 0) {
    messages.push(`当前分析围绕“${context.selectedExamName}”展开，切换考试后需重新查看统计口径。`);
  }
  return messages;
}

export function buildScoreReportGuardMessages(
  reportType: string,
  context: ScoreReadinessContext,
): string[] {
  const scoreReportTypes = new Set(["student_analysis", "student_knowledge_plan", "class_analysis", "grade_summary", "teacher_analysis"]);
  if (!scoreReportTypes.has(reportType)) return [];
  if (context.scoreRecordTotal <= 0) {
    return ["成绩类报表需要先导入成绩记录；当前成绩库为空，生成报表容易造成误读。"];
  }
  if (context.examCount === 1) {
    return ["当前只有 1 场考试，报表中的趋势字段只代表单次考试快照。"];
  }
  return [];
}
