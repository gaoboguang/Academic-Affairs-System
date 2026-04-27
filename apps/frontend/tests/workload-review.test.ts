import { describe, expect, it } from "vitest";

import {
  buildTimetableReviewSummary,
  buildWorkloadPrecheckMessages,
  buildWorkloadResultReviewCards,
} from "../src/components/workload/workloadReview";
import type { TimetableEntryItem, WorkloadResultItem } from "../src/components/workload/types";

const entries: TimetableEntryItem[] = [
  {
    id: 1,
    batch_id: 1,
    semester_id: 2,
    weekday: 1,
    period_no: 1,
    teacher_id: 1,
    class_id: 1,
    subject_id: 1,
    course_type: "regular",
    week_rule: "all",
    mapping_status: "matched",
    raw_teacher_name: "李语文",
    raw_class_name: "1班",
    raw_subject_name: "语文",
    raw_course_type: "正课",
    is_active: true,
  },
  {
    id: 2,
    batch_id: 1,
    semester_id: 2,
    weekday: 1,
    period_no: 1,
    teacher_id: 1,
    class_id: null,
    subject_id: null,
    course_type: null,
    week_rule: "all",
    mapping_status: "unresolved",
    raw_teacher_name: "李语文",
    raw_class_name: "未知班",
    raw_subject_name: "未知课",
    raw_course_type: "未知类型",
    is_active: true,
  },
];

describe("workload review helpers", () => {
  it("summarizes timetable review risks", () => {
    const summary = buildTimetableReviewSummary(entries);
    expect(summary.unmatchedClasses).toBe(1);
    expect(summary.unmatchedSubjects).toBe(1);
    expect(summary.unmatchedCourseTypes).toBe(1);
    expect(summary.conflictSlots).toBe(1);
  });

  it("builds calculation precheck messages", () => {
    const summary = buildTimetableReviewSummary(entries);
    const messages = buildWorkloadPrecheckMessages({
      selectedSemesterId: 2,
      selectedRuleVersionId: 1,
      currentBatch: {
        id: 1,
        semester_id: 2,
        import_time: "2026-04-27",
        status: "partially_failed",
        entry_count: 2,
        unresolved_count: 1,
        is_active: true,
      },
      ruleItemCount: 0,
      reviewSummary: summary,
    });
    expect(messages).toContain("当前规则版本没有规则项，计算结果可能全部按默认值处理。");
    expect(messages.some((item) => item.includes("疑似冲突课时"))).toBe(true);
  });

  it("flags high and zero workload results", () => {
    const results: WorkloadResultItem[] = [
      {
        id: 1,
        teacher_id: 1,
        semester_id: 2,
        rule_version_id: 1,
        weekly_hours: 32,
        semester_hours: 640,
        semester_workload: 660,
        snapshot_json: { details: [{ weekday: 1, period_no: 1, active_week_count: 20, coefficient: 1, semester_contribution: 20 }] },
        calculated_at: "2026-04-27",
        is_active: true,
      },
      {
        id: 2,
        teacher_id: 2,
        semester_id: 2,
        rule_version_id: 1,
        weekly_hours: 0,
        semester_hours: 0,
        semester_workload: 0,
        snapshot_json: { details: [] },
        calculated_at: "2026-04-27",
        is_active: true,
      },
    ];
    const cards = buildWorkloadResultReviewCards(results);
    expect(cards.find((item) => item.label === "异常高课时")?.value).toBe(1);
    expect(cards.find((item) => item.label === "低/零工作量")?.value).toBe(1);
  });
});
