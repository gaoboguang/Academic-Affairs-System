import { describe, expect, it } from "vitest";

import {
  buildStudentRadarRows,
  formatDiagnosisTags,
  formatPercentValue,
  formatSignedNumber,
  getSuggestionTone,
  getTargetGapSummary,
} from "../src/components/analytics/studentReport";

describe("student report helpers", () => {
  it("builds radar rows from PR and T score metrics", () => {
    const subjects = [
      { subject_id: 1, subject_name: "语文", score: 120, grade_percentile: 0.875, t_score: 61.24 },
      { subject_id: 2, subject_name: "数学", score: 90, grade_percentile: null, t_score: 44.1 },
    ];

    expect(buildStudentRadarRows(subjects, "pr")).toEqual([
      { subject: "语文", value: 87.5, label: "87.5%" },
    ]);
    expect(buildStudentRadarRows(subjects, "t_score")).toEqual([
      { subject: "语文", value: 61.2, label: "61.2" },
      { subject: "数学", value: 44.1, label: "44.1" },
    ]);
  });

  it("formats target gaps, tags and suggestion tones", () => {
    expect(formatPercentValue(0.856)).toBe("85.6%");
    expect(formatSignedNumber(-12.5, "分")).toBe("-12.5分");
    expect(formatSignedNumber(8, "名")).toBe("+8名");
    expect(formatDiagnosisTags(["偏科弱项", "低于同档"])).toBe("偏科弱项 / 低于同档");
    expect(getTargetGapSummary([
      { line_id: 1, line_name: "本科线", threshold_label: "230 分", gap_score: -5, status: "near_below" },
    ])).toBe("本科线：-5分");
    expect(getSuggestionTone("keep_strength")).toBe("success");
    expect(getSuggestionTone("fix_weakness")).toBe("warning");
  });
});
