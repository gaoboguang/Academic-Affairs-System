import { describe, expect, it } from "vitest";

import { formatUserActionError, getErrorMessage } from "../src/utils/userFeedback";

describe("user feedback helpers", () => {
  it("formats unknown errors into a user-facing message", () => {
    expect(getErrorMessage(null)).toBe("系统暂时没有返回具体原因");
  });

  it("adds action and next-step guidance to request failures", () => {
    expect(formatUserActionError("刷新导入中心", new Error("请求失败: 500"), "确认本地服务已启动后重试")).toBe(
      "刷新导入中心失败。原因：本地服务返回异常：500。建议：确认本地服务已启动后重试",
    );
  });
});
