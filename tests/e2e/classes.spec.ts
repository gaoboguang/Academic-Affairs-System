import { expect, test } from "@playwright/test";

test("年级班级主流程：进入班级详情、维护荣誉并跳转学生", async ({ page }) => {
  await page.goto("/classes");

  await expect(page.getByRole("heading", { name: "年级班级" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "高一" })).toBeVisible();
  await expect(page.getByText("1班").first()).toBeVisible();

  await page.locator(".class-card").filter({ hasText: "1班" }).getByRole("button", { name: "详情" }).click();

  await expect(page).toHaveURL(/\/classes\/\d+$/);
  await expect(page.getByRole("heading", { name: "1班" })).toBeVisible();
  await expect(page.getByText("班主任李语文", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "新增荣誉" }).first().click();
  const honorDialog = page.getByRole("dialog", { name: "新增荣誉" });
  await expect(honorDialog).toBeVisible();
  await honorDialog.locator(".el-form-item").filter({ hasText: "荣誉标题" }).locator("input").fill("E2E 文明班集体");
  await honorDialog.locator(".el-form-item").filter({ hasText: "级别" }).locator("input").fill("校级");
  await honorDialog.locator(".el-form-item").filter({ hasText: "获奖日期" }).locator("input").fill("2026-05-02");
  await honorDialog.locator(".el-form-item").filter({ hasText: "来源" }).locator("input").fill("年级组");
  await honorDialog.getByRole("button", { name: "保存" }).click();

  await expect(page.getByText("班级荣誉保存成功")).toBeVisible();
  await page.getByRole("tab", { name: "荣誉" }).click();
  await expect(page.getByRole("cell", { name: "E2E 文明班集体" })).toBeVisible();

  await page.getByRole("tab", { name: "学生" }).click();
  await page.getByRole("button", { name: "张三" }).click();
  await expect(page).toHaveURL(/\/students\/\d+$/);
  await expect(page.getByRole("heading", { name: "张三" })).toBeVisible();
});

test("年级详情展示班级矩阵并可回到班级详情", async ({ page }) => {
  await page.goto("/classes");
  await page.getByRole("button", { name: "年级详情" }).first().click();

  await expect(page).toHaveURL(/\/grades\/\d+$/);
  await expect(page.getByRole("heading", { name: "高一" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "班级横向矩阵" })).toBeVisible();

  await page.getByRole("button", { name: "1班" }).click();
  await expect(page).toHaveURL(/\/classes\/\d+$/);
  await expect(page.getByRole("heading", { name: "1班" })).toBeVisible();
});

test("年级班级速览可直接设置任课教师", async ({ page }) => {
  await page.goto("/classes");

  await page.locator(".class-card").filter({ hasText: "2班" }).getByRole("button", { name: "设置任课" }).click();
  await expect(page).toHaveURL(/\/classes\/\d+\?tab=teachers&action=assignment$/);
  await expect(page.getByRole("tab", { name: "任课教师" })).toHaveAttribute("aria-selected", "true");

  const dialog = page.getByRole("dialog", { name: "新增任教关系" });
  await expect(dialog).toBeVisible();

  await dialog.locator(".el-form-item").filter({ hasText: "教师" }).locator(".el-select").click();
  await page.getByRole("option", { name: "李语文" }).last().click();
  await dialog.locator(".el-form-item").filter({ hasText: "学科" }).locator(".el-select").click();
  await page.getByRole("option", { name: "语文" }).last().click();
  await dialog.locator(".el-form-item").filter({ hasText: "周课时" }).locator("input").fill("5");
  await dialog.getByRole("button", { name: "保存" }).click();

  await expect(page.getByText("任教关系保存成功")).toBeVisible();
  await expect(page.getByRole("cell", { name: "李语文" })).toBeVisible();

  await page.goto("/classes");
  await expect(page.locator(".class-card").filter({ hasText: "2班" }).getByText("任课已维护")).toBeVisible();
});

test("年级班级顶部可进入教师中心批量维护任课", async ({ page }) => {
  await page.goto("/classes");

  await page.getByRole("button", { name: "批量维护任课" }).click();
  await expect(page).toHaveURL(/\/teachers\?assignments=1$/);
  await expect(page.getByRole("dialog", { name: "任教关系维护" })).toBeVisible();
});
