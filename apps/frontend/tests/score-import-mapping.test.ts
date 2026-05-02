import { describe, expect, it } from "vitest";

import {
  buildScoreImportMappingPayload,
  buildScoreImportReadinessText,
  cloneScoreImportMapping,
  getScoreImportHeaders,
  getUnassignedScoreColumns,
  type ScoreImportPreview,
} from "../src/components/exams/scoreImportMapping";

const preview: ScoreImportPreview = {
  source_filename: "scores.xlsx",
  sheet_name: "数据",
  header_row: 3,
  layout_type: "wide",
  confidence: 0.91,
  messages: [],
  columns: [
    { header: "班级", role: "class_name" },
    { header: "考号", role: "student_no" },
    { header: "姓名", role: "student_name" },
    { header: "语文成绩", subject_name: "语文" },
    { header: "数学成绩", subject_name: "数学" },
    { header: "总分", ignored: true },
  ],
  sample_rows: [],
  normalized_preview: [],
  mapping: {
    layout_type: "wide",
    sheet_name: "数据",
    header_row: 3,
    field_mapping: { student_no: "考号", student_name: "姓名", class_name: "班级" },
    subject_mapping: { 语文成绩: "语文", 数学成绩: "数学" },
    subject_score_types: { 语文成绩: "original", 数学成绩: "converted" },
    ignored_columns: ["总分"],
  },
  import_ready: true,
  source_row_count: 2,
  detected_record_count: 4,
};

describe("score import mapping helpers", () => {
  it("lists source headers and editable subject columns", () => {
    expect(getScoreImportHeaders(preview)).toEqual(["班级", "考号", "姓名", "语文成绩", "数学成绩", "总分"]);
    expect(getUnassignedScoreColumns(preview, preview.mapping)).toEqual(["语文成绩", "数学成绩"]);
  });

  it("clones and serializes mapping without empty subject values", () => {
    const cloned = cloneScoreImportMapping(preview.mapping);
    cloned.subject_mapping["英语成绩"] = "";

    const payload = JSON.parse(buildScoreImportMappingPayload(cloned)) as {
      subject_mapping: Record<string, string>;
      subject_score_types: Record<string, string>;
    };
    expect(payload.subject_mapping).toEqual({ 语文成绩: "语文", 数学成绩: "数学" });
    expect(payload.subject_score_types).toEqual({ 语文成绩: "original", 数学成绩: "converted" });
    expect(cloned).not.toBe(preview.mapping);
  });

  it("formats readiness text for review states", () => {
    expect(buildScoreImportReadinessText(preview)).toContain("4 条成绩记录");
    expect(
      buildScoreImportReadinessText(preview, {
        ...preview.mapping,
        field_mapping: { student_name: "姓名" },
      }),
    ).toContain("还不能导入");
    expect(buildScoreImportReadinessText({ ...preview, confidence: 0.6 })).toContain("置信度偏低");
  });
});
