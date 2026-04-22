import type {
  ClassAnalysisInsightData,
  GradeAnalysisInsightData,
  ReportInsightCard,
  StudentAnalysisInsightData,
  TeacherAnalysisInsightData,
} from "./reportInsightTypes";
import {
  buildStudentSubjectDetail,
  formatNumber,
  formatPercent,
  formatTeacherAssignment,
  pickMaxBy,
  pickMinBy,
  pickStudentFocusSubject,
  pickStudentStrongestSubject,
  trendToneByDelta,
} from "./reportInsightShared";

export function buildStudentAnalysisInsightCards(data: StudentAnalysisInsightData): ReportInsightCard[] {
  const cards: ReportInsightCard[] = [];
  const rankSegments: string[] = [];
  if (data.class_rank != null) {
    rankSegments.push(`班级第 ${data.class_rank}`);
  }
  if (data.grade_rank != null) {
    rankSegments.push(`年级第 ${data.grade_rank}`);
  }
  cards.push({
    key: "student_overview",
    title: "本次成绩摘要",
    summary: `${data.student_name} 在 ${data.exam_name} 取得总分 ${formatNumber(data.total_score)}`,
    detail:
      rankSegments.join(" / ") ||
      "当前摘要可用于导出前快速复核学生本次成绩定位，避免把错误考试或学生参数带入报表。",
    tone: "info",
  });

  if (typeof data.total_score_delta === "number") {
    const trendLabel =
      data.total_score_delta > 0 ? "较上次考试提升" : data.total_score_delta < 0 ? "较上次考试回落" : "与上次考试基本持平";
    cards.push({
      key: "student_trend",
      title: "阶段趋势",
      summary: `${trendLabel} ${formatNumber(Math.abs(data.total_score_delta))} 分`,
      detail: data.previous_exam_name
        ? `对比考试：${data.previous_exam_name}。导出前建议确认本次分析是否使用了正确的对比考试。`
        : "当前暂无上一场考试可对比，导出结果会以单次考试分析为主。",
      tone: trendToneByDelta(data.total_score_delta),
    });
  }

  const strongestSubject = pickStudentStrongestSubject(data.subjects);
  if (strongestSubject) {
    cards.push({
      key: "student_strength",
      title: "优势学科",
      summary: `${strongestSubject.subject_name} 当前表现最强`,
      detail: buildStudentSubjectDetail(strongestSubject, "可在汇报时作为稳定得分点优先展示。"),
      tone: "success",
    });
  }

  const focusSubject = pickStudentFocusSubject(data.subjects);
  if (focusSubject && focusSubject.subject_id !== strongestSubject?.subject_id) {
    cards.push({
      key: "student_focus",
      title: "重点关注学科",
      summary: `${focusSubject.subject_name} 建议继续重点复核`,
      detail: buildStudentSubjectDetail(focusSubject, "如需导出给班主任或任课教师，这一科更适合作为后续跟进重点。"),
      tone: "warning",
    });
  }

  return cards;
}

export function buildClassAnalysisInsightCards(data: ClassAnalysisInsightData): ReportInsightCard[] {
  const cards: ReportInsightCard[] = [
    {
      key: "class_overview",
      title: "班级整体状态",
      summary: `${data.class_name} 共 ${data.student_count} 人，总分均分 ${formatNumber(data.total_average)}，中位数 ${formatNumber(data.total_median)}`,
      detail: "当前摘要可用于导出前确认班级规模和整体分布是否符合预期，避免误选班级或考试。",
      tone: "info",
    },
  ];

  if (typeof data.grade_average === "number") {
    const delta = data.total_average - data.grade_average;
    cards.push({
      key: "class_grade_delta",
      title: "与年级对比",
      summary: delta >= 0 ? `班级均分高于年级 ${formatNumber(delta)} 分` : `班级均分低于年级 ${formatNumber(Math.abs(delta))} 分`,
      detail: `班级均分 ${formatNumber(data.total_average)}，年级均分 ${formatNumber(data.grade_average)}。`,
      tone: trendToneByDelta(delta),
    });
  }

  const strongestSubject = pickMaxBy(data.subject_breakdown, (item) => item.average_score);
  if (strongestSubject) {
    cards.push({
      key: "class_strength_subject",
      title: "优势学科",
      summary: `${strongestSubject.subject_name} 当前均分最高`,
      detail: `均分 ${formatNumber(strongestSubject.average_score)}，优秀率 ${formatPercent(strongestSubject.excellent_rate)}，及格率 ${formatPercent(strongestSubject.pass_rate)}。`,
      tone: "success",
    });
  }

  const focusSubject = pickMinBy(data.subject_breakdown, (item) => item.pass_rate);
  if (focusSubject && focusSubject.subject_id !== strongestSubject?.subject_id) {
    cards.push({
      key: "class_focus_subject",
      title: "重点攻坚学科",
      summary: `${focusSubject.subject_name} 当前及格率最低`,
      detail: `均分 ${formatNumber(focusSubject.average_score)}，及格率 ${formatPercent(focusSubject.pass_rate)}，优秀率 ${formatPercent(focusSubject.excellent_rate)}。`,
      tone: "warning",
    });
  }

  return cards;
}

