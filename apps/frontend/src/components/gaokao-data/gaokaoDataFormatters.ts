import { formatGaokaoCollegeEvidenceOptionLabel } from "../../utils/gaokaoEvidence";
import type {
  GaokaoDataHealthTable,
  GaokaoDataHealthType,
  GaokaoReviewGroupMember,
} from "./gaokaoDataTypes";

export function formatSourceMode(value?: string | null): string {
  const mapping: Record<string, string> = {
    doc_baseline: "同步板冻结基线",
    db_rc1_live: "本地高考只读库",
    app_model_fallback: "应用侧主档补充",
    mixed_read_only: "混合只读视图",
  };
  return (value ? mapping[value] : null) ?? "待确认";
}

export function formatCoverage(total: number, rate?: number | null): string {
  if (rate === null || rate === undefined) {
    return String(total);
  }
  return `${total} / ${rate}%`;
}

export function formatStatus(value?: string | null): string {
  const mapping: Record<string, string> = {
    success: "成功",
    processing: "处理中",
    frozen: "冻结",
    failed: "失败",
  };
  return (value ? mapping[value] : null) ?? value ?? "未知";
}

export function formatMonitorStatus(value?: string | null): string {
  const mapping: Record<string, string> = {
    ok: "正常",
    gap: "需关注",
    missing: "缺失",
    ready: "已接入",
    imported: "已导入",
    published: "已公开",
    pending_official_release: "待官方发布",
    not_applicable: "当前不适用",
    manual_review_required: "需人工核验",
    partial: "部分可用",
    waiting: "待同步",
    empty: "暂无数据",
    no_year_column: "缺年份列",
  };
  return (value ? mapping[value] : null) ?? "待确认";
}

export function statusTagType(value?: string | null): "success" | "info" | "warning" | "danger" | undefined {
  if (["ok", "ready", "success", "imported"].includes(value ?? "")) return "success";
  if (["gap", "partial", "processing", "no_year_column", "published", "manual_review_required"].includes(value ?? "")) return "warning";
  if (["waiting", "frozen", "empty", "pending_official_release", "not_applicable"].includes(value ?? "")) return "info";
  if (["failed", "missing"].includes(value ?? "")) return "danger";
  return undefined;
}

export function deliveryTagType(value?: string | null): "success" | "info" | "warning" | "danger" | undefined {
  if (value === "pass") return "success";
  if (value === "warning") return "warning";
  if (value === "blocked") return "danger";
  return "info";
}

export function riskLevelTagType(value?: string | null): "success" | "info" | "warning" | "danger" | undefined {
  if (value === "normal") return "success";
  if (value === "warning") return "warning";
  if (value === "blocking") return "danger";
  return "info";
}

export function coverageToneTagType(value: "success" | "warning" | "danger" | "info"): "success" | "info" | "warning" | "danger" {
  return value;
}

export function formatYearList(years?: number[]): string {
  return years?.length ? years.join("、") : "无";
}

export function formatDistribution(items?: GaokaoDataHealthType[], emptyText = "无"): string {
  return items?.length ? items.map((item) => `${item.label || item.key}：${item.count}`).join("；") : emptyText;
}

export function formatFallbackLabels(items?: string[]): string {
  return items?.length ? items.join("；") : "无初筛兜底";
}

export function formatTableNotes(row: GaokaoDataHealthTable): string {
  const parts = [...(row.notes || [])];
  if (row.explanation) {
    parts.unshift(row.explanation);
  }
  return parts.length ? parts.join("；") : "-";
}

export function formatReviewFilter(value?: string | null): string {
  const mapping: Record<string, string> = {
    all: "全部",
    pending_manual_review: "待人工复核",
    pending_manual_review_with_official_candidate: "待人工复核（已有官方候选）",
    unresolved: "仍未解决",
  };
  return (value ? mapping[value] : null) ?? "全部";
}

export function formatReviewFocus(value?: string | null): string {
  const mapping: Record<string, string> = {
    all: "全部队列",
    high_priority: "高优先",
    missing_chapter: "缺章程",
    missing_recruit_site: "缺招生网",
    duplicate_or_same_name: "重复 / 同名组",
    unresolved: "仍未解决",
  };
  return (value ? mapping[value] : null) ?? "全部队列";
}

export function formatReviewSort(value?: string | null): string {
  const mapping: Record<string, string> = {
    priority_desc: "优先级优先",
    updated_desc: "最近更新时间",
  };
  return (value ? mapping[value] : null) ?? "优先级优先";
}

export function reviewPriorityTagType(value?: string | null): "success" | "warning" | "danger" | undefined {
  if (value === "high") return "danger";
  if (value === "medium") return "warning";
  if (value === "low") return "success";
  return undefined;
}

export function comparisonFieldTagType(value?: string | null): "success" | "info" | "warning" | "danger" | undefined {
  if (value === "mixed") return "warning";
  if (value === "partial") return "info";
  if (value === "empty") return "danger";
  if (value === "same") return "success";
  return undefined;
}

export function formatGroupMemberLabel(item: GaokaoReviewGroupMember): string {
  return formatGaokaoCollegeEvidenceOptionLabel({
    college_id: item.college_id ?? 0,
    college_name: item.college_name,
    college_code: item.college_code,
    province: item.province,
    review_status: item.review_status,
  });
}

export function formatGroupType(value?: string | null): string {
  if (value === "duplicate") return "重复组";
  if (value === "same_name") return "同名跨站组";
  return "待确认分组";
}

export function formatGroupCompareCell(value?: string | null): string {
  if (!value) return "待补齐";
  try {
    const parsed = new URL(value);
    return parsed.host || value;
  } catch {
    return value;
  }
}

export function formatGroupSourceUrlCell(value?: string | null): string {
  if (!value) return "待补齐";
  try {
    const parsed = new URL(value);
    const pathname = parsed.pathname === "/" ? "" : parsed.pathname.replace(/\/$/, "");
    return `${parsed.host}${pathname}`;
  } catch {
    return value;
  }
}

export function formatGroupChapterCell(member: GaokaoReviewGroupMember): string {
  const chapterValue = member.chapter_url || member.fallback_url || member.effective_chapter_url;
  if (!chapterValue) return "待补齐";
  const label = formatGroupCompareCell(chapterValue);
  if (!member.chapter_url && member.fallback_url) {
    return `${label}（备用）`;
  }
  return label;
}
