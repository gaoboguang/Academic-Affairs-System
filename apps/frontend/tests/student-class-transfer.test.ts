import { describe, expect, it } from "vitest";

import {
  canExecuteClassTransfer,
  formatClassTransferEventSummary,
  formatClassTransferResultMessage,
  formatClassTransferRoute,
  resolveClassTransferExecuteStatusLabel,
  resolveClassTransferPreviewStatusLabel,
  type ClassTransferHistoryItem,
  type ClassTransferPreviewResponse,
} from "../src/components/students/studentClassTransfer";

describe("student class transfer helpers", () => {
  it("requires the exact backend confirm text before execution", () => {
    const preview: ClassTransferPreviewResponse = {
      total: 2,
      transferable_count: 2,
      blocked_count: 0,
      target_class_id: 8,
      target_class_name: "3 班",
      target_grade_id: 2,
      target_grade_name: "高二",
      effective_on: "2026-04-25",
      required_confirm_text: "确认调班 2 名学生",
      confirm_token: "token-token-token-token",
      items: [],
      warnings: [],
      blocked: [],
    };

    expect(canExecuteClassTransfer(preview, "确认调班 2 名学生")).toBe(true);
    expect(canExecuteClassTransfer(preview, "确认调班2名学生")).toBe(false);
    expect(canExecuteClassTransfer({ ...preview, transferable_count: 0 }, "确认调班 2 名学生")).toBe(false);
  });

  it("formats class movement and timeline copy for teachers", () => {
    const item: ClassTransferHistoryItem = {
      event_type: "class_transfer",
      title: "班级调整",
      summary: "班级调整：高二 1 班 -> 高二 3 班",
      batch_id: 3,
      item_id: 9,
      student_id: 1,
      student_no: "S001",
      student_name: "张三",
      from_grade_id: 1,
      from_grade_name: "高二",
      from_class_id: 1,
      from_class_name: "1 班",
      to_grade_id: 1,
      to_grade_name: "高二",
      to_class_id: 3,
      to_class_name: "3 班",
      effective_on: "2026-04-25",
      reason: "文理方向调整",
      note: "按年级统一调班方案执行",
      operator_name: "教务处",
      status: "success",
      created_at: "2026-04-25T10:00:00",
    };

    expect(formatClassTransferRoute(item)).toBe("高二 1 班 -> 高二 3 班");
    expect(formatClassTransferEventSummary(item)).toBe(
      "2026-04-25 班级调整：高二 1 班 -> 高二 3 班，原因：文理方向调整。",
    );
  });

  it("formats status and result copy for the dialog", () => {
    expect(resolveClassTransferPreviewStatusLabel("transferable")).toBe("可调班");
    expect(resolveClassTransferPreviewStatusLabel("blocked")).toBe("已阻断");
    expect(resolveClassTransferExecuteStatusLabel("success")).toBe("已调班");
    expect(
      formatClassTransferResultMessage({
        total: 3,
        success_count: 2,
        failed_count: 1,
        blocked_count: 0,
        status: "partially_failed",
        message: "部分学生调班失败",
        items: [],
        success_items: [],
        failed_items: [],
        blocked: [],
      }),
    ).toBe("批量调班完成：成功 2 名，失败 1 名，被阻断 0 名。");
  });
});
