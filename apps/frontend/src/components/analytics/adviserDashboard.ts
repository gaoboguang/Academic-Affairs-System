export type AdviserRiskLevel = "urgent" | "follow_up" | "watch" | "normal";

export interface AttendanceRiskSummary {
  imported: boolean;
  total_records: number;
  late_count: number;
  early_leave_count: number;
  sick_leave_count: number;
  personal_leave_count: number;
  truancy_count: number;
}

export interface BehaviorRiskSummary {
  imported: boolean;
  total_records: number;
  positive_count: number;
  discipline_count: number;
  severe_count: number;
}

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
    attendance_status: string;
    behavior_status: string;
    absence_risk_count: number;
    behavior_risk_count: number;
    follow_up_count: number;
  };
  score_summary: {
    imported: boolean;
    sample_count: number;
    average_total_score?: number | null;
    low_score_count: number;
    decline_count: number;
  };
  attendance_summary: AttendanceRiskSummary;
  behavior_summary: BehaviorRiskSummary;
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

export function formatAttendanceSummary(summary: AttendanceRiskSummary): string {
  if (!summary.imported) return "未导入";
  const leaveCount = summary.sick_leave_count + summary.personal_leave_count;
  return `记录 ${summary.total_records} 条，迟到 ${summary.late_count}，请假 ${leaveCount}，旷课 ${summary.truancy_count}`;
}

export function formatBehaviorSummary(summary: BehaviorRiskSummary): string {
  if (!summary.imported) return "未导入";
  return `记录 ${summary.total_records} 条，表扬 ${summary.positive_count}，违纪/奖惩 ${summary.discipline_count}，高关注 ${summary.severe_count}`;
}

export function buildAdviserDashboardEmptyTips(payload?: AdviserDashboardResponse | null): string[] {
  if (!payload) return ["请选择年级或班级后加载班主任驾驶舱。"];
  const tips: string[] = [];
  if (payload.overview.student_count === 0) tips.push("当前范围没有学生，请先维护基础数据。");
  if (!payload.score_summary.imported) tips.push("当前范围没有成绩样本，成绩风险只显示数据缺口。");
  if (!payload.attendance_summary.imported) tips.push("考勤未导入，不会按 0 风险处理。");
  if (!payload.behavior_summary.imported) tips.push("行为记录未导入，不会按 0 风险处理。");
  return tips;
}

export function buildAdviserActionSummary(actions: AdviserActionItem[]): string {
  if (!actions.length) return "暂无行动项";
  return actions.map((item) => `${item.title} ${item.count}`).join(" / ");
}
