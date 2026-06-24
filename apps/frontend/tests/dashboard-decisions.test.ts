import { describe, expect, it } from "vitest";

import { buildDashboardNextSteps } from "../src/components/dashboard/dashboardDecisions";

describe("dashboard decision helpers", () => {
  it("suggests concrete next actions for an empty teaching trial dataset", () => {
    const steps = buildDashboardNextSteps({
      student_total: 806,
      teacher_total: 2,
      exam_total: 1,
      score_record_total: 0,
      latest_backup: null,
      data_health: {
        status: "warning",
        label: "可验收但有数据警告",
        summary: "P0 安全底座可继续验收，但数据可用性仍需补齐和人工复核。",
        p0_gap_count: 3,
        warning_count: 5,
        blocking_count: 0,
        gaps: ["特殊类型已有招生计划但缺专门录取结果：单独招生、综合评价招生"],
      },
    });

    expect(steps.map((step) => step.code)).toEqual([
      "score_record_empty",
      "teacher_too_few",
    ]);
    expect(steps[0].path).toBe("/exams");
    expect(steps[1].title).toBe("教师台账待补充");
  });

  it("falls back to a ready state when the dashboard has no actionable warning", () => {
    const steps = buildDashboardNextSteps({
      student_total: 806,
      teacher_total: 20,
      exam_total: 3,
      score_record_total: 1200,
      latest_backup: {
        backup_name: "local_edu_backup.zip",
        created_at: "2026-04-27T12:30:00",
        status: "success",
        file_size: 1024,
      },
      data_health: {
        status: "pass",
        label: "P0 可通过",
        summary: "当前健康检查未发现阻断项或 P0 数据缺口。",
        p0_gap_count: 0,
        warning_count: 0,
        blocking_count: 0,
        gaps: [],
      },
      planning_summary: {
        open_task_count: 0,
        overdue_task_count: 0,
        due_soon_task_count: 0,
        students_without_goal_count: 0,
        volunteer_draft_without_review_count: 0,
        material_gap_without_due_count: 0,
      },
    });

    expect(steps).toHaveLength(1);
    expect(steps[0].code).toBe("ready_for_trial");
    expect(steps[0].path).toBe("/analytics");
  });

  it("surfaces planning reminders before the ready state", () => {
    const steps = buildDashboardNextSteps({
      student_total: 12,
      teacher_total: 12,
      exam_total: 2,
      score_record_total: 120,
      latest_backup: {
        backup_name: "local_edu_backup.zip",
        created_at: "2026-04-27T12:30:00",
        status: "success",
        file_size: 1024,
      },
      data_health: {
        status: "pass",
        label: "P0 可通过",
        summary: "",
        p0_gap_count: 0,
        warning_count: 0,
        blocking_count: 0,
        gaps: [],
      },
      planning_summary: {
        open_task_count: 3,
        overdue_task_count: 2,
        due_soon_task_count: 1,
        students_without_goal_count: 4,
        volunteer_draft_without_review_count: 0,
        material_gap_without_due_count: 0,
      },
    });

    expect(steps[0]).toMatchObject({
      code: "planning_overdue_tasks",
      path: "/students",
    });
  });
});
