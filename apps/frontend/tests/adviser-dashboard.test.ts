import { describe, expect, it } from "vitest";

import {
  adviserRiskTagType,
  buildAdviserActionSummary,
  buildAdviserDashboardEmptyTips,
  formatGrowthSummary,
  formatPlanningSummary,
} from "../src/components/analytics/adviserDashboard";

describe("adviser dashboard helpers", () => {
  it("keeps missing score, growth and planning data visible", () => {
    const tips = buildAdviserDashboardEmptyTips({
      grade_id: 1,
      grade_name: "高一",
      class_id: 1,
      class_name: "1班",
      exam_id: null,
      exam_name: null,
      start_date: "2026-04-01",
      end_date: "2026-04-30",
      overview: {
        student_count: 42,
        score_sample_count: 0,
        growth_record_count: 0,
        open_task_count: 0,
        overdue_task_count: 0,
        follow_up_count: 0,
      },
      score_summary: { imported: false, sample_count: 0, low_score_count: 0, decline_count: 0 },
      growth_summary: {
        total_records: 0,
        students_with_records_count: 0,
      },
      planning_summary: {
        open_task_count: 0,
        overdue_task_count: 0,
        due_soon_task_count: 0,
        high_priority_open_count: 0,
        students_without_goal_count: 3,
      },
      risk_students: [],
      action_items: [],
      data_flags: ["当前范围暂无成长档案记录"],
    });

    expect(tips).toContain("当前范围没有成绩样本，成绩风险只显示数据缺口。");
    expect(tips).toContain("当前范围暂无成长档案记录，跟进建议会偏保守。");
    expect(tips).toContain("仍有 3 名学生未建立升学规划目标。");
    expect(adviserRiskTagType("urgent")).toBe("danger");
  });

  it("formats compact summaries and action labels", () => {
    expect(
      formatGrowthSummary({
        total_records: 8,
        students_with_records_count: 5,
        latest_record_date: "2026-04-20",
      }),
    ).toBe("记录 8 条，覆盖 5 人，最近 2026-04-20");
    expect(
      formatPlanningSummary({
        open_task_count: 3,
        overdue_task_count: 1,
        due_soon_task_count: 2,
        high_priority_open_count: 1,
        students_without_goal_count: 0,
      }),
    ).toBe("开放 3 项，逾期 1，7 天内到期 2");
    expect(buildAdviserActionSummary([{ action_type: "report", title: "生成班主任周报", count: 1, student_ids: [] }])).toBe(
      "生成班主任周报 1",
    );
  });
});
