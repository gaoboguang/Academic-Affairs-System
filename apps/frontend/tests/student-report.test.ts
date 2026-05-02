import { describe, expect, it } from "vitest";

import {
  buildStudentRadarRows,
  filterKnowledgePointsBySubject,
  formatExamStudentOptionLabel,
  formatDiagnosisTags,
  formatPercentValue,
  formatQuestionNumbers,
  formatSignedNumber,
  getKnowledgeDiagnosisTone,
  getSuggestionTone,
  getTargetGapSummary,
  pickExamStudentSelection,
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

  it("keeps or resets student selection within current exam sample", () => {
    const students = [
      { id: 201, student_no: "S201", name: "后段学生", current_class_name: "3班", grade_rank: 201 },
      { id: 250, student_no: "S250", name: "可检索学生", current_class_name: "5班", grade_rank: 250 },
    ];

    expect(pickExamStudentSelection(students, 250)).toBe(250);
    expect(pickExamStudentSelection(students, 1)).toBe(201);
    expect(pickExamStudentSelection([], 250)).toBeNull();
    expect(formatExamStudentOptionLabel(students[1])).toBe("S250 - 可检索学生（5班 / 校内250名）");
  });

  it("filters and formats knowledge point diagnostics", () => {
    const points = [
      {
        subject_id: 2,
        subject_name: "数学",
        knowledge_point_id: 1,
        knowledge_point_name: "函数单调性",
        score: 6,
        full_score: 20,
        lost_score: 14,
        priority_score: 9.8,
        diagnosis_label: "优先补弱",
        question_count: 2,
        question_numbers: ["12", "18"],
      },
      {
        subject_id: 1,
        subject_name: "语文",
        knowledge_point_id: 2,
        knowledge_point_name: "文言实词",
        score: 8,
        full_score: 10,
        lost_score: 2,
        priority_score: 0.4,
        diagnosis_label: "正常",
        question_count: 1,
        question_numbers: ["5"],
      },
    ];

    expect(filterKnowledgePointsBySubject(points, 2)).toHaveLength(1);
    expect(filterKnowledgePointsBySubject(points, null)).toHaveLength(2);
    expect(formatQuestionNumbers(points[0].question_numbers)).toBe("12、18");
    expect(formatQuestionNumbers([])).toBe("-");
    expect(getKnowledgeDiagnosisTone("优先补弱")).toBe("warning");
    expect(getKnowledgeDiagnosisTone("正常")).toBe("success");
    expect(getSuggestionTone("knowledge_focus")).toBe("warning");
  });
});
