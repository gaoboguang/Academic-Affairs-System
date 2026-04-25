import { describe, expect, it } from "vitest";

import {
  buildImportCenterErrorReportUrl,
  buildImportCenterRowSummary,
  formatImportCenterDetails,
  importCenterStatusType,
  type ImportCenterBatch,
} from "../src/utils/importCenter";

const baseBatch: ImportCenterBatch = {
  id: "import_job:1",
  numeric_id: 1,
  source_type: "import_job",
  source_type_label: "通用导入任务",
  job_type: "scores",
  job_type_label: "成绩导入",
  source_filename: "scores.xlsx",
  status: "partially_failed",
  started_at: "2026-04-24 09:30:00",
  finished_at: "2026-04-24 09:31:00",
  total_rows: 12,
  success_rows: 10,
  failed_rows: 2,
  skipped_rows: 0,
  created_rows: 0,
  updated_rows: 10,
  error_report_path: "data/logs/score_import_errors.xlsx",
  business_path: "/exams",
  template_download_url: "/api/system/files?path=data%2Ftemplates%2Fexam_scores_import_template.xlsx",
  rollback_supported: false,
  rollback_hint: "请通过备份或重新导入修正。",
  detail_summary: "共 12 行，成功 10 行，失败 2 行。",
};

describe("import center helpers", () => {
  it("builds readable row summaries", () => {
    expect(buildImportCenterRowSummary(baseBatch)).toBe("共 12 行，成功 10 行，失败 2 行，跳过 0 行");
  });

  it("uses unified status tag types", () => {
    expect(importCenterStatusType("partially_failed")).toBe("warning");
    expect(importCenterStatusType("failed")).toBe("danger");
  });

  it("builds error report urls only when present", () => {
    expect(buildImportCenterErrorReportUrl(baseBatch)).toBe(
      "/api/system/files?path=data%2Flogs%2Fscore_import_errors.xlsx",
    );
    expect(buildImportCenterErrorReportUrl({ ...baseBatch, error_report_path: null })).toBeNull();
  });

  it("formats compact audit details", () => {
    expect(formatImportCenterDetails({ batch_id: 1, failed_rows: 2 })).toBe("batch_id=1 / failed_rows=2");
    expect(formatImportCenterDetails(null)).toBe("-");
  });
});
