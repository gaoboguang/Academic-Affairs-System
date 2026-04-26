import { describe, expect, it } from "vitest";

import {
  canExecuteBulkDelete,
  formatBulkDeleteAssociationSummary,
  formatBulkDeleteResultMessage,
  resolveExecuteStatusLabel,
  resolvePreviewStatusLabel,
  type StudentBulkDeletePreviewResponse,
} from "../src/components/students/studentBulkDelete";

const emptyCounts = {
  score_count: 0,
  score_snapshot_count: 0,
  growth_record_count: 0,
  attachment_count: 0,
  class_history_count: 0,
  recommendation_count: 0,
  volunteer_draft_count: 0,
  gaokao_score_projection_count: 0,
  pathway_profile_count: 0,
  pathway_evaluation_count: 0,
};

describe("student bulk delete helpers", () => {
  it("summarizes association counts with teacher-readable labels", () => {
    expect(
      formatBulkDeleteAssociationSummary({
        ...emptyCounts,
        score_count: 12,
        growth_record_count: 2,
        volunteer_draft_count: 1,
        pathway_profile_count: 1,
      }),
    ).toEqual(["成绩记录 12 条", "成长档案 2 条", "志愿草稿 1 条", "升学画像 1 条"]);
  });

  it("keeps empty association summaries explicit", () => {
    expect(formatBulkDeleteAssociationSummary(emptyCounts)).toEqual(["暂无关联历史数据"]);
  });

  it("requires the exact backend confirm text before execution", () => {
    const preview: StudentBulkDeletePreviewResponse = {
      total: 2,
      deletable_count: 2,
      blocked_count: 0,
      mode: "soft_delete",
      required_confirm_text: "确认删除 2 名学生",
      confirm_token: "token-token-token-token",
      items: [],
      warnings: [],
      blocked: [],
    };

    expect(canExecuteBulkDelete(preview, "确认删除 2 名学生")).toBe(true);
    expect(canExecuteBulkDelete(preview, "确认删除2名学生")).toBe(false);
    expect(canExecuteBulkDelete({ ...preview, deletable_count: 0 }, "确认删除 2 名学生")).toBe(false);
  });

  it("formats status and result copy for the dialog", () => {
    expect(resolvePreviewStatusLabel("deletable")).toBe("可停用");
    expect(resolvePreviewStatusLabel("blocked")).toBe("已阻断");
    expect(resolveExecuteStatusLabel("success")).toBe("已停用");
    expect(
      formatBulkDeleteResultMessage({
        total: 3,
        success_count: 2,
        failed_count: 1,
        blocked_count: 0,
        status: "partially_failed",
        mode: "soft_delete",
        message: "部分学生处理失败",
        items: [],
        success_items: [],
        failed_items: [],
        blocked: [],
      }),
    ).toBe("批量删除完成：成功 2 名，失败 1 名，被阻断 0 名。");
  });
});
