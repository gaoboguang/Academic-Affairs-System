export interface ImportFeedbackResult {
  message: string;
  total_rows?: number;
  success_rows?: number;
  failed_rows?: number;
  skipped_rows?: number;
  error_report_path?: string;
  error_preview?: string[];
  notice_preview?: string[];
}

export function resolveImportAlertType(result: ImportFeedbackResult): "success" | "warning" {
  return (result.failed_rows ?? 0) > 0 ? "warning" : "success";
}

export function buildImportSummary(result: ImportFeedbackResult): string {
  const totalRows = result.total_rows ?? 0;
  const successRows = result.success_rows ?? 0;
  const failedRows = result.failed_rows ?? 0;
  const skippedRows = result.skipped_rows ?? 0;
  return `共 ${totalRows} 行，成功 ${successRows} 行，失败 ${failedRows} 行，跳过 ${skippedRows} 行。`;
}

export function buildImportErrorReportUrl(path: string): string {
  return `/api/system/files?path=${encodeURIComponent(path)}`;
}
