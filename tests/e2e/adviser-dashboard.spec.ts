import { expect, test } from "@playwright/test";
import {
  e2eExamName,
  ensureExamWithScores,
  expectToast,
  selectDropdownOption,
} from "./helpers/localEduE2e";

test("班主任驾驶舱：按成绩成长规划查看风险学生并导出周报", async ({ page }) => {
  test.setTimeout(90000);

  await ensureExamWithScores(page);

  const removedAttendanceResponse = await page.request.get("/api/attendance/records");
  expect(removedAttendanceResponse.status()).toBe(404);
  const removedBehaviorResponse = await page.request.get("/api/behavior/records");
  expect(removedBehaviorResponse.status()).toBe(404);

  await page.request.post("/api/archives/students/1/records", {
    data: {
      occurred_on: "2026-04-20",
      record_type: "stage_review",
      title: "阶段学习复盘",
      content: "围绕近期成绩波动形成跟进记录。",
      owner_name: "李语文",
      attachment_file_ids: [],
      is_active: true,
    },
  });
  await page.request.post("/api/planning/goals", {
    data: {
      student_id: 1,
      target_year: 2026,
      pathway_code: "gaokao_regular",
      pathway_name: "普通类高考",
      status: "in_progress",
      priority: "high",
      is_active: true,
    },
  });
  await page.request.post("/api/planning/tasks", {
    data: {
      student_id: 1,
      source_type: "manual",
      task_type: "score_review",
      title: "复核阶段成绩波动",
      status: "in_progress",
      priority: "high",
      due_date: "2026-04-01",
      related_route: "/analytics",
      is_active: true,
    },
  });

  await page.goto("/import-center");
  await expect(page.getByRole("heading", { name: "统一查看模板、批次、错误报告和撤销说明" })).toBeVisible();
  await expect(page.getByText("6. 维护成长与规划")).toBeVisible();
  await expect(page.getByText("7. 查看驾驶舱")).toBeVisible();
  await expect(page.getByText("导入考勤")).toHaveCount(0);

  await page.goto("/analytics");
  await expect(page.getByRole("heading", { name: "分析中心" })).toBeVisible();

  const examPanel = page.locator(".panel-block").filter({ hasText: "选择考试" });
  await selectDropdownOption(page, examPanel.locator(".el-select").first(), e2eExamName);

  await page.getByRole("tab", { name: "班主任驾驶舱" }).click();
  const adviserPanel = page.locator(".panel-block").filter({ hasText: "班主任驾驶舱" }).first();
  const adviserSelects = adviserPanel.locator(".adviser-filter-grid .el-select");
  await selectDropdownOption(page, adviserSelects.nth(1), "1班");
  await adviserPanel.getByRole("button", { name: "加载驾驶舱" }).click();

  await expect(adviserPanel.getByRole("heading", { name: "成长档案" })).toBeVisible();
  await expect(adviserPanel.getByRole("heading", { name: "规划任务" })).toBeVisible();
  await expect(adviserPanel.getByText("本周行动清单")).toBeVisible();
  await expect(adviserPanel.locator(".adviser-summary-grid")).toContainText("记录");
  await expect(adviserPanel.locator(".adviser-summary-grid")).toContainText("逾期");

  const riskRow = adviserPanel.locator(".el-table__row").filter({ hasText: "张三" }).first();
  await expect(riskRow).toBeVisible();
  await expect(riskRow).toContainText("紧急跟进");
  await expect(riskRow).toContainText("升学规划逾期任务");
  await riskRow.getByRole("button", { name: "张三" }).click();

  await expect(page.getByRole("heading", { name: /张三/ })).toBeVisible();
  await expect(page.locator(".student-risk-card").filter({ hasText: "成长档案" })).toBeVisible();
  await expect(page.locator(".student-risk-card").filter({ hasText: "规划任务" })).toBeVisible();
  await expect(page.locator(".action-card").filter({ hasText: "学生跟进包" })).toBeVisible();

  await page.goto("/reports");
  await expect(page.getByRole("heading", { name: "报表中心" })).toBeVisible();

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
