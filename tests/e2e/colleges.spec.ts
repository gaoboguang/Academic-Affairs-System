import { expect, test } from "@playwright/test";
import { ensureAdmissionsImported, ensureEnrollmentPlansImported } from "./helpers/localEduE2e";

test("院校库：可搜索院校并查看招生计划与录取历史", async ({ page }) => {
  await ensureAdmissionsImported(page);
  await ensureEnrollmentPlansImported(page);
  const collegeName = "岭南科技大学";

  await page.goto("/colleges");
  await expect(page.getByRole("heading", { name: "院校库" })).toBeVisible();

  await page.getByPlaceholder("院校名称或代码").fill(collegeName);
  await page.getByRole("button", { name: "查询" }).click();
  await expect(page.locator(".el-table__row").filter({ hasText: collegeName }).first()).toBeVisible();

  await page.locator(".el-table__row").filter({ hasText: collegeName }).first().getByRole("button", { name: collegeName }).click();
  await expect(page.getByRole("heading", { name: collegeName })).toBeVisible();
  await expect(page.getByRole("heading", { name: "招生数据" })).toBeVisible();

  await page.getByRole("tab", { name: "招生计划" }).click();
  await expect(page.getByRole("tabpanel", { name: "招生计划" }).getByRole("button", { name: "查询" })).toBeVisible();

  await page.getByRole("tab", { name: "录取/投档" }).click();
  await expect(page.getByRole("tabpanel", { name: "录取/投档" }).getByRole("button", { name: "查询" })).toBeVisible();
});
