import { describe, expect, it } from "vitest";

import {
  buildImportErrorReportUrl,
  buildImportSummary,
  formatImportStatus,
  importStatusTagType,
  resolveImportAlertType,
} from "../src/utils/importFeedback";

describe("import feedback", () => {
  it("builds warning summaries for partial failures", () => {
    expect(
      buildImportSummary({
        message: "学生导入完成，成功 0 条，失败 803 条。",
        total_rows: 803,
        success_rows: 0,
        failed_rows: 803,
        skipped_rows: 0,
      }),
    ).toBe("共 803 行，成功 0 行，失败 803 行，跳过 0 行。");
    expect(
      resolveImportAlertType({
        message: "学生导入完成，成功 0 条，失败 803 条。",
        failed_rows: 803,
      }),
    ).toBe("error");
  });

  it("formats canonical and legacy import statuses", () => {
    expect(formatImportStatus("partial_success")).toBe("部分成功");
    expect(formatImportStatus("partially_failed")).toBe("部分成功");
    expect(importStatusTagType("completed_with_unresolved")).toBe("warning");
  });

  it("includes created and updated rows when available", () => {
    expect(
      buildImportSummary({
        message: "教师导入完成。",
        total_rows: 3,
        success_rows: 3,
        failed_rows: 0,
        skipped_rows: 0,
        created_rows: 2,
        updated_rows: 1,
      }),
    ).toBe("共 3 行，成功 3 行，失败 0 行，跳过 0 行。新增 2 行，更新 1 行。");
  });

  it("builds safe runtime download paths for error reports", () => {
    expect(buildImportErrorReportUrl("data/logs/student_import_errors.xlsx")).toBe(
      "/api/system/files?path=data%2Flogs%2Fstudent_import_errors.xlsx",
    );
  });
});
