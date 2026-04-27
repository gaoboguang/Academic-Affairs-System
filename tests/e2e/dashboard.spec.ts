import { expect, test } from "@playwright/test";

test("工作台冒烟：可加载概况并进入学生中心", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "先判断系统能不能试用，再进入具体工作" })).toBeVisible();
  await expect(page.locator(".page-chip-row").first()).toContainText("3");
  await expect(page.getByRole("heading", { name: "最近考试与成绩状态" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "最近导入" })).toBeVisible();

  await page.getByRole("button", { name: "学生中心", exact: true }).click();

  await expect(page).toHaveURL(/\/students$/);
  await expect(page.getByRole("heading", { name: "学生中心" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "学生列表" })).toBeVisible();
});
