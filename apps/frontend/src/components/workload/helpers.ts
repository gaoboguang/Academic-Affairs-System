import type { OptionItem } from "../../stores/reference";
import type { RuleVersionItem, TimetableBatchItem, TimetableEntryItem } from "./types";

export const dimensionOptions = [
  { value: "subject", label: "学科" },
  { value: "grade", label: "年级" },
  { value: "class_type", label: "班型" },
  { value: "course_type", label: "课程类型" },
  { value: "class_size", label: "班额" },
  { value: "head_teacher", label: "班主任附加量" },
] as const;

export const ruleVersionStatusOptions = [
  { label: "启用", value: "active" },
  { label: "草稿", value: "draft" },
] as const;

export function formatSemesterLabel(item: OptionItem): string {
  return item.academic_year_name ? `${item.academic_year_name} ${item.name}` : item.name;
}

export function batchLabel(item: TimetableBatchItem): string {
  return `${item.import_time} | ${item.source_filename ?? "未命名"} | 未匹配 ${item.unresolved_count}`;
}

export function formatRuleVersionStatus(status: string): string {
  const mapping: Record<string, string> = {
    active: "启用",
    draft: "草稿",
  };
  return mapping[status] ?? status;
}

export function ruleLabel(item: RuleVersionItem): string {
  const suffix = item.is_default ? "默认" : formatRuleVersionStatus(item.status);
  return `${item.name} | ${item.semester_name ?? "通用"} | ${suffix}`;
}

export function formatBatchStatus(status: string): string {
  const mapping: Record<string, string> = {
    completed: "已完成",
    completed_with_unresolved: "待修正",
    processing: "处理中",
    failed: "失败",
  };
  return mapping[status] ?? status;
}

export function batchTagType(status: string): "success" | "warning" | "info" | "danger" {
  if (status === "completed") return "success";
  if (status === "completed_with_unresolved") return "warning";
  if (status === "failed") return "danger";
  return "info";
}

export function ruleStatusTagType(status: string): "success" | "info" | "warning" {
  if (status === "active") return "success";
  if (status === "draft") return "info";
  return "warning";
}

export function formatWeekRule(row: TimetableEntryItem): string {
  if (row.week_rule === "all") return "全周";
  if (row.week_rule === "odd") return "单周";
  if (row.week_rule === "even") return "双周";
  if (row.week_rule === "custom" && row.week_list_json?.length) {
    return `指定周 ${row.week_list_json.join(",")}`;
  }
  return row.week_rule;
}

export function formatCourseTypeLabel(
  code?: string | null,
  fallback?: string | null,
  courseTypeOptions: OptionItem[] = [],
): string {
  if (!code) return fallback ?? "-";
  const match = courseTypeOptions.find((item) => item.code === code);
  return match ? match.name : (fallback ?? code);
}

export function formatMonthlyHours(value?: Record<string, number> | null): string {
  if (!value) return "-";
  const items = Object.entries(value);
  if (!items.length) return "-";
  return items.map(([month, hours]) => `${month}: ${hours}`).join(" / ");
}

export function formatBreakdown(value?: Record<string, number>): string {
  if (!value) return "-";
  return Object.entries(value)
    .map(([key, score]) => `${key}=${score}`)
    .join(" × ");
}
