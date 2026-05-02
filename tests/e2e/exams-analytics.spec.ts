import { expect, test } from "@playwright/test";
import {
  e2eExamName,
  ensureExamWithScores,
  expectToast,
  invalidScoresFixture,
} from "./helpers/localEduE2e";

test("考试主流程：新建考试、导入成绩并带到分析中心", async ({ page }) => {
  await ensureExamWithScores(page);
  await page.goto("/analytics");
  await expect(page.getByRole("heading", { name: "分析中心" })).toBeVisible();
  await page.locator(".panel-block").filter({ hasText: "选择考试" }).locator(".el-select").first().click();
  await page.keyboard.type(e2eExamName);
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Enter");
  await expect(page.locator(".page-chip-row").first()).toContainText(e2eExamName);
});

test("分析中心：多学年全景对比可展示两学年趋势", async ({ page }) => {
  await page.goto("/analytics");
  await expect(page.getByRole("heading", { name: "分析中心" })).toBeVisible();

  await page.getByRole("tab", { name: "全景对比" }).click();
  const panoramaPanel = page.locator(".panel-block").filter({ hasText: "多学年全景对比" });
  await expect(panoramaPanel.getByRole("heading", { name: "多学年全景对比" })).toBeVisible();
  await expect(panoramaPanel.getByText("覆盖学年")).toBeVisible();
  await expect(panoramaPanel.locator(".el-table__row").filter({ hasText: "2024-2025" }).first()).toBeVisible();
  await expect(panoramaPanel.locator(".el-table__row").filter({ hasText: "2025-2026" }).first()).toBeVisible();
  await expect(panoramaPanel.locator(".el-table__row").filter({ hasText: "2025届高一4月月考" }).first()).toBeVisible();
  await expect(panoramaPanel.locator(".el-table__row").filter({ hasText: "2026届高一4月月考" }).first()).toBeVisible();
  await expect(panoramaPanel.getByRole("heading", { name: "学科攻坚优先级" })).toBeVisible();
  await expect(panoramaPanel.getByRole("heading", { name: "学科风险预警" })).toBeVisible();
  await expect(panoramaPanel.getByText("当前重点")).toBeVisible();
  await expect(panoramaPanel.getByText("关注级别")).toBeVisible();
  await expect(panoramaPanel.locator(".el-table__row").filter({ hasText: "语文" }).first()).toBeVisible();
  await expect(panoramaPanel.locator(".el-table__row").filter({ hasText: "数学" }).first()).toBeVisible();

  await page.getByRole("tab", { name: "班级全景" }).click();
  const classPanoramaPanel = page.locator(".panel-block").filter({ hasText: "班级全景对比" });
  await expect(classPanoramaPanel.getByRole("heading", { name: "班级全景对比" })).toBeVisible();
  await expect(classPanoramaPanel.getByText("学科攻坚优先级")).toBeVisible();
  await expect(classPanoramaPanel.locator(".el-table__row").filter({ hasText: "2024-2025" }).first()).toBeVisible();
  await expect(classPanoramaPanel.locator(".el-table__row").filter({ hasText: "2025-2026" }).first()).toBeVisible();
  await expect(classPanoramaPanel.locator(".el-table__row").filter({ hasText: "语文" }).first()).toBeVisible();

  await page.getByRole("tab", { name: "教师全景" }).click();
  const teacherPanoramaPanel = page.locator(".panel-block").filter({ hasText: "教师全景对比" });
  await expect(teacherPanoramaPanel.getByRole("heading", { name: "教师全景对比" })).toBeVisible();
  await expect(teacherPanoramaPanel.getByText("学科风险预警")).toBeVisible();
  await expect(teacherPanoramaPanel.locator(".el-table__row").filter({ hasText: "2024-2025" }).first()).toBeVisible();
  await expect(teacherPanoramaPanel.locator(".el-table__row").filter({ hasText: "2025-2026" }).first()).toBeVisible();
  await expect(teacherPanoramaPanel.locator(".el-table__row").filter({ hasText: "语文" }).first()).toBeVisible();
});

test("考试异常提示：错误成绩模板会给出明确失败原因", async ({ page }) => {
  await ensureExamWithScores(page);

  const importDialog = page.locator('[role="dialog"]').filter({ hasText: "导入成绩" });
  await expect(importDialog).toBeVisible();
  await importDialog
    .locator(".el-upload")
    .filter({ hasText: "按统一模板导入" })
    .locator('input[type="file"]')
    .setInputFiles(invalidScoresFixture);

  await expectToast(page, "成绩导入模板表头不匹配");
});