export function buildGradeAnalysisInsightCards(data: GradeAnalysisInsightData): ReportInsightCard[] {
  const cards: ReportInsightCard[] = [
    {
      key: "grade_overview",
      title: "年级整体状态",
      summary: `${data.grade_name} 共 ${data.student_count} 人，均分 ${formatNumber(data.total_average)}，中位数 ${formatNumber(data.total_median)}`,
      detail:
        typeof data.excellent_rate === "number"
          ? `当前优秀率 ${formatPercent(data.excellent_rate)}，适合作为导出前的整体判断基线。`
          : "当前摘要可用于导出前确认年级整体成绩面貌和人数口径。",
      tone: "info",
    },
  ];

  const bestClass = pickMaxBy(data.class_breakdown, (item) => item.average_score);
  if (bestClass) {
    cards.push({
      key: "grade_best_class",
      title: "领先班级",
      summary: `${bestClass.class_name} 当前均分领先`,
      detail: `班级均分 ${formatNumber(bestClass.average_score)}，人数 ${bestClass.student_count}${
        typeof bestClass.excellent_rate === "number" ? `，优秀率 ${formatPercent(bestClass.excellent_rate)}` : ""
      }。`,
      tone: "success",
    });
  }

  const riskClass = pickMinBy(data.class_breakdown, (item) => item.average_score);
  if (riskClass && riskClass.class_name !== bestClass?.class_name) {
    cards.push({
      key: "grade_risk_class",
      title: "需重点跟进班级",
      summary: `${riskClass.class_name} 当前均分相对靠后`,
      detail: `班级均分 ${formatNumber(riskClass.average_score)}，人数 ${riskClass.student_count}${
        typeof riskClass.excellent_rate === "number" ? `，优秀率 ${formatPercent(riskClass.excellent_rate)}` : ""
      }。`,
      tone: "warning",
    });
  }

  const focusSubject = pickMinBy(data.subject_breakdown, (item) => item.pass_rate);
  if (focusSubject) {
    cards.push({
      key: "grade_focus_subject",
      title: "学科攻坚重点",
      summary: `${focusSubject.subject_name} 当前及格率最低`,
      detail: `均分 ${formatNumber(focusSubject.average_score)}，及格率 ${formatPercent(focusSubject.pass_rate)}，优秀率 ${formatPercent(focusSubject.excellent_rate)}。`,
      tone: "warning",
    });
  }

  return cards;
}

export function buildTeacherAnalysisInsightCards(data: TeacherAnalysisInsightData): ReportInsightCard[] {
  const cards: ReportInsightCard[] = [
    {
      key: "teacher_overview",
      title: "任教整体状态",
      summary:
        typeof data.overall_average === "number"
          ? `${data.teacher_name} 当前任教均分 ${formatNumber(data.overall_average)}`
          : `${data.teacher_name} 当前共有 ${data.assignment_breakdown.length} 条任教分析`,
      detail: `当前分析基于 ${data.assignment_breakdown.length} 条任教拆分结果，可用于导出前确认教师与考试参数是否正确。`,
      tone: "info",
    },
  ];

  const bestAssignment = pickMaxBy(data.assignment_breakdown, (item) => item.average_score);
  if (bestAssignment) {
    cards.push({
      key: "teacher_best_assignment",
      title: "表现最佳任教拆分",
      summary: `${formatTeacherAssignment(bestAssignment)} 当前均分最高`,
      detail: `均分 ${formatNumber(bestAssignment.average_score)}，优秀率 ${formatPercent(bestAssignment.excellent_rate)}，及格率 ${formatPercent(bestAssignment.pass_rate)}。`,
      tone: "success",
    });
  }

  const focusAssignment = pickMinBy(data.assignment_breakdown, (item) => item.pass_rate);
  if (focusAssignment && focusAssignment.assignment_id !== bestAssignment?.assignment_id) {
    cards.push({
      key: "teacher_focus_assignment",
      title: "需重点跟进任教拆分",
      summary: `${formatTeacherAssignment(focusAssignment)} 当前及格率最低`,
      detail: `均分 ${formatNumber(focusAssignment.average_score)}，及格率 ${formatPercent(focusAssignment.pass_rate)}，优秀率 ${formatPercent(focusAssignment.excellent_rate)}。`,
      tone: "warning",
    });
  }

  return cards;
}
