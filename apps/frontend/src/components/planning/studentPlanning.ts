export type PlanningStatus = "not_started" | "in_progress" | "review" | "completed" | "paused";
export type PlanningPriority = "high" | "medium" | "low";

export interface PlanningTask {
  id?: number | null;
  student_id: number;
  goal_id?: number | null;
  source_type: string;
  source_ref_id?: string | null;
  task_type: string;
  task_type_label: string;
  title: string;
  description?: string | null;
  status: PlanningStatus | string;
  status_label: string;
  priority: PlanningPriority | string;
  priority_label: string;
  due_date?: string | null;
  completed_at?: string | null;
  related_route?: string | null;
  is_overdue: boolean;
}

export interface PlanningGoal {
  id: number;
  student_id: number;
  target_year: number;
  pathway_code: string;
  pathway_name: string;
  target_college?: string | null;
  target_major?: string | null;
  target_score?: number | null;
  target_rank?: number | null;
  backup_pathways?: string | null;
  status: PlanningStatus | string;
  status_label: string;
  priority: PlanningPriority | string;
  priority_label: string;
  note?: string | null;
}

export interface PlanningSummary {
  open_task_count: number;
  completed_task_count: number;
  overdue_task_count: number;
  due_soon_task_count: number;
  material_gap_task_count: number;
  no_goal: boolean;
  has_pathway_profile: boolean;
  has_pathway_evaluations: boolean;
}

export interface PlanningTaskDraft {
  task_type: string;
  title: string;
  description?: string | null;
  priority: PlanningPriority;
  due_date?: string | null;
}

export const planningStatusLabels: Record<PlanningStatus, string> = {
  not_started: "未开始",
  in_progress: "进行中",
  review: "待复核",
  completed: "已完成",
  paused: "暂缓",
};

export const planningPriorityLabels: Record<PlanningPriority, string> = {
  high: "高",
  medium: "中",
  low: "低",
};

const statusOrder: Record<string, number> = {
  review: 0,
  in_progress: 1,
  not_started: 2,
  paused: 3,
  completed: 4,
};

const priorityOrder: Record<string, number> = {
  high: 0,
  medium: 1,
  low: 2,
};

export function formatPlanningStatus(value?: string | null): string {
  if (!value) return "未开始";
  return planningStatusLabels[value as PlanningStatus] ?? value;
}

export function formatPlanningPriority(value?: string | null): string {
  if (!value) return "中";
  return planningPriorityLabels[value as PlanningPriority] ?? value;
}

export function isPlanningTaskOverdue(task: Pick<PlanningTask, "due_date" | "status">, today = new Date()): boolean {
  if (!task.due_date || task.status === "completed") return false;
  const due = new Date(`${task.due_date}T00:00:00`);
  const normalizedToday = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  return due.getTime() < normalizedToday.getTime();
}

export function sortPlanningTasks<T extends PlanningTask>(tasks: T[], today = new Date()): T[] {
  return [...tasks].sort((left, right) => {
    const leftOverdue = isPlanningTaskOverdue(left, today) ? 0 : 1;
    const rightOverdue = isPlanningTaskOverdue(right, today) ? 0 : 1;
    if (leftOverdue !== rightOverdue) return leftOverdue - rightOverdue;
    const leftStatus = statusOrder[left.status] ?? 9;
    const rightStatus = statusOrder[right.status] ?? 9;
    if (leftStatus !== rightStatus) return leftStatus - rightStatus;
    const leftPriority = priorityOrder[left.priority] ?? 9;
    const rightPriority = priorityOrder[right.priority] ?? 9;
    if (leftPriority !== rightPriority) return leftPriority - rightPriority;
    return String(left.due_date ?? "9999-12-31").localeCompare(String(right.due_date ?? "9999-12-31"));
  });
}

export function summarizePlanningTasks(tasks: PlanningTask[], today = new Date()): PlanningSummary {
  const activeTasks = tasks.filter((item) => item.status !== "completed");
  const soon = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 7);
  return {
    open_task_count: activeTasks.length,
    completed_task_count: tasks.filter((item) => item.status === "completed").length,
    overdue_task_count: activeTasks.filter((item) => isPlanningTaskOverdue(item, today)).length,
    due_soon_task_count: activeTasks.filter((item) => {
      if (!item.due_date || isPlanningTaskOverdue(item, today)) return false;
      const due = new Date(`${item.due_date}T00:00:00`);
      return due.getTime() <= soon.getTime();
    }).length,
    material_gap_task_count: activeTasks.filter((item) => item.task_type === "material").length,
    no_goal: false,
    has_pathway_profile: false,
    has_pathway_evaluations: false,
  };
}

export function buildMaterialGapTaskDraft(gap: { material_label?: string; next_action?: string }, pathwayName: string): PlanningTaskDraft {
  const label = gap.material_label || "待补材料";
  return {
    task_type: "material",
    title: `补齐${pathwayName}材料：${label}`,
    description: gap.next_action || `补充${label}后重新评估该路径。`,
    priority: "medium",
  };
}
