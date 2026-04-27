import { expect, test } from "@playwright/test";

test("学生中心主流程：筛选后进入学生详情并查看附件页", async ({ page }) => {
  await page.goto("/students");

  await expect(page.getByRole("heading", { name: "学生中心" })).toBeVisible();
  await page.getByPlaceholder("按学号筛选").fill("2026001");
  await page.getByRole("button", { name: "查询" }).click();

  await expect(page.getByRole("cell", { name: "2026001" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "张三" })).toBeVisible();

  await page.getByRole("button", { name: "详情" }).click();

  await expect(page).toHaveURL(/\/students\/\d+$/);
  await expect(page.getByRole("heading", { name: "张三" })).toBeVisible();
  await expect(page.getByText("2026001")).toBeVisible();

  await page.getByRole("tab", { name: "附件" }).click();
  await expect(page.getByRole("heading", { name: "学生附件" })).toBeVisible();
});
