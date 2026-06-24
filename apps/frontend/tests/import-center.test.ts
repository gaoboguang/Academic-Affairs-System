import { describe, expect, it } from "vitest";

import {
  buildImportCenterErrorReportUrl,
  buildImportCenterRowSummary,
  formatImportCenterDetails,
  formatImportCenterErrorItem,
  formatLatestBackupLabel,
  importCenterStatusType,
  importCenterTrialRunSteps,
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
    expect(buildImportCenterRowSummary(baseBatch)).toBe("共 12 行，成功 10 行，失败 2 行，跳过 0 行，更新 10 行");
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

  it("formats latest backup and structured error items for non-technical review", () => {
    expect(formatLatestBackupLabel(null)).toBe("暂无备份记录");
    expect(formatLatestBackupLabel({
      id: 1,
      backup_name: "trial.zip",
      file_path: "data/backups/trial.zip",
      file_size: 128,
      created_at: "2026-04-27T09:00:00",
      status: "success",
    })).toContain("trial.zip");
    expect(formatImportCenterErrorItem({
      row_number: 3,
      field_name: "学号",
      raw_value: "2026999",
      message: "学生不存在",
      suggestion: "请先维护学生，或核对学号。",
    })).toBe("第 3 行 / 学号 / 原值：2026999：学生不存在 / 建议：请先维护学生，或核对学号。");
  });

  it("keeps the trial run guide in the expected school-data order", () => {
    expect(importCenterTrialRunSteps.map((item) => item.title)).toEqual([
      "1. 备份当前主库",
      "2. 导入/核验基础数据",
      "3. 导入学生与教师",
      "4. 维护任教关系",
      "5. 创建考试并导入成绩",
      "6. 维护成长与规划",
      "7. 查看驾驶舱",
      "8. 导出报表",
    ]);
  });

  it("models the pathway profile template as a student-center upload entry", () => {
    const pathwayProfileBatch: ImportCenterBatch = {
      ...baseBatch,
      job_type: "pathway_profiles",
      job_type_label: "升学画像导入",
      business_path: "/students",
      template_download_url: "/api/system/files?path=data%2Ftemplates%2Fstudent_pathway_profiles_import_template.xlsx",
    };

    expect(pathwayProfileBatch.job_type_label).toBe("升学画像导入");
    expect(pathwayProfileBatch.business_path).toBe("/students");
    expect(pathwayProfileBatch.template_download_url).toContain("student_pathway_profiles_import_template.xlsx");
  });
});
