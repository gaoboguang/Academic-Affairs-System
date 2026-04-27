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
