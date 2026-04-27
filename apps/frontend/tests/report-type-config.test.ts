import { describe, expect, it } from "vitest";

import {
  buildReportExportPayload,
  formatReportExportParams,
  getGroupedReportCatalog,
  getReportCatalogItem,
  getMissingRequiredReportFields,
  getMissingRequiredReportFieldsMessage,
  getReportPrintPreviewPath,
  getReportRuleOptionScope,
  getReportTypeLabel,
  REPORT_TYPE_OPTIONS,
  reportTypeUsesField,
} from "../src/components/reports/reportTypeConfig";

describe("report type config", () => {
  it("exposes stable report type options and labels", () => {
    expect(REPORT_TYPE_OPTIONS).toHaveLength(10);
    expect(getReportTypeLabel("student_analysis")).toBe("学生成绩分析单");
    expect(getReportTypeLabel("unknown_report")).toBe("unknown_report");
  });

  it("groups reports into teacher-readable output domains", () => {
    const groups = getGroupedReportCatalog();
    const labels = groups.map((item) => item.label);

    expect(labels).toContain("考试成绩");
    expect(labels).toContain("高考推荐");
    expect(getReportCatalogItem("recommendation_summary")).toMatchObject({
      domain: "gaokao",
      requiredParams: ["学生", "推荐方案"],
      formats: ["Excel", "打印预览"],
    });
  });

  it("knows which fields each report type uses", () => {
    expect(reportTypeUsesField("student_analysis", "exam_id")).toBe(true);
    expect(reportTypeUsesField("student_analysis", "student_id")).toBe(true);
    expect(reportTypeUsesField("student_analysis", "class_id")).toBe(false);
    expect(reportTypeUsesField("teacher_workload", "rule_version_id")).toBe(true);
    expect(reportTypeUsesField("recommendation_summary", "scheme_id")).toBe(true);
  });

  it("builds missing required field labels from the form state", () => {
    expect(
      getMissingRequiredReportFields({
        report_type: "student_analysis",
      }),
    ).toEqual(["考试", "学生"]);

    expect(
      getMissingRequiredReportFields({
        report_type: "teacher_workload",
        semester_id: 2,
      }),
    ).toEqual([]);
    expect(
      getMissingRequiredReportFieldsMessage({
        report_type: "student_analysis",
      }),
    ).toBe("请先补齐：考试、学生");
  });

  it("returns the correct rule scope and print preview path", () => {
    expect(getReportRuleOptionScope("teacher_workload")).toBe("workload");
    expect(getReportRuleOptionScope("adviser_quant_summary")).toBe("adviser");
    expect(getReportRuleOptionScope("student_analysis")).toBeNull();

    expect(
      getReportPrintPreviewPath({
        report_type: "student_analysis",
        student_id: 8,
        exam_id: 12,
      }),
    ).toBe("/print/student-analysis/8/12");
    expect(
      getReportPrintPreviewPath({
        report_type: "recommendation_summary",
        student_id: 8,
        scheme_id: 21,
      }),
    ).toBe("/print/recommendations/8/21");
    expect(
      getReportPrintPreviewPath({
        report_type: "teacher_workload",
        semester_id: 5,
        rule_version_id: 3,
      }),
    ).toBe("/print/workload/5?ruleVersionId=3");
  });

  it("builds export payloads from filled form values", () => {
    expect(
      buildReportExportPayload({
        report_type: "recommendation_summary",
        student_id: 8,
        scheme_id: 21,
        semester_id: undefined,
      }),
    ).toEqual({
      report_type: "recommendation_summary",
      student_id: 8,
      scheme_id: 21,
    });

    expect(
      buildReportExportPayload({
        report_type: "teacher_workload",
        semester_id: 5,
        rule_version_id: 3,
      }),
    ).toEqual({
      report_type: "teacher_workload",
      semester_id: 5,
      rule_version_id: 3,
    });
  });

  it("formats stored export params with non-technical field labels", () => {
    expect(
      formatReportExportParams({
        report_type: "student_analysis",
        exam_id: 12,
        student_id: 8,
      }),
    ).toBe("报表类型=学生成绩分析单 / 考试=12 / 学生=8");

    expect(formatReportExportParams(null)).toBe("-");
  });
});
