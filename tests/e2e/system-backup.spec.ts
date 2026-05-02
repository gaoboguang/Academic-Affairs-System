import { expect, test } from "@playwright/test";

test("系统设置主流程：创建备份后备份数量增加", async ({ page }) => {
  await page.goto("/system-tools");

  await expect(page.getByRole("heading", { name: "系统设置" })).toBeVisible();

  const backupCountLocator = page.locator(".app-stat-grid .stat-card").filter({ hasText: "备份数量" }).locator("strong");
  const initialBackupCount = Number((await backupCountLocator.textContent()) ?? "0");

  await page.getByRole("button", { name: "立即备份" }).click();
  await expect(page.getByText("备份完成")).toBeVisible();
  await expect(backupCountLocator).toHaveText(String(initialBackupCount + 1));

  await page.getByRole("tab", { name: "备份恢复" }).click();
  await expect(page.getByRole("heading", { name: "备份记录" })).toBeVisible();
  await expect(page.getByText("local_edu_backup", { exact: false }).first()).toBeVisible();
});
