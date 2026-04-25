import { buildImportErrorReportUrl, formatImportStatus, importStatusTagType } from "./importFeedback";

export interface ImportCenterSummary {
  total_batches: number;
  failed_batches: number;
  partial_batches: number;
  error_report_count: number;
}

export interface ImportCenterTemplate {
  job_type: string;
  job_type_label: string;
  template_name: string;
  file_name: string;
  download_url: string;
  business_path: string;
  guidance: string;
}

export interface ImportCenterBatch {
  id: string;
  numeric_id: number;
  source_type: string;
  source_type_label: string;
  job_type: string;
  job_type_label: string;
  source_filename?: string | null;
  status: string;
  started_at?: string | null;
  finished_at?: string | null;
  total_rows?: number | null;
  success_rows?: number | null;
  failed_rows?: number | null;
  skipped_rows: number;
  created_rows: number;
  updated_rows: number;
  error_report_path?: string | null;
  business_path: string;
  template_download_url?: string | null;
  rollback_supported: boolean;
  rollback_hint: string;
  detail_summary: string;
}

export interface ImportCenterAuditLog {
  id: number;
  module: string;
  action: string;
  target_type?: string | null;
  target_id?: string | null;
  detail_json?: Record<string, unknown> | null;
  created_at: string;
}

export interface ImportCenterResponse {
  generated_at: string;
  summary: ImportCenterSummary;
  templates: ImportCenterTemplate[];
  batches: ImportCenterBatch[];
}

export interface ImportCenterBatchDetail {
  batch: ImportCenterBatch;
  result_json?: Record<string, unknown> | null;
  audit_logs: ImportCenterAuditLog[];
  error_preview: string[];
  notice_preview: string[];
  rollback_steps: string[];
}

export function formatImportCenterStatus(status: string): string {
  return formatImportStatus(status);
}

export function importCenterStatusType(status: string): "success" | "warning" | "danger" | "info" {
  return importStatusTagType(status);
}

export function buildImportCenterRowSummary(batch: ImportCenterBatch): string {
  const totalRows = batch.total_rows ?? 0;
  const successRows = batch.success_rows ?? 0;
  const failedRows = batch.failed_rows ?? 0;
  const skippedRows = batch.skipped_rows ?? 0;
  return `共 ${totalRows} 行，成功 ${successRows} 行，失败 ${failedRows} 行，跳过 ${skippedRows} 行`;
}

export function buildImportCenterErrorReportUrl(batch: ImportCenterBatch): string | null {
  return batch.error_report_path ? buildImportErrorReportUrl(batch.error_report_path) : null;
}

export function formatImportCenterDetails(value?: Record<string, unknown> | null): string {
  if (!value) return "-";
  return Object.entries(value)
    .filter(([, item]) => item !== null && item !== undefined && item !== "")
    .slice(0, 8)
    .map(([key, item]) => `${key}=${Array.isArray(item) ? item.join(",") : String(item)}`)
    .join(" / ") || "-";
}
