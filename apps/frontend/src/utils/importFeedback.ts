export interface ImportFeedbackResult {
  message: string;
  status?: string;
  total_rows?: number;
  success_rows?: number;
  failed_rows?: number;
  skipped_rows?: number;
  created_rows?: number;
  updated_rows?: number;
  error_report_path?: string;
  error_preview?: string[];
  notice_preview?: string[];
}

export type ImportFeedbackAlertType = "success" | "warning" | "error";
export type ImportStatusTagType = "success" | "warning" | "info" | "danger";

const statusAliases: Record<string, string> = {
  processing: "running",
  completed: "success",
  completed_with_unresolved: "partially_failed",
  partial_success: "partially_failed",
};

export function normalizeImportStatus(status?: string | null): string {
  if (!status) return "success";
  return statusAliases[status] ?? status;
}

export function resolveImportAlertType(result: ImportFeedbackResult): ImportFeedbackAlertType {
  const status = normalizeImportStatus(result.status);
  if (status === "failed" || ((result.success_rows ?? 0) === 0 && (result.failed_rows ?? 0) > 0)) return "error";
  if (status === "partially_failed" || (result.failed_rows ?? 0) > 0) return "warning";
  return "success";
}

export function formatImportStatus(status?: string | null): string {
  const mapping: Record<string, string> = {
    pending: "待开始",
    running: "处理中",
    success: "成功",
    failed: "失败",
    partially_failed: "部分成功",
    rolled_back: "已回滚",
  };
  const normalized = normalizeImportStatus(status);
  return mapping[normalized] ?? normalized;
}

export function importStatusTagType(status?: string | null): ImportStatusTagType {
  const normalized = normalizeImportStatus(status);
  if (normalized === "success") return "success";
  if (normalized === "partially_failed") return "warning";
  if (normalized === "failed") return "danger";
  return "info";
}

export function buildImportSummary(result: ImportFeedbackResult): string {
  const totalRows = result.total_rows ?? 0;
  const successRows = result.success_rows ?? 0;
  const failedRows = result.failed_rows ?? 0;
  const skippedRows = result.skipped_rows ?? 0;
  const createdRows = result.created_rows ?? 0;
  const updatedRows = result.updated_rows ?? 0;
  const mutationSummary = createdRows > 0 || updatedRows > 0
    ? `新增 ${createdRows} 行，更新 ${updatedRows} 行。`
    : "";
  return `共 ${totalRows} 行，成功 ${successRows} 行，失败 ${failedRows} 行，跳过 ${skippedRows} 行。${mutationSummary}`;
}

export function buildImportErrorReportUrl(path: string): string {
  return `/api/system/files?path=${encodeURIComponent(path)}`;
}
