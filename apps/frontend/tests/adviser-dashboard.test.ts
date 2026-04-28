import { describe, expect, it } from "vitest";

import {
  adviserRiskTagType,
  buildAdviserActionSummary,
  buildAdviserDashboardEmptyTips,
  formatAttendanceSummary,
  formatBehaviorSummary,
} from "../src/components/analytics/adviserDashboard";

describe("adviser dashboard helpers", () => {
  it("keeps missing attendance and behavior visible instead of treating them as zero risk", () => {
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
        attendance_status: "未导入",
        behavior_status: "未导入",
        absence_risk_count: 0,
        behavior_risk_count: 0,
        follow_up_count: 0,
      },
      score_summary: { imported: false, sample_count: 0, low_score_count: 0, decline_count: 0 },
      attendance_summary: {
        imported: false,
        total_records: 0,
        late_count: 0,
        early_leave_count: 0,
        sick_leave_count: 0,
        personal_leave_count: 0,
        truancy_count: 0,
      },
      behavior_summary: {
        imported: false,
        total_records: 0,
        positive_count: 0,
        discipline_count: 0,
        severe_count: 0,
      },
      risk_students: [],
      action_items: [],
      data_flags: ["考勤数据未导入", "行为数据未导入"],
    });

    expect(tips).toContain("考勤未导入，不会按 0 风险处理。");
    expect(tips).toContain("行为记录未导入，不会按 0 风险处理。");
    expect(adviserRiskTagType("urgent")).toBe("danger");
  });

  it("formats compact summaries and action labels", () => {
    expect(
      formatAttendanceSummary({
        imported: true,
        total_records: 8,
        late_count: 2,
        early_leave_count: 1,
        sick_leave_count: 1,
        personal_leave_count: 0,
        truancy_count: 1,
      }),
    ).toBe("记录 8 条，迟到 2，请假 1，旷课 1");
    expect(
      formatBehaviorSummary({
        imported: true,
        total_records: 3,
        positive_count: 1,
        discipline_count: 1,
        severe_count: 1,
      }),
    ).toBe("记录 3 条，表扬 1，违纪/奖惩 1，高关注 1");
    expect(buildAdviserActionSummary([{ action_type: "report", title: "生成班主任周报", count: 1, student_ids: [] }])).toBe(
      "生成班主任周报 1",
    );
  });
});
