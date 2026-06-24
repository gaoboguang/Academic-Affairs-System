import type { VolunteerDraftComparisonEntry, VolunteerWorkbenchCandidate, VolunteerWorkbenchRuleAlert } from "./types";

export type VolunteerEmploymentMatchStrength = "core" | "high" | "medium" | "transferable" | "pending";
export type VolunteerEmploymentHintStatus = "yes" | "not_explicit" | "pending";

export function resultTypeLabel(value: string): string {
  const mapping: Record<string, string> = {
    challenge: "冲刺",
    steady: "稳妥",
    safe: "保底",
  };
  return mapping[value] ?? value;
}

export function resultTagType(value: string): "danger" | "warning" | "success" | "info" {
  const mapping: Record<string, "danger" | "warning" | "success" | "info"> = {
    challenge: "danger",
    steady: "warning",
    safe: "success",
  };
  return mapping[value] ?? "info";
}

export function formatStudentType(value?: string | null): string {
  if (!value) return "-";
  const mapping: Record<string, string> = {
    general: "普通生",
    repeat: "复读生",
    art: "艺体生",
    sports: "体育生",
  };
  return mapping[value] ?? value;
}

export function emptyResultGroupCopy(label: string): string {
  return `当前草稿里还没有${label}。`;
}

export function buildCodeMeta(
  candidate: Pick<VolunteerWorkbenchCandidate, "college_code_snapshot" | "major_code_snapshot" | "major_group_code">,
): string {
  const segments: string[] = [];
  if (candidate.college_code_snapshot) {
    segments.push(`院校代码 ${candidate.college_code_snapshot}`);
  }
  if (candidate.major_code_snapshot) {
    segments.push(`专业代码 ${candidate.major_code_snapshot}`);
  }
  if (candidate.major_group_code) {
    segments.push(`专业组 ${candidate.major_group_code}`);
  }
  return segments.join(" / ");
}

export function formatComparisonType(value?: VolunteerDraftComparisonEntry["currentType"]): string {
  if (!value) return "-";
  return resultTypeLabel(value);
}

export function formatComparisonOrderChange(entry: VolunteerDraftComparisonEntry): string {
  return `当前第 ${entry.currentOrder ?? "-"} 位，对比稿第 ${entry.compareOrder ?? "-"} 位`;
}

export function formatComparisonTypeChange(entry: VolunteerDraftComparisonEntry): string {
  return `${formatComparisonType(entry.currentType)} / 对比稿 ${formatComparisonType(entry.compareType)}`;
}

export function formatEmploymentMatchStrength(value: VolunteerEmploymentMatchStrength): string {
  const mapping = {
    core: "核心相关",
    high: "强相关",
    medium: "一般相关",
    transferable: "可转化相关",
    pending: "待维护",
  } as const;
  return mapping[value];
}

export function employmentMatchTagType(value: VolunteerEmploymentMatchStrength): "success" | "warning" | "info" {
  const mapping = {
    core: "success",
    high: "success",
    medium: "warning",
    transferable: "warning",
    pending: "info",
  } as const;
  return mapping[value];
}

export function formatEmploymentHintStatus(value: VolunteerEmploymentHintStatus): string {
  const mapping = {
    yes: "建议关注",
    not_explicit: "未见明确提示",
    pending: "待维护",
  } as const;
  return mapping[value];
}

export function employmentHintTagType(value: VolunteerEmploymentHintStatus): "warning" | "info" {
  const mapping = {
    yes: "warning",
    not_explicit: "info",
    pending: "info",
  } as const;
  return mapping[value];
}

export function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", { hour12: false });
}

export function normalizeAlertLevel(value: string): "warning" | "info" {
  return value === "warning" ? "warning" : "info";
}

export function alertTagType(value: string): "warning" | "info" {
  return normalizeAlertLevel(value);
}

export function alertLevelLabel(value: VolunteerWorkbenchRuleAlert["level"]): string {
  return value === "warning" ? "需人工复核" : "已自动回退";
}
