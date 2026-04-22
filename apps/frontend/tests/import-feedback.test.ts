import { describe, expect, it } from "vitest";

import { buildImportErrorReportUrl, buildImportSummary, resolveImportAlertType } from "../src/utils/importFeedback";

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
    ).toBe("warning");
  });

  it("builds safe runtime download paths for error reports", () => {
    expect(buildImportErrorReportUrl("data/logs/student_import_errors.xlsx")).toBe(
      "/api/system/files?path=data%2Flogs%2Fstudent_import_errors.xlsx",
    );
  });
});
