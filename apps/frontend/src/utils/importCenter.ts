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

export interface ImportCenterBackup {
  id: number;
  backup_name: string;
  file_path: string;
  file_size: number;
  created_at: string;
  status: string;
  download_url?: string | null;
}

export interface ImportCenterErrorItem {
  row_number?: number | null;
  field_name?: string | null;
  raw_value?: unknown;
  message: string;
  suggestion?: string | null;
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
  latest_backup?: ImportCenterBackup | null;
  templates: ImportCenterTemplate[];
  batches: ImportCenterBatch[];
}

export interface ImportCenterBatchDetail {
  batch: ImportCenterBatch;
  result_json?: Record<string, unknown> | null;
  audit_logs: ImportCenterAuditLog[];
  error_preview: string[];
  error_items: ImportCenterErrorItem[];
  notice_preview: string[];
  rollback_steps: string[];
}

export interface ImportCenterTrialRunStep {
  title: string;
  detail: string;
  actionLabel: string;
  path: string;
}

export const importCenterTrialRunSteps: ImportCenterTrialRunStep[] = [
  { title: "1. 备份当前主库", detail: "先保存当前数据状态，后续导入不支持无快照一键回滚。", actionLabel: "去备份", path: "/system-tools" },
  { title: "2. 导入/核验基础数据", detail: "确认学年学期、年级班级、学科课程等基础字典可匹配。", actionLabel: "基础数据", path: "/base-data" },
  { title: "3. 导入学生与教师", detail: "先维护学生学号、教师工号和班级归属，保证后续导入能匹配。", actionLabel: "学生中心", path: "/students" },
  { title: "4. 维护任教关系", detail: "确认教师、学期、年级、班级和学科关系，再导入成绩或课表。", actionLabel: "教师中心", path: "/teachers" },
  { title: "5. 创建考试并导入成绩", detail: "考试名称、科目、满分和统计口径确认后，再上传成绩表。", actionLabel: "考试成绩", path: "/exams" },
  { title: "6. 维护成长与规划", detail: "补充成长档案、升学规划目标和阶段任务，让学生跟进包有依据。", actionLabel: "学生中心", path: "/students" },
  { title: "7. 查看驾驶舱", detail: "进入班主任驾驶舱查看成绩波动、成长档案和规划任务跟进清单。", actionLabel: "分析中心", path: "/analytics" },
  { title: "8. 导出报表", detail: "确认分析口径后再导出班主任周报、学生跟进包或成绩报告。", actionLabel: "报表中心", path: "/reports" },
];

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
  const mutationParts = [
    batch.created_rows > 0 ? `新增 ${batch.created_rows} 行` : "",
    batch.updated_rows > 0 ? `更新 ${batch.updated_rows} 行` : "",
  ].filter(Boolean);
  const mutationSummary = mutationParts.length ? `，${mutationParts.join("，")}` : "";
  return `共 ${totalRows} 行，成功 ${successRows} 行，失败 ${failedRows} 行，跳过 ${skippedRows} 行${mutationSummary}`;
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

export function formatLatestBackupLabel(backup?: ImportCenterBackup | null): string {
  if (!backup) return "暂无备份记录";
  return `${backup.created_at} · ${backup.backup_name}`;
}

export function formatImportCenterErrorItem(item: ImportCenterErrorItem): string {
  const row = item.row_number ? `第 ${item.row_number} 行` : "未知行";
  const field = item.field_name ? ` / ${item.field_name}` : "";
  const rawValue = item.raw_value !== null && item.raw_value !== undefined && item.raw_value !== ""
    ? ` / 原值：${String(item.raw_value)}`
    : "";
  const suggestion = item.suggestion ? ` / 建议：${item.suggestion}` : "";
  return `${row}${field}${rawValue}：${item.message}${suggestion}`;
}
