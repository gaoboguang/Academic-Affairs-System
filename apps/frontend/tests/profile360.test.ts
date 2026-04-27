import { describe, expect, it } from "vitest";

import {
  buildStudent360Actions,
  buildStudent360RiskTags,
  buildTeacher360Actions,
  buildTeacher360RiskTags,
} from "../src/utils/profile360";

describe("profile360 helpers", () => {
  it("builds student risk tags from missing or sensitive profile data", () => {
    const tags = buildStudent360RiskTags({
      examCount: 0,
      growthRecordCount: 0,
      recommendationCount: 0,
      attachmentCount: 0,
      classTransferCount: 1,
      studentType: "art",
    });
    expect(tags.map((item) => item.label)).toContain("成绩数据缺失");
    expect(tags.map((item) => item.label)).toContain("近期调班需复核");
    expect(tags.map((item) => item.label)).toContain("特殊类型仅初筛");
    expect(buildStudent360Actions(3).find((item) => item.label === "成长时间线")?.path).toBe(
      "/growth-archive?student_id=3",
    );
  });

  it("builds teacher risk tags and actions for incomplete teaching data", () => {
    const tags = buildTeacher360RiskTags({
      activeAssignmentCount: 0,
      examTrendCount: 0,
      peerComparisonCount: 0,
      hasSubject: false,
    });
    expect(tags.map((item) => item.label)).toEqual([
      "任教学科未设置",
      "任教关系缺失",
      "考试样本不足",
      "同科对比不足",
    ]);
    expect(buildTeacher360Actions().map((item) => item.label)).toContain("课表与工作量");
  });
});
