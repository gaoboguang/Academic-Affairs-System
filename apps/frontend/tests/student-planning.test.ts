import { describe, expect, it } from "vitest";

import {
  buildMaterialGapTaskDraft,
  formatPlanningPriority,
  formatPlanningStatus,
  isPlanningTaskOverdue,
  sortPlanningTasks,
  summarizePlanningTasks,
  type PlanningTask,
} from "../src/components/planning/studentPlanning";

function task(overrides: Partial<PlanningTask>): PlanningTask {
  return {
    id: 1,
    student_id: 1,
    source_type: "manual",
    task_type: "stage_review",
    task_type_label: "阶段复盘",
    title: "任务",
    status: "not_started",
    status_label: "未开始",
    priority: "medium",
    priority_label: "中",
    is_overdue: false,
    ...overrides,
  };
}

describe("student planning helpers", () => {
  it("formats status and priority with Chinese labels", () => {
    expect(formatPlanningStatus("review")).toBe("待复核");
    expect(formatPlanningStatus("custom")).toBe("custom");
    expect(formatPlanningPriority("high")).toBe("高");
  });

  it("detects overdue tasks without marking completed tasks", () => {
    const today = new Date("2026-04-28T08:00:00");
    expect(isPlanningTaskOverdue(task({ due_date: "2026-04-27" }), today)).toBe(true);
    expect(isPlanningTaskOverdue(task({ due_date: "2026-04-27", status: "completed" }), today)).toBe(false);
    expect(isPlanningTaskOverdue(task({ due_date: "2026-04-28" }), today)).toBe(false);
  });

  it("sorts overdue and high-priority review tasks first", () => {
    const today = new Date("2026-04-28T08:00:00");
    const sorted = sortPlanningTasks(
      [
        task({ id: 1, title: "已完成", status: "completed", due_date: "2026-04-20" }),
        task({ id: 2, title: "待复核", status: "review", priority: "high", due_date: "2026-04-30" }),
        task({ id: 3, title: "逾期材料", task_type: "material", priority: "medium", due_date: "2026-04-21" }),
      ],
      today,
    );

    expect(sorted.map((item) => item.title)).toEqual(["逾期材料", "待复核", "已完成"]);
  });

  it("summarizes open, overdue, due-soon and material tasks", () => {
    const today = new Date("2026-04-28T08:00:00");
    const summary = summarizePlanningTasks(
      [
        task({ id: 1, status: "completed", due_date: "2026-04-20" }),
        task({ id: 2, task_type: "material", due_date: "2026-04-27" }),
        task({ id: 3, due_date: "2026-05-03" }),
      ],
      today,
    );

    expect(summary).toMatchObject({
      open_task_count: 2,
      completed_task_count: 1,
      overdue_task_count: 1,
      due_soon_task_count: 1,
      material_gap_task_count: 1,
    });
  });

  it("builds task drafts from material gaps", () => {
    expect(
      buildMaterialGapTaskDraft(
        {
          material_label: "高考报名确认材料",
          next_action: "补充报名截图后重新评估。",
        },
        "普通类常规批",
      ),
    ).toMatchObject({
      task_type: "material",
      title: "补齐普通类常规批材料：高考报名确认材料",
      description: "补充报名截图后重新评估。",
    });
  });
});
