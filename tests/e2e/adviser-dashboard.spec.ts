import fs from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";
import {
  e2eExamName,
  ensureExamWithScores,
  expectToast,
  selectDropdownOption,
} from "./helpers/localEduE2e";

const attendanceFixture = path.resolve(process.cwd(), "tests/e2e/fixtures/attendance-import.xlsx");
const behaviorFixture = path.resolve(process.cwd(), "tests/e2e/fixtures/behavior-import.xlsx");

async function importStudentEventFixture(page: Page, url: string, fixturePath: string): Promise<void> {
  const response = await page.request.post(url, {
    multipart: {
      file: {
        name: path.basename(fixturePath),
        mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        buffer: fs.readFileSync(fixturePath),
      },
    },
  });
  expect(response.ok()).toBeTruthy();
  const payload = (await response.json()) as { success_rows?: number };
  expect(payload.success_rows ?? 0).toBeGreaterThan(0);
}

test("班主任驾驶舱：导入考勤行为后查看风险学生并导出周报", async ({ page }) => {
  test.setTimeout(90000);

  await ensureExamWithScores(page);

  await page.goto("/import-center");
  await expect(page.getByRole("heading", { name: "统一查看模板、批次、错误报告和撤销说明" })).toBeVisible();
  await expect(page.getByText("6. 导入考勤")).toBeVisible();
  await expect(page.getByText("7. 导入行为")).toBeVisible();

  await importStudentEventFixture(page, "/api/attendance/import", attendanceFixture);
  await importStudentEventFixture(page, "/api/behavior/import", behaviorFixture);

  await page.goto("/analytics");
  await expect(page.getByRole("heading", { name: "分析中心" })).toBeVisible();

  const examPanel = page.locator(".panel-block").filter({ hasText: "选择考试" });
  await selectDropdownOption(page, examPanel.locator(".el-select").first(), e2eExamName);

  await page.getByRole("tab", { name: "班主任驾驶舱" }).click();
  const adviserPanel = page.locator(".panel-block").filter({ hasText: "班主任驾驶舱" }).first();
  const adviserSelects = adviserPanel.locator(".adviser-filter-grid .el-select");
  await selectDropdownOption(page, adviserSelects.nth(1), "1班");
  await adviserPanel.getByRole("button", { name: "加载驾驶舱" }).click();

  await expect(adviserPanel.getByText("考勤概况")).toBeVisible();
  await expect(adviserPanel.getByText("行为概况")).toBeVisible();
  await expect(adviserPanel.getByText("本周行动清单")).toBeVisible();
  await expect(adviserPanel.locator(".adviser-summary-grid")).toContainText("旷课 1");
  await expect(adviserPanel.locator(".adviser-summary-grid")).toContainText("高关注 1");

  const riskRow = adviserPanel.locator(".el-table__row").filter({ hasText: "张三" }).first();
  await expect(riskRow).toBeVisible();
  await expect(riskRow).toContainText("紧急跟进");
  await expect(riskRow).toContainText("存在旷课");
  await riskRow.getByRole("button", { name: "张三" }).click();

  await expect(page.getByRole("heading", { name: /张三/ })).toBeVisible();
  await expect(page.getByText("近 30 天考勤")).toBeVisible();
  await expect(page.getByText("近 30 天行为")).toBeVisible();
  await expect(page.getByText("生成跟进包")).toBeVisible();

  await page.goto("/reports");
  await expect(page.getByRole("heading", { name: "输出中心" })).toBeVisible();

  const reportPanel = page.locator(".panel-block").filter({ hasText: "报表参数" });
  const reportSelects = reportPanel.locator(".filter-grid .el-select");
  await selectDropdownOption(page, reportSelects.first(), "班主任周报");
  await selectDropdownOption(page, reportSelects.nth(1), e2eExamName);
  await selectDropdownOption(page, reportSelects.nth(2), "1班");
  await expect(reportPanel.getByText("当前报表还缺少")).toHaveCount(0);

  const exportPopupPromise = page.waitForEvent("popup", { timeout: 5000 }).catch(() => null);
  await reportPanel.getByRole("button", { name: "生成报表" }).click();
  const exportPopup = await exportPopupPromise;
  if (exportPopup) {
    await exportPopup.close();
  }

  await expectToast(page, "报表已生成");
  await expect(page.locator(".el-table__row").filter({ hasText: "班主任周报" }).first()).toBeVisible();
});
