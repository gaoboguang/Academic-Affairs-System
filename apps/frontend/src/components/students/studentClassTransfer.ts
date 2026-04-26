export interface ClassTransferPreviewItem {
  student_id: number;
  student_no?: string | null;
  student_name?: string | null;
  from_grade_id?: number | null;
  from_grade_name?: string | null;
  from_class_id?: number | null;
  from_class_name?: string | null;
  to_grade_id?: number | null;
  to_grade_name?: string | null;
  to_class_id?: number | null;
  to_class_name?: string | null;
  status: "transferable" | "blocked";
  reason?: string | null;
  message: string;
  warnings: string[];
}

export interface ClassTransferPreviewResponse {
  total: number;
  transferable_count: number;
  blocked_count: number;
  target_class_id: number;
  target_class_name: string;
  target_grade_id?: number | null;
  target_grade_name?: string | null;
  effective_on: string;
  required_confirm_text: string;
  confirm_token: string;
  items: ClassTransferPreviewItem[];
  warnings: ClassTransferPreviewItem[];
  blocked: ClassTransferPreviewItem[];
}

export interface ClassTransferExecuteItem {
  student_id: number;
  batch_item_id?: number | null;
  student_no?: string | null;
  student_name?: string | null;
  from_grade_id?: number | null;
  from_grade_name?: string | null;
  from_class_id?: number | null;
  from_class_name?: string | null;
  to_grade_id?: number | null;
  to_grade_name?: string | null;
  to_class_id?: number | null;
  to_class_name?: string | null;
  status: "success" | "blocked" | "failed";
  message: string;
  error_message?: string | null;
}

export interface ClassTransferExecuteResponse {
  total: number;
  success_count: number;
  failed_count: number;
  blocked_count: number;
  status: "success" | "partially_failed" | "failed";
  message: string;
  batch_id?: number | null;
  audit_log_id?: number | null;
  items: ClassTransferExecuteItem[];
  success_items: ClassTransferExecuteItem[];
  failed_items: ClassTransferExecuteItem[];
  blocked: ClassTransferExecuteItem[];
}

export interface ClassTransferHistoryItem {
  event_type: "class_transfer";
  title: string;
  summary: string;
  batch_id: number;
  item_id: number;
  student_id: number;
  student_no?: string | null;
  student_name?: string | null;
  from_grade_id?: number | null;
  from_grade_name?: string | null;
  from_class_id?: number | null;
  from_class_name?: string | null;
  to_grade_id?: number | null;
  to_grade_name?: string | null;
  to_class_id?: number | null;
  to_class_name?: string | null;
  effective_on: string;
  reason: string;
  note?: string | null;
  operator_name?: string | null;
  status: string;
  error_message?: string | null;
  created_at: string;
}

export function canExecuteClassTransfer(
  preview: ClassTransferPreviewResponse | null,
  confirmText: string,
): boolean {
  if (!preview || preview.transferable_count <= 0) return false;
  return confirmText.trim() === preview.required_confirm_text;
}

export function resolveClassTransferPreviewStatusLabel(status: ClassTransferPreviewItem["status"]): string {
  return status === "transferable" ? "可调班" : "已阻断";
}

export function resolveClassTransferPreviewStatusType(
  status: ClassTransferPreviewItem["status"],
): "success" | "danger" {
  return status === "transferable" ? "success" : "danger";
}

export function resolveClassTransferExecuteStatusLabel(status: ClassTransferExecuteItem["status"]): string {
  const mapping: Record<ClassTransferExecuteItem["status"], string> = {
    success: "已调班",
    blocked: "已阻断",
    failed: "失败",
  };
  return mapping[status];
}

export function resolveClassTransferExecuteStatusType(
  status: ClassTransferExecuteItem["status"],
): "success" | "danger" | "warning" {
  const mapping: Record<ClassTransferExecuteItem["status"], "success" | "danger" | "warning"> = {
    success: "success",
    blocked: "warning",
    failed: "danger",
  };
  return mapping[status];
}

export function formatClassTransferRoute(
  item: Pick<
    ClassTransferHistoryItem | ClassTransferPreviewItem | ClassTransferExecuteItem,
    "from_grade_name" | "from_class_name" | "to_grade_name" | "to_class_name"
  >,
): string {
  const fromLabel = [item.from_grade_name, item.from_class_name].filter(Boolean).join(" ") || "未分班";
  const toLabel = [item.to_grade_name, item.to_class_name].filter(Boolean).join(" ") || "未指定班级";
  return `${fromLabel} -> ${toLabel}`;
}

export function formatClassTransferEventSummary(item: ClassTransferHistoryItem): string {
  return `${item.effective_on} 班级调整：${formatClassTransferRoute(item)}，原因：${item.reason}。`;
}

export function formatClassTransferResultMessage(response: ClassTransferExecuteResponse): string {
  return `批量调班完成：成功 ${response.success_count} 名，失败 ${response.failed_count} 名，被阻断 ${response.blocked_count} 名。`;
}
