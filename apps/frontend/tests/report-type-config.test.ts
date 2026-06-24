import { describe, expect, it } from "vitest";

import {
  buildReportExportPayload,
  formatReportExportParams,
  getReportCatalogItemsByDomain,
  getReportDomainForType,
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
    const optionValues = REPORT_TYPE_OPTIONS.map((item) => item.value);
    expect(optionValues).toContain("student_analysis");
    expect(optionValues).toContain("student_knowledge_plan");
    expect(optionValues).toContain("class_knowledge_briefing");
    expect(optionValues).toContain("student_followup_package");
    expect(optionValues).toContain("planning_followup");
    expect(getReportTypeLabel("student_analysis")).toBe("学生成绩分析单");
    expect(getReportTypeLabel("student_knowledge_plan")).toBe("学生知识点学习清单");
    expect(getReportTypeLabel("class_knowledge_briefing")).toBe("班级知识点讲评清单");
    expect(getReportTypeLabel("unknown_report")).toBe("unknown_report");
  });

  it("groups reports into teacher-readable output domains", () => {
    const groups = getGroupedReportCatalog();
    const labels = groups.map((item) => item.label);

    expect(labels).toContain("考试成绩");
    expect(labels).toContain("班主任");
    expect(labels).toContain("高考推荐");
    expect(getReportCatalogItem("recommendation_summary")).toMatchObject({
      domain: "gaokao",
      requiredParams: ["学生", "推荐方案"],
      formats: ["Excel", "打印预览"],
    });
    expect(getReportCatalogItem("student_knowledge_plan")).toMatchObject({
      domain: "students",
      requiredParams: ["考试", "学生"],
      formats: ["Excel", "打印预览"],
    });
    expect(getReportCatalogItem("class_knowledge_briefing")).toMatchObject({
      domain: "scores",
      requiredParams: ["考试", "班级"],
      formats: ["Excel", "打印预览"],
    });
  });

  it("supports compact report selection by domain", () => {
    expect(getReportDomainForType("student_analysis")).toBe("students");
    expect(getReportDomainForType("class_analysis")).toBe("scores");
    expect(getReportDomainForType("unknown_report")).toBeNull();

    expect(getReportCatalogItemsByDomain("scores").map((item) => item.value)).toEqual([
      "class_knowledge_briefing",
      "class_analysis",
      "grade_summary",
    ]);
    expect(getReportCatalogItemsByDomain("system")).toEqual([]);
  });

  it("knows which fields each report type uses", () => {
    expect(reportTypeUsesField("student_analysis", "exam_id")).toBe(true);
    expect(reportTypeUsesField("student_analysis", "student_id")).toBe(true);
    expect(reportTypeUsesField("student_knowledge_plan", "student_id")).toBe(true);
    expect(reportTypeUsesField("class_knowledge_briefing", "class_id")).toBe(true);
    expect(reportTypeUsesField("student_analysis", "class_id")).toBe(false);
    expect(reportTypeUsesField("teacher_workload", "rule_version_id")).toBe(true);
    expect(reportTypeUsesField("recommendation_summary", "scheme_id")).toBe(true);
    expect(reportTypeUsesField("student_followup_package", "start_date")).toBe(true);
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
    expect(getReportRuleOptionScope("student_followup_package")).toBeNull();
    expect(getReportRuleOptionScope("planning_followup")).toBeNull();
    expect(getReportRuleOptionScope("student_knowledge_plan")).toBeNull();
    expect(getReportRuleOptionScope("class_knowledge_briefing")).toBeNull();
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
        report_type: "student_knowledge_plan",
        student_id: 8,
        exam_id: 12,
      }),
    ).toBe("/print/student-knowledge/8/12");
    expect(
      getReportPrintPreviewPath({
        report_type: "class_knowledge_briefing",
        class_id: 3,
        exam_id: 12,
      }),
    ).toBe("/print/class-knowledge-briefing/3/12");
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
    expect(
      getReportPrintPreviewPath({
        report_type: "student_followup_package",
        student_id: 8,
        exam_id: 12,
        start_date: "2026-04-01",
      }),
    ).toBe("/print/student-followup-package/8?examId=12&startDate=2026-04-01");
    expect(
      getReportPrintPreviewPath({
        report_type: "planning_followup",
        student_id: 8,
        exam_id: 12,
      }),
    ).toBe("/print/planning-followup/8?examId=12");
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
        start_date: "2026-04-01",
      }),
    ).toEqual({
      report_type: "teacher_workload",
      semester_id: 5,
      rule_version_id: 3,
      start_date: "2026-04-01",
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
