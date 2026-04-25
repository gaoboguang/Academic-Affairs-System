import { describe, expect, it } from "vitest";

import {
  buildAdviserQuantInsightCards,
  buildClassAnalysisInsightCards,
  buildEvaluationInsightCards,
  buildGradeAnalysisInsightCards,
  buildGrowthInsightCards,
  buildRecommendationReportInsightCards,
  buildStudentAnalysisInsightCards,
  buildTeacherAnalysisInsightCards,
  buildWorkloadInsightCards,
} from "../src/components/reports/reportInsights";

describe("report insights", () => {
  it("builds student analysis insight cards with trend and subject focus", () => {
    const cards = buildStudentAnalysisInsightCards({
      student_name: "张三",
      exam_name: "高三一模",
      total_score: 612,
      class_rank: 3,
      grade_rank: 18,
      previous_exam_name: "高三零模",
      total_score_delta: 18,
      subjects: [
        {
          subject_id: 1,
          subject_name: "语文",
          score: 122,
          class_rank: 2,
          grade_rank: 10,
          grade_percentile: 92,
          score_delta: 6,
        },
        {
          subject_id: 2,
          subject_name: "数学",
          score: 101,
          class_rank: 12,
          grade_rank: 76,
          grade_percentile: 41,
          score_delta: -9,
        },
      ],
    });

    expect(cards).toHaveLength(4);
    expect(cards[0]?.summary).toContain("总分 612");
    expect(cards[1]?.summary).toContain("提升 18 分");
    expect(cards[2]?.summary).toContain("语文");
    expect(cards[3]?.summary).toContain("数学");
    expect(cards[3]?.tone).toBe("warning");
  });

  it("builds class analysis insight cards with grade comparison", () => {
    const cards = buildClassAnalysisInsightCards({
      class_name: "高三1班",
      exam_name: "高三一模",
      student_count: 48,
      total_average: 536.5,
      total_median: 541,
      grade_average: 529.25,
      subject_breakdown: [
        {
          subject_id: 1,
          subject_name: "语文",
          average_score: 110.5,
          excellent_rate: 52.1,
          pass_rate: 97.9,
        },
        {
          subject_id: 2,
          subject_name: "数学",
          average_score: 94.2,
          excellent_rate: 28.4,
          pass_rate: 71.6,
        },
      ],
    });

    expect(cards).toHaveLength(4);
    expect(cards[1]?.summary).toContain("高于年级 7.25 分");
    expect(cards[2]?.summary).toContain("语文");
    expect(cards[3]?.summary).toContain("数学");
  });

  it("builds grade analysis insight cards with class and subject priorities", () => {
    const cards = buildGradeAnalysisInsightCards({
      grade_name: "高三",
      exam_name: "高三一模",
      student_count: 320,
      total_average: 498.4,
      total_median: 503,
      excellent_rate: 36.8,
      class_breakdown: [
        { class_name: "高三1班", student_count: 52, average_score: 534.2, excellent_rate: 48.1 },
        { class_name: "高三8班", student_count: 47, average_score: 462.3, excellent_rate: 19.7 },
      ],
      subject_breakdown: [
        { subject_id: 1, subject_name: "语文", average_score: 108.8, excellent_rate: 41.2, pass_rate: 93.4 },
        { subject_id: 2, subject_name: "数学", average_score: 86.1, excellent_rate: 18.4, pass_rate: 62.5 },
      ],
    });

    expect(cards).toHaveLength(4);
    expect(cards[0]?.detail).toContain("36.8%");
    expect(cards[1]?.summary).toContain("高三1班");
    expect(cards[2]?.summary).toContain("高三8班");
    expect(cards[3]?.summary).toContain("数学");
  });

  it("builds teacher analysis insight cards with strongest and weakest assignments", () => {
    const cards = buildTeacherAnalysisInsightCards({
      teacher_name: "李老师",
      exam_name: "高三一模",
      overall_average: 102.4,
      assignment_breakdown: [
        {
          assignment_id: 1,
          class_name: "高三1班",
          subject_name: "英语",
          average_score: 112.6,
          excellent_rate: 58.3,
          pass_rate: 95.8,
          valid_count: 48,
        },
        {
          assignment_id: 2,
          class_name: "高三8班",
          subject_name: "英语",
          average_score: 89.1,
          excellent_rate: 21.5,
          pass_rate: 68.1,
          valid_count: 46,
        },
      ],
    });

    expect(cards).toHaveLength(3);
    expect(cards[0]?.summary).toContain("102.4");
    expect(cards[1]?.summary).toContain("高三1班 / 英语");
    expect(cards[2]?.summary).toContain("高三8班 / 英语");
    expect(cards[2]?.tone).toBe("warning");
  });

  it("builds workload insight cards from result rows", () => {
    const cards = buildWorkloadInsightCards([
      {
        semester_name: "2025-2026 学年下学期",
        rule_version_name: "默认规则 v3",
        teacher_name: "张老师",
        weekly_hours: 18,
        semester_hours: 324,
        semester_workload: 356.5,
      },
      {
        semester_name: "2025-2026 学年下学期",
        rule_version_name: "默认规则 v3",
        teacher_name: "李老师",
        weekly_hours: 21,
        semester_hours: 336,
        semester_workload: 348,
      },
    ]);

    expect(cards).toHaveLength(3);
    expect(cards[0]?.summary).toContain("2 位教师");
    expect(cards[1]?.summary).toContain("张老师");
    expect(cards[2]?.summary).toContain("李老师");
  });

  it("builds evaluation insight cards from batch overview", () => {
    const cards = buildEvaluationInsightCards({
      batch_id: 12,
      template_name: "2026 春季评教",
      semester_name: "2025-2026 下学期",
      teacher_count: 2,
      teacher_summaries: [
        {
          teacher_id: 1,
          teacher_name: "王老师",
          overall_avg_score: 4.83,
          response_count: 120,
          rank: 1,
          dimension_scores_json: { 教学组织: 4.9, 课堂互动: 4.7 },
        },
        {
          teacher_id: 2,
          teacher_name: "赵老师",
          overall_avg_score: 4.18,
          response_count: 116,
          rank: 2,
          dimension_scores_json: { 教学组织: 4.5, 课堂互动: 3.9 },
        },
      ],
    });

    expect(cards).toHaveLength(4);
    expect(cards[0]?.summary).toContain("2 位教师");
    expect(cards[1]?.summary).toContain("王老师");
    expect(cards[2]?.summary).toContain("赵老师");
    expect(cards[3]?.summary).toContain("教学组织");
  });

  it("builds adviser quant insight cards from summary rows", () => {
    const cards = buildAdviserQuantInsightCards([
      {
        teacher_id: 1,
        teacher_name: "周老师",
        semester_name: "2025-2026 下学期",
        rule_version_name: "量化规则 v2",
        total_score: 32,
        positive_score: 36,
        negative_score: 4,
        record_count: 7,
        class_names: ["高二1班"],
        category_scores_json: { daily_management: 18, activity: 14 },
      },
      {
        teacher_id: 2,
        teacher_name: "吴老师",
        semester_name: "2025-2026 下学期",
        rule_version_name: "量化规则 v2",
        total_score: 21,
        positive_score: 28,
        negative_score: 7,
        record_count: 8,
        class_names: ["高二8班"],
        category_scores_json: { daily_management: 12, activity: 9 },
      },
    ]);

    expect(cards).toHaveLength(4);
    expect(cards[0]?.summary).toContain("2 位教师");
    expect(cards[1]?.summary).toContain("周老师");
    expect(cards[2]?.summary).toContain("吴老师");
    expect(cards[3]?.summary).toContain("班级常规管理");
  });

  it("builds growth insight cards from student archive data", () => {
    const cards = buildGrowthInsightCards({
      profile: {
        student: {
          student_no: "2026001",
          name: "陈同学",
          current_grade_name: "高二",
          current_class_name: "1班",
        },
      },
      records: [
        {
          id: 1,
          occurred_on: "2026-03-18",
          record_type: "activity",
          title: "校内科技节获奖",
          owner_name: "班主任",
          attachments: [{ id: 1 }],
        },
        {
          id: 2,
          occurred_on: "2026-04-02",
          record_type: "activity",
          title: "社会实践总结",
          owner_name: "德育处",
          attachments: [],
        },
      ],
    });

    expect(cards).toHaveLength(3);
    expect(cards[0]?.summary).toContain("2 条成长记录");
    expect(cards[1]?.summary).toContain("活动记录");
    expect(cards[2]?.summary).toContain("2026-04-02");
  });

  it("builds recommendation report insight cards with global risk summary", () => {
    const cards = buildRecommendationReportInsightCards(
      [
        {
          id: 1,
          school_name: "华东理工大学",
          major_name: "化学工程与工艺",
          admit_probability: "medium",
          match_score: 78,
          rank_gap: -520,
          risk_flags_json: ["sample_insufficient", "manual_formula_check"],
        },
        {
          id: 2,
          school_name: "上海大学",
          major_name: "信息工程",
          admit_probability: "medium",
          match_score: 81,
          rank_gap: -180,
          risk_flags_json: ["rank_missing", "postgraduate_path_mismatch"],
        },
      ] as any,
      {
        score_input_label: "高三一模换算位次",
        reference_exam_name: "高三一模",
        use_historical_mapping: true,
      },
    );

    expect(cards).toHaveLength(5);
    expect(cards[0]?.summary).toContain("高三一模换算位次");
    expect(cards[1]?.summary).toContain("1 条结果存在样本不足提示");
    expect(cards[2]?.summary).toContain("1 条结果已改按分数参考");
    expect(cards[3]?.summary).toContain("1 条结果仍需人工核对招生章程");
    expect(cards[4]?.summary).toContain("1 条结果与当前可接受路径存在偏差");
  });
});
