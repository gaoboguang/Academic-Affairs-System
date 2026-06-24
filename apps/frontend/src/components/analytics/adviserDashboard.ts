export type AdviserRiskLevel = "urgent" | "follow_up" | "watch" | "normal";

export interface AdviserRiskStudentItem {
  student_id: number;
  student_no?: string | null;
  student_name: string;
  class_id?: number | null;
  class_name?: string | null;
  risk_level: AdviserRiskLevel;
  risk_label: string;
  primary_reason: string;
  reasons: string[];
  suggested_action: string;
}

export interface AdviserActionItem {
  action_type: string;
  title: string;
  count: number;
  student_ids: number[];
  target_route?: string | null;
}

export interface AdviserDashboardResponse {
  grade_id?: number | null;
  grade_name?: string | null;
  class_id?: number | null;
  class_name?: string | null;
  exam_id?: number | null;
  exam_name?: string | null;
  start_date: string;
  end_date: string;
  overview: {
    student_count: number;
    score_sample_count: number;
    growth_record_count: number;
    open_task_count: number;
    overdue_task_count: number;
    follow_up_count: number;
  };
  score_summary: {
    imported: boolean;
    sample_count: number;
    average_total_score?: number | null;
    low_score_count: number;
    decline_count: number;
  };
  growth_summary: {
    total_records: number;
    students_with_records_count: number;
    latest_record_date?: string | null;
  };
  planning_summary: {
    open_task_count: number;
    overdue_task_count: number;
    due_soon_task_count: number;
    high_priority_open_count: number;
    students_without_goal_count: number;
  };
  risk_students: AdviserRiskStudentItem[];
  action_items: AdviserActionItem[];
  data_flags: string[];
}

export function adviserRiskTagType(level: AdviserRiskLevel): "danger" | "warning" | "info" | "success" {
  if (level === "urgent") return "danger";
  if (level === "follow_up") return "warning";
  if (level === "watch") return "info";
  return "success";
}

export function formatGrowthSummary(summary: AdviserDashboardResponse["growth_summary"]): string {
  if (summary.total_records <= 0) return "暂无成长档案记录";
  return `记录 ${summary.total_records} 条，覆盖 ${summary.students_with_records_count} 人，最近 ${summary.latest_record_date ?? "-"}`;
}

export function formatPlanningSummary(summary: AdviserDashboardResponse["planning_summary"]): string {
  if (summary.open_task_count <= 0) return "暂无开放规划任务";
  return `开放 ${summary.open_task_count} 项，逾期 ${summary.overdue_task_count}，7 天内到期 ${summary.due_soon_task_count}`;
}

export function buildAdviserDashboardEmptyTips(payload?: AdviserDashboardResponse | null): string[] {
  if (!payload) return ["请选择年级或班级后加载班主任驾驶舱。"];
  const tips: string[] = [];
  if (payload.overview.student_count === 0) tips.push("当前范围没有学生，请先维护基础数据。");
  if (!payload.score_summary.imported) tips.push("当前范围没有成绩样本，成绩风险只显示数据缺口。");
  if (payload.growth_summary.total_records <= 0) tips.push("当前范围暂无成长档案记录，跟进建议会偏保守。");
  if (payload.planning_summary.students_without_goal_count > 0) {
    tips.push(`仍有 ${payload.planning_summary.students_without_goal_count} 名学生未建立升学规划目标。`);
  }
  return tips;
}

export function buildAdviserActionSummary(actions: AdviserActionItem[]): string {
  if (!actions.length) return "暂无行动项";
  return actions.map((item) => `${item.title} ${item.count}`).join(" / ");
}
