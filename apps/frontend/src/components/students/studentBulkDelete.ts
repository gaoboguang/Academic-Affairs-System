export interface StudentBulkDeleteAssociationCounts {
  score_count: number;
  score_snapshot_count: number;
  growth_record_count: number;
  teacher_comment_count: number;
  attachment_count: number;
  class_history_count: number;
  recommendation_count: number;
  volunteer_draft_count: number;
  gaokao_score_projection_count: number;
  pathway_profile_count: number;
  pathway_evaluation_count: number;
}

export interface StudentBulkDeletePreviewItem {
  student_id: number;
  student_no?: string | null;
  student_name?: string | null;
  current_class_id?: number | null;
  current_class_name?: string | null;
  status: "deletable" | "blocked";
  reason?: string | null;
  message: string;
  association_counts: StudentBulkDeleteAssociationCounts;
}

export interface StudentBulkDeletePreviewResponse {
  total: number;
  deletable_count: number;
  blocked_count: number;
  mode: "soft_delete";
  required_confirm_text: string;
  confirm_token: string;
  items: StudentBulkDeletePreviewItem[];
  warnings: StudentBulkDeletePreviewItem[];
  blocked: StudentBulkDeletePreviewItem[];
}

export interface StudentBulkDeleteExecuteItem {
  student_id: number;
  student_no?: string | null;
  student_name?: string | null;
  status: "success" | "blocked" | "failed";
  message: string;
  error_message?: string | null;
  association_counts: StudentBulkDeleteAssociationCounts;
}

export interface StudentBulkDeleteExecuteResponse {
  total: number;
  success_count: number;
  failed_count: number;
  blocked_count: number;
  status: "success" | "partially_failed" | "failed";
  mode: "soft_delete";
  message: string;
  audit_log_id?: number | null;
  items: StudentBulkDeleteExecuteItem[];
  success_items: StudentBulkDeleteExecuteItem[];
  failed_items: StudentBulkDeleteExecuteItem[];
  blocked: StudentBulkDeleteExecuteItem[];
}

const associationFields: Array<{
  key: keyof StudentBulkDeleteAssociationCounts;
  label: string;
}> = [
  { key: "score_count", label: "成绩记录" },
  { key: "score_snapshot_count", label: "成绩快照" },
  { key: "growth_record_count", label: "成长档案" },
  { key: "teacher_comment_count", label: "教师评语" },
  { key: "attachment_count", label: "附件" },
  { key: "class_history_count", label: "班级历史" },
  { key: "recommendation_count", label: "推荐记录" },
  { key: "volunteer_draft_count", label: "志愿草稿" },
  { key: "gaokao_score_projection_count", label: "高考预估" },
  { key: "pathway_profile_count", label: "升学画像" },
  { key: "pathway_evaluation_count", label: "路径评估" },
];

export function formatBulkDeleteAssociationSummary(
  counts: StudentBulkDeleteAssociationCounts,
): string[] {
  const summaries = associationFields.flatMap(({ key, label }) => {
    const count = counts[key] ?? 0;
    return count > 0 ? [`${label} ${count} 条`] : [];
  });
  return summaries.length ? summaries : ["暂无关联历史数据"];
}

export function canExecuteBulkDelete(
  preview: StudentBulkDeletePreviewResponse | null,
  confirmText: string,
): boolean {
  if (!preview || preview.deletable_count <= 0) return false;
  return confirmText.trim() === preview.required_confirm_text;
}

export function resolvePreviewStatusLabel(status: StudentBulkDeletePreviewItem["status"]): string {
  return status === "deletable" ? "可停用" : "已阻断";
}

export function resolvePreviewStatusType(
  status: StudentBulkDeletePreviewItem["status"],
): "success" | "danger" {
  return status === "deletable" ? "success" : "danger";
}

export function resolveExecuteStatusLabel(status: StudentBulkDeleteExecuteItem["status"]): string {
  const mapping: Record<StudentBulkDeleteExecuteItem["status"], string> = {
    success: "已停用",
    blocked: "已阻断",
    failed: "失败",
  };
  return mapping[status];
}

export function resolveExecuteStatusType(
  status: StudentBulkDeleteExecuteItem["status"],
): "success" | "danger" | "warning" {
  const mapping: Record<StudentBulkDeleteExecuteItem["status"], "success" | "danger" | "warning"> = {
    success: "success",
    blocked: "warning",
    failed: "danger",
  };
  return mapping[status];
}

export function formatBulkDeleteResultMessage(response: StudentBulkDeleteExecuteResponse): string {
  return `批量删除完成：成功 ${response.success_count} 名，失败 ${response.failed_count} 名，被阻断 ${response.blocked_count} 名。`;
}
