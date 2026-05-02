import { describe, expect, it } from "vitest";

import {
  buildStudentRadarRows,
  filterKnowledgePointsBySubject,
  filterKnowledgeTrendsBySubject,
  formatExamStudentOptionLabel,
  formatDiagnosisTags,
  formatErrorTagStats,
  formatKnowledgeTrendTrack,
  formatPercentValue,
  formatQuestionNumbers,
  formatSignedNumber,
  formatTaskPreviewSummary,
  getBriefingPriorityTone,
  getKnowledgeDiagnosisTone,
  getKnowledgeTrendTone,
  getSuggestionTone,
  getTargetGapSummary,
  knowledgeDisplayName,
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
        knowledge_path: "函数>函数性质>函数单调性",
        score: 6,
        full_score: 20,
        lost_score: 14,
        priority_score: 9.8,
        diagnosis_label: "优先补弱",
        error_tag_stats: [{ tag: "概念不清", count: 2 }],
        dominant_error_tag: "概念不清",
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
    expect(formatErrorTagStats(points[0].error_tag_stats)).toBe("概念不清×2");
    expect(formatErrorTagStats([{ name: "计算错误" }])).toBe("计算错误");
    expect(knowledgeDisplayName(points[0])).toBe("函数>函数性质>函数单调性");
    expect(knowledgeDisplayName(points[1])).toBe("文言实词");
    expect(getKnowledgeDiagnosisTone("优先补弱")).toBe("warning");
    expect(getKnowledgeDiagnosisTone("正常")).toBe("success");
    expect(getSuggestionTone("knowledge_focus")).toBe("warning");
  });

  it("formats knowledge trend diagnostics", () => {
    const trends = [
      {
        subject_id: 2,
        subject_name: "数学",
        knowledge_point_id: 1,
        knowledge_point_name: "函数单调性",
        trend_exam_count: 3,
        weak_exam_count: 3,
        latest_score_rate: 0.4,
        average_score_rate: 0.3,
        trend_delta: 0.2,
        total_full_score: 30,
        total_lost_score: 21,
        priority_score: 12.2,
        trend_label: "持续薄弱",
        points: [
          {
            exam_id: 1,
            exam_name: "一模",
            exam_date: "2026-03-01",
            score_rate: 0.2,
            full_score: 10,
            lost_score: 8,
            diagnosis_label: "优先补弱",
          },
          {
            exam_id: 2,
            exam_name: "二模",
            exam_date: "2026-04-01",
            score_rate: 0.4,
            full_score: 10,
            lost_score: 6,
            diagnosis_label: "优先补弱",
          },
        ],
      },
      {
        subject_id: 1,
        subject_name: "语文",
        knowledge_point_id: 2,
        knowledge_point_name: "文言实词",
        trend_exam_count: 2,
        weak_exam_count: 0,
        total_full_score: 20,
        total_lost_score: 2,
        priority_score: 0,
        trend_label: "保持观察",
        points: [],
      },
    ];

    expect(filterKnowledgeTrendsBySubject(trends, 2)).toHaveLength(1);
    expect(filterKnowledgeTrendsBySubject(trends, null)).toHaveLength(2);
    expect(formatKnowledgeTrendTrack(trends[0].points)).toBe("一模 20.0% / 二模 40.0%");
    expect(formatKnowledgeTrendTrack([])).toBe("-");
    expect(getKnowledgeTrendTone("持续薄弱")).toBe("warning");
    expect(getKnowledgeTrendTone("正在改善")).toBe("success");
    expect(getSuggestionTone("knowledge_trend_focus")).toBe("warning");
  });

  it("formats class briefing priority and remediation task previews", () => {
    expect(getBriefingPriorityTone("高")).toBe("danger");
    expect(getBriefingPriorityTone("中")).toBe("warning");
    expect(getBriefingPriorityTone("低")).toBe("info");
    expect(formatTaskPreviewSummary(2, 1)).toBe("可生成 2 项，已存在 1 项");
    expect(formatTaskPreviewSummary(0, 0)).toBe("暂无可生成任务");
  });
});
