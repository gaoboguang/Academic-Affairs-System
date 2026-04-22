import type { OptionItem } from "../../stores/reference";

export const ruleVersionStatusOptions = [
  { label: "启用", value: "active" },
  { label: "草稿", value: "draft" },
  { label: "归档", value: "archived" },
] as const;

export const templateTargetTypeOptions = [
  { label: "教师", value: "teacher" },
  { label: "班主任", value: "adviser" },
] as const;

export function semesterLabel(item: OptionItem): string {
  return item.academic_year_name ? `${item.academic_year_name} ${item.name}` : item.name;
}

export function formatTemplateTargetType(targetType: string): string {
  const mapping: Record<string, string> = {
    teacher: "教师",
    adviser: "班主任",
  };
  return mapping[targetType] ?? targetType;
}

export function formatEvaluationBatchStatus(status: string): string {
  const mapping: Record<string, string> = {
    completed: "已完成",
    partial_success: "部分成功",
    processing: "处理中",
    failed: "失败",
  };
  return mapping[status] ?? status;
}

export function evaluationBatchStatusType(status: string): "success" | "warning" | "danger" | "info" {
  if (status === "completed") return "success";
  if (status === "partial_success") return "warning";
  if (status === "failed") return "danger";
  return "info";
}

export function formatRuleVersionStatus(status: string): string {
  const mapping: Record<string, string> = {
    active: "启用",
    draft: "草稿",
    archived: "归档",
  };
  return mapping[status] ?? status;
}

export function ruleVersionStatusType(status: string): "success" | "info" | "warning" {
  if (status === "active") return "success";
  if (status === "draft") return "info";
  return "warning";
}

export function formatWeight(value?: Record<string, number> | null): string {
  if (!value || !Object.keys(value).length) return "-";
  return Object.entries(value)
    .map(([key, score]) => `${key}:${score}`)
    .join(" / ");
}

export function formatSignedValue(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined) return "-";
  const normalized = Number(value.toFixed(digits));
  if (normalized > 0) return `+${normalized}`;
  return String(normalized);
}

export function formatRankDelta(value: number | null | undefined): string {
  if (value === null || value === undefined) return "-";
  if (value > 0) return `提升 ${value}`;
  if (value < 0) return `下降 ${Math.abs(value)}`;
  return "持平";
}

export function deltaClass(value: number | null | undefined): string {
  if (value === null || value === undefined) return "comparison-flat";
  if (value > 0) return "comparison-up";
  if (value < 0) return "comparison-down";
  return "comparison-flat";
}
