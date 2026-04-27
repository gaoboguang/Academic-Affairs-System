import { describe, expect, it } from "vitest";

import {
  buildScoreReadinessMessages,
  buildScoreReportGuardMessages,
} from "../src/utils/scoreReadiness";

describe("score readiness helpers", () => {
  it("warns when score records are empty", () => {
    const messages = buildScoreReadinessMessages({ examCount: 1, scoreRecordTotal: 0 });
    expect(messages).toContain("当前成绩记录为 0，学生、班级、年级和教师分析会显示空态；请先导入成绩表。");
  });

  it("marks single-exam data as snapshot instead of trend", () => {
    expect(buildScoreReadinessMessages({ examCount: 1, scoreRecordTotal: 12 })).toContain(
      "当前只有 1 场考试，趋势变化只能作为单次快照，不宜解读为升降趋势。",
    );
    expect(buildScoreReportGuardMessages("student_analysis", { examCount: 1, scoreRecordTotal: 12 })).toEqual([
      "当前只有 1 场考试，报表中的趋势字段只代表单次考试快照。",
    ]);
  });
});
