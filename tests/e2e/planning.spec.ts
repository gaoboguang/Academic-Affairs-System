import { expect, test } from "@playwright/test";
import {
  e2eExamName,
  ensureExamWithScores,
  expectToast,
  selectDropdownOption,
} from "./helpers/localEduE2e";

test("升学规划任务中心：建目标、生成任务、完成任务并导出跟进表", async ({ page }) => {
  test.setTimeout(90000);

  await ensureExamWithScores(page);

  await page.request.post("/api/gaokao/pathways/bootstrap-shandong", {
    params: { target_year: 2026 },
  });
  await page.request.put("/api/gaokao/students/1/pathway-profile", {
    data: {
      province: "山东",
      candidate_type: "general",
      has_gaokao_registration: true,
      subject_combination: "物理,化学,生物",
      materials_json: {},
    },
  });

  await page.goto("/students/1?tab=planning");
  await expect(page.getByRole("heading", { name: /张三/ })).toBeVisible();
  const planningPanel = page.locator(".student-planning-panel");
  await expect(planningPanel.getByRole("heading", { name: "升学规划" })).toBeVisible();

  await planningPanel.getByRole("button", { name: "保存目标" }).click();
  await expectToast(page, "升学目标已保存");
  await expect(planningPanel.locator(".planning-row").filter({ hasText: "普通类常规批" }).first()).toBeVisible();

  await page.goto("/gaokao-pathways?student_id=1");
  await expect(page.getByRole("heading", { name: "山东升学方案中心" })).toBeVisible();
  await page.getByRole("button", { name: "生成规划任务" }).click();
  await expectToast(page, "已生成");

  await expect(page.getByRole("heading", { name: /张三/ })).toBeVisible();
  await expect(planningPanel.getByRole("heading", { name: "任务清单" })).toBeVisible();
  const taskRow = planningPanel.locator(".el-table__row").filter({ hasText: "复核" }).first();
  await expect(taskRow).toBeVisible();
  await taskRow.getByRole("button", { name: "完成" }).click();
  await expectToast(page, "任务已完成");

  await page.goto("/reports");
  await expect(page.getByRole("heading", { name: "输出中心" })).toBeVisible();
  const reportPanel = page.locator(".panel-block").filter({ hasText: "报表参数" });
  const selects = reportPanel.locator(".filter-grid .el-select");
  await selectDropdownOption(page, selects.first(), "学生升学规划跟进表");
  await selectDropdownOption(page, selects.nth(1), e2eExamName);
  await selectDropdownOption(page, selects.nth(2), "2026001 - 张三");
  await expect(reportPanel.getByText("当前报表还缺少")).toHaveCount(0);

  const printPreviewPopupPromise = page.waitForEvent("popup", { timeout: 5000 }).catch(() => null);
  await reportPanel.getByRole("button", { name: "打印预览" }).click();
  const printPreviewPopup = await printPreviewPopupPromise;
  if (printPreviewPopup) {
    await expect(printPreviewPopup.getByText("学生升学规划跟进表")).toBeVisible();
    await printPreviewPopup.close();
  }

  const exportPopupPromise = page.waitForEvent("popup", { timeout: 5000 }).catch(() => null);
  await reportPanel.getByRole("button", { name: "生成报表" }).click();
  const exportPopup = await exportPopupPromise;
  if (exportPopup) {
    await exportPopup.close();
  }

  await expectToast(page, "报表已生成");
  await expect(page.locator(".el-table__row").filter({ hasText: "学生升学规划跟进表" }).first()).toBeVisible();
});
