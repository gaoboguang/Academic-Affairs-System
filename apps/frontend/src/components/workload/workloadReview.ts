import type { StatusCard, TimetableBatchItem, TimetableEntryItem, WorkloadResultItem } from "./types";

export interface TimetableReviewSummary {
  totalRows: number;
  unmatchedTeachers: number;
  unmatchedClasses: number;
  unmatchedSubjects: number;
  unmatchedCourseTypes: number;
  conflictSlots: number;
  emptyFieldRows: number;
}

export function buildTimetableReviewSummary(entries: TimetableEntryItem[]): TimetableReviewSummary {
  const teacherSlots = new Map<string, number>();
  const classSlots = new Map<string, number>();
  let emptyFieldRows = 0;
  for (const item of entries) {
    if (!item.raw_teacher_name || !item.raw_class_name || !item.raw_subject_name || !item.raw_course_type) {
      emptyFieldRows += 1;
    }
    if (item.teacher_id) {
      const key = `${item.teacher_id}:${item.weekday}:${item.period_no}`;
      teacherSlots.set(key, (teacherSlots.get(key) ?? 0) + 1);
    }
    if (item.class_id) {
      const key = `${item.class_id}:${item.weekday}:${item.period_no}`;
      classSlots.set(key, (classSlots.get(key) ?? 0) + 1);
    }
  }
  const conflictSlots = [...teacherSlots.values(), ...classSlots.values()].filter((count) => count > 1).length;
  return {
    totalRows: entries.length,
    unmatchedTeachers: entries.filter((item) => !item.teacher_id && Boolean(item.raw_teacher_name)).length,
    unmatchedClasses: entries.filter((item) => !item.class_id && Boolean(item.raw_class_name)).length,
    unmatchedSubjects: entries.filter((item) => !item.subject_id && Boolean(item.raw_subject_name)).length,
    unmatchedCourseTypes: entries.filter((item) => !item.course_type && Boolean(item.raw_course_type)).length,
    conflictSlots,
    emptyFieldRows,
  };
}

export function buildTimetableReviewCards(summary: TimetableReviewSummary): StatusCard[] {
  return [
    { label: "未匹配教师", value: summary.unmatchedTeachers, help: "教师姓名或工号未匹配时不会计入教师课时。", tone: summary.unmatchedTeachers ? "tone-amber" : "tone-green" },
    { label: "未匹配班级", value: summary.unmatchedClasses, help: "班级无法匹配会影响班额和班级维度系数。", tone: summary.unmatchedClasses ? "tone-amber" : "tone-green" },
    { label: "未匹配学科", value: summary.unmatchedSubjects, help: "学科无法匹配会影响学科系数和统计口径。", tone: summary.unmatchedSubjects ? "tone-amber" : "tone-green" },
    { label: "冲突课时", value: summary.conflictSlots, help: "同一教师或班级同节次重复出现，建议人工复核。", tone: summary.conflictSlots ? "tone-amber" : "tone-green" },
    { label: "空字段行", value: summary.emptyFieldRows, help: "教师、班级、学科或课程类型有空值的行。", tone: summary.emptyFieldRows ? "tone-amber" : "tone-green" },
  ];
}

export function buildWorkloadPrecheckMessages(input: {
  selectedSemesterId: number | null;
  selectedRuleVersionId: number | null;
  currentBatch: TimetableBatchItem | null;
  ruleItemCount: number;
  reviewSummary: TimetableReviewSummary;
}): string[] {
  const messages: string[] = [];
  if (!input.selectedSemesterId) messages.push("请先选择学期。");
  if (!input.selectedRuleVersionId) messages.push("请先选择工作量规则版本。");
  if (!input.currentBatch) messages.push("请先选择或导入课表批次。");
  if (input.ruleItemCount <= 0) messages.push("当前规则版本没有规则项，计算结果可能全部按默认值处理。");
  if (input.currentBatch?.unresolved_count) messages.push(`当前批次仍有 ${input.currentBatch.unresolved_count} 条未匹配记录，未修正条目不会参与计算。`);
  if (input.reviewSummary.conflictSlots) messages.push(`发现 ${input.reviewSummary.conflictSlots} 个疑似冲突课时，建议先复核再计算。`);
  if (input.reviewSummary.emptyFieldRows) messages.push(`发现 ${input.reviewSummary.emptyFieldRows} 行空字段，建议补齐教师、班级、学科和课程类型。`);
  return messages;
}

export function buildWorkloadResultReviewCards(results: WorkloadResultItem[]): StatusCard[] {
  const highCount = results.filter((item) => item.weekly_hours >= 30).length;
  const lowCount = results.filter((item) => item.weekly_hours <= 0 || item.semester_workload <= 0).length;
  const noDetailCount = results.filter((item) => !(item.snapshot_json?.details ?? []).length).length;
  const totalHours = results.reduce((sum, item) => sum + item.semester_hours, 0).toFixed(2);
  return [
    { label: "教师数", value: results.length, help: "本次结果覆盖的教师数量。", tone: results.length ? "tone-blue" : "tone-slate" },
    { label: "学期总课时", value: totalHours, help: "所有教师学期课时合计。", tone: "tone-blue" },
    { label: "异常高课时", value: highCount, help: "周课时达到 30 及以上，建议复核是否重复导入。", tone: highCount ? "tone-amber" : "tone-green" },
    { label: "低/零工作量", value: lowCount, help: "周课时或工作量为 0 的教师需检查课表和附加项。", tone: lowCount ? "tone-amber" : "tone-green" },
    { label: "无明细结果", value: noDetailCount, help: "没有课时明细的结果不适合直接交付。", tone: noDetailCount ? "tone-amber" : "tone-green" },
  ];
}
