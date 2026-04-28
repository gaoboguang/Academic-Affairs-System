export interface DashboardBackupSummary {
  backup_name: string;
  created_at?: string | null;
  status?: string | null;
  file_size?: number | null;
}

export interface DashboardDataHealthSummary {
  status: string;
  label: string;
  summary: string;
  p0_gap_count: number;
  warning_count: number;
  blocking_count: number;
  gaps: string[];
}

export interface DashboardDecisionSummary {
  student_total: number;
  teacher_total: number;
  exam_total: number;
  score_record_total: number;
  latest_backup?: DashboardBackupSummary | null;
  data_health?: DashboardDataHealthSummary | null;
  planning_summary?: {
    open_task_count: number;
    overdue_task_count: number;
    due_soon_task_count: number;
    students_without_goal_count: number;
    volunteer_draft_without_review_count: number;
    material_gap_without_due_count: number;
  } | null;
}

export interface DashboardNextStep {
  code: string;
  title: string;
  detail: string;
  actionLabel: string;
  path: string;
  severity: "danger" | "warning" | "info";
}

export function buildDashboardNextSteps(summary: DashboardDecisionSummary): DashboardNextStep[] {
  const steps: DashboardNextStep[] = [];

  if (summary.score_record_total === 0) {
    steps.push({
      code: "score_record_empty",
      title: "还没有成绩记录",
      detail: "当前可以维护基础数据，但学生、班级、年级和教师分析需要先导入成绩。",
      actionLabel: "导入考试成绩",
      path: "/exams",
      severity: "warning",
    });
  }

  if (summary.teacher_total < 5) {
    steps.push({
      code: "teacher_too_few",
      title: "教师台账样本偏少",
      detail: "教师数量偏少时，任教分析、工作量和评教对比只能做流程验证。",
      actionLabel: "维护教师",
      path: "/teachers",
      severity: "info",
    });
  }

  const academicGaps = summary.data_health?.gaps.filter((item) => item.includes("教务")) ?? [];
  if (academicGaps.length > 0) {
    steps.push({
      code: "adviser_data_gap",
      title: "班主任驾驶舱数据不完整",
      detail: academicGaps.slice(0, 2).join("；"),
      actionLabel: "补齐导入数据",
      path: "/import-center",
      severity: "warning",
    });
  }

  if (summary.data_health && (summary.data_health.status !== "pass" || summary.data_health.p0_gap_count > 0)) {
    steps.push({
      code: "gaokao_data_warning",
      title: "高考数据仍有风险提示",
      detail:
        summary.data_health.p0_gap_count > 0
          ? `当前还有 ${summary.data_health.p0_gap_count} 条 P0 数据缺口，推荐和志愿结果需要保留人工复核。`
          : summary.data_health.summary,
      actionLabel: "查看高考数据",
      path: "/gaokao-data",
      severity: summary.data_health.status === "blocked" ? "danger" : "warning",
    });
  }

  if (summary.planning_summary?.overdue_task_count) {
    steps.push({
      code: "planning_overdue_tasks",
      title: "升学规划任务已逾期",
      detail: `当前有 ${summary.planning_summary.overdue_task_count} 项规划任务超过截止日期，建议先处理材料、章程复核和阶段复盘。`,
      actionLabel: "查看学生规划",
      path: "/students",
      severity: "warning",
    });
  } else if (summary.planning_summary?.volunteer_draft_without_review_count) {
    steps.push({
      code: "planning_volunteer_review_gap",
      title: "志愿草稿缺少复核任务",
      detail: `当前有 ${summary.planning_summary.volunteer_draft_without_review_count} 份志愿草稿还没有生成章程复核任务。`,
      actionLabel: "进入升学方案",
      path: "/gaokao-pathways",
      severity: "info",
    });
  } else if (summary.planning_summary?.material_gap_without_due_count) {
    steps.push({
      code: "planning_material_due_gap",
      title: "材料缺口没有截止日期",
      detail: `当前有 ${summary.planning_summary.material_gap_without_due_count} 项材料任务缺少截止日期，容易丢失跟进节奏。`,
      actionLabel: "查看学生规划",
      path: "/students",
      severity: "info",
    });
  }

  if (!summary.latest_backup) {
    steps.push({
      code: "backup_missing",
      title: "还没有系统备份",
      detail: "导入真实数据、修复数据或恢复前，建议先创建一个本地备份包。",
      actionLabel: "创建备份",
      path: "/system-tools",
      severity: "warning",
    });
  }

  if (steps.length === 0) {
    steps.push({
      code: "ready_for_trial",
      title: "可以进入试用流程",
      detail: "关键入口已有数据基础，建议按导入中心、分析中心、报表中心的顺序做一次完整复核。",
      actionLabel: "进入导入中心",
      path: "/import-center",
      severity: "info",
    });
  }

  return steps;
}

export function formatDashboardBackupLabel(backup?: DashboardBackupSummary | null): string {
  if (!backup) return "未创建";
  if (backup.created_at) return formatDateTime(backup.created_at);
  return backup.backup_name;
}

export function formatDataHealthCardValue(dataHealth?: DashboardDataHealthSummary | null): string {
  if (!dataHealth) return "未检查";
  if (dataHealth.p0_gap_count > 0) return `${dataHealth.p0_gap_count} 条`;
  return dataHealth.label;
}

export function formatDateTime(value?: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}
