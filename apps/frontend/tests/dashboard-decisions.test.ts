import { describe, expect, it } from "vitest";

import {
  buildDashboardNextSteps,
  formatDashboardBackupLabel,
  formatDataHealthCardValue,
} from "../src/components/dashboard/dashboardDecisions";

describe("dashboard decision helpers", () => {
  it("suggests concrete next actions for an empty teaching trial dataset", () => {
    const steps = buildDashboardNextSteps({
      student_total: 806,
      teacher_total: 2,
      exam_total: 1,
      score_record_total: 0,
      latest_backup: null,
      data_health: {
        status: "warning",
        label: "可验收但有数据警告",
        summary: "P0 安全底座可继续验收，但数据可用性仍需补齐和人工复核。",
        p0_gap_count: 3,
        warning_count: 5,
        blocking_count: 0,
        gaps: ["特殊类型已有招生计划但缺专门录取结果：单独招生、综合评价招生"],
      },
    });

    expect(steps.map((step) => step.code)).toEqual([
      "score_record_empty",
      "teacher_too_few",
      "gaokao_data_warning",
      "backup_missing",
    ]);
    expect(steps[0].path).toBe("/exams");
    expect(steps[2].detail).toContain("3 条 P0 数据缺口");
  });

  it("falls back to a ready state when the dashboard has no actionable warning", () => {
    const steps = buildDashboardNextSteps({
      student_total: 806,
      teacher_total: 20,
      exam_total: 3,
      score_record_total: 1200,
      latest_backup: {
        backup_name: "local_edu_backup.zip",
        created_at: "2026-04-27T12:30:00",
        status: "success",
        file_size: 1024,
      },
      data_health: {
        status: "pass",
        label: "P0 可通过",
        summary: "当前健康检查未发现阻断项或 P0 数据缺口。",
        p0_gap_count: 0,
        warning_count: 0,
        blocking_count: 0,
        gaps: [],
      },
    });

    expect(steps).toHaveLength(1);
    expect(steps[0].code).toBe("ready_for_trial");
    expect(
      formatDataHealthCardValue({
        status: "pass",
        label: "P0 可通过",
        summary: "",
        p0_gap_count: 0,
        warning_count: 0,
        blocking_count: 0,
        gaps: [],
      }),
    ).toBe("P0 可通过");
  });

  it("formats backup labels without hiding missing backups", () => {
    expect(formatDashboardBackupLabel(null)).toBe("未创建");
    expect(
      formatDashboardBackupLabel({
        backup_name: "local_edu_backup_20260427.zip",
        created_at: null,
        status: "success",
        file_size: 1024,
      }),
    ).toBe("local_edu_backup_20260427.zip");
  });
});
