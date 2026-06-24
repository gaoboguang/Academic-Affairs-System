import { expect, test } from "@playwright/test";
import {
  apiPost,
  createVolunteerDraft,
  e2eExamName,
  ensureExamWithScores,
  expectToast,
  selectDropdownOption,
} from "./helpers/localEduE2e";

test("报表主流程：导出学生分析单并写入导出记录", async ({ page }) => {
  await ensureExamWithScores(page);

  await page.goto("/reports");
  await expect(page.getByRole("heading", { name: "报表中心" })).toBeVisible();

  const reportPanel = page.locator(".panel-block").filter({ hasText: "报表参数" });
  const selects = reportPanel.locator(".filter-grid .el-select");

  await selects.nth(1).click();
  await page.locator(".el-select-dropdown__item").filter({ hasText: e2eExamName }).last().click();

  await selects.nth(2).click();
  await page.locator(".el-select-dropdown__item").filter({ hasText: "2026001 - 张三" }).last().click();

  await expect(reportPanel.getByText("当前报表还缺少：考试")).toHaveCount(0);

  const printPreviewPopupPromise = page.waitForEvent("popup", { timeout: 5000 }).catch(() => null);
  await reportPanel.getByRole("button", { name: "打印预览" }).click();
  const printPreviewPopup = await printPreviewPopupPromise;
  if (printPreviewPopup) {
    await expect(printPreviewPopup.getByText("学生成绩分析单打印预览")).toBeVisible();
    await printPreviewPopup.close();
  }

  const popupPromise = page.waitForEvent("popup", { timeout: 5000 }).catch(() => null);
  await reportPanel.getByRole("button", { name: "生成报表" }).click();
  const popup = await popupPromise;
  if (popup) {
    await popup.close();
  }

  await expect(page.locator(".el-table__row").filter({ hasText: "学生成绩分析单" }).first()).toBeVisible();
});

test("报表打印扩展：班级/年级/教师分析预览可打开", async ({ page }) => {
  await ensureExamWithScores(page);

  await page.goto("/reports");
  await expect(page.getByRole("heading", { name: "报表中心" })).toBeVisible();

  const reportPanel = page.locator(".panel-block").filter({ hasText: "报表参数" });
  const reportTypeSelect = reportPanel.locator(".filter-grid .el-select").first();

  await reportTypeSelect.click();
  await page.locator(".el-select-dropdown__item").filter({ hasText: "班级成绩分析报表" }).last().click();
  await reportPanel.locator(".filter-grid .el-select").nth(1).click();
  await page.locator(".el-select-dropdown__item").filter({ hasText: e2eExamName }).last().click();
  await reportPanel.locator(".filter-grid .el-select").nth(2).click();
  await page.locator(".el-select-dropdown__item").filter({ hasText: "1班" }).last().click();
  const classPrintPopupPromise = page.waitForEvent("popup", { timeout: 5000 }).catch(() => null);
  await reportPanel.getByRole("button", { name: "打印预览" }).click();
  const classPrintPopup = await classPrintPopupPromise;
  if (classPrintPopup) {
    await expect(classPrintPopup.getByText("班级成绩分析报表打印预览")).toBeVisible();
    await classPrintPopup.close();
  }

  await reportTypeSelect.click();
  await page.locator(".el-select-dropdown__item").filter({ hasText: "年级成绩汇总表" }).last().click();
  await reportPanel.locator(".filter-grid .el-select").nth(1).click();
  await page.locator(".el-select-dropdown__item").filter({ hasText: e2eExamName }).last().click();
  await reportPanel.locator(".filter-grid .el-select").nth(2).click();
  await page.locator(".el-select-dropdown__item").filter({ hasText: "高一" }).last().click();
  const gradePrintPopupPromise = page.waitForEvent("popup", { timeout: 5000 }).catch(() => null);
  await reportPanel.getByRole("button", { name: "打印预览" }).click();
  const gradePrintPopup = await gradePrintPopupPromise;
  if (gradePrintPopup) {
    await expect(gradePrintPopup.getByText("年级汇总表打印预览")).toBeVisible();
    await gradePrintPopup.close();
  }

  await reportTypeSelect.click();
  await page.locator(".el-select-dropdown__item").filter({ hasText: "教师任教分析报表" }).last().click();
  await reportPanel.locator(".filter-grid .el-select").nth(1).click();
  await page.locator(".el-select-dropdown__item").filter({ hasText: e2eExamName }).last().click();
  await reportPanel.locator(".filter-grid .el-select").nth(2).click();
  await page.locator(".el-select-dropdown__item").filter({ hasText: "李语文" }).last().click();
  const teacherPrintPopupPromise = page.waitForEvent("popup", { timeout: 5000 }).catch(() => null);
  await reportPanel.getByRole("button", { name: "打印预览" }).click();
  const teacherPrintPopup = await teacherPrintPopupPromise;
  if (teacherPrintPopup) {
    await expect(teacherPrintPopup.getByText("教师任教分析报表打印预览")).toBeVisible();
    await teacherPrintPopup.close();
  }
});

test("报表打印扩展：工作量/评教/班主任量化预览可打开", async ({ page }) => {
  await page.goto("/reports");
  await expect(page.getByRole("heading", { name: "报表中心" })).toBeVisible();

  const reportPanel = page.locator(".panel-block").filter({ hasText: "报表参数" });
  const reportTypeSelect = reportPanel.locator(".filter-grid .el-select").first();

  await reportTypeSelect.click();
  await page.locator(".el-select-dropdown__item").filter({ hasText: "教师课时与工作量报表" }).last().click();
  await reportPanel.locator(".filter-grid .el-select").nth(1).click();
  await page.locator(".el-select-dropdown__item").filter({ hasText: "2025-2026 下学期" }).last().click();
  const workloadPrintPopupPromise = page.waitForEvent("popup", { timeout: 5000 }).catch(() => null);
  await reportPanel.getByRole("button", { name: "打印预览" }).click();
  const workloadPrintPopup = await workloadPrintPopupPromise;
  if (workloadPrintPopup) {
    await expect(workloadPrintPopup.getByText("教师课时与工作量报表打印预览")).toBeVisible();
    await workloadPrintPopup.close();
  }

  await reportTypeSelect.click();
  await page.locator(".el-select-dropdown__item").filter({ hasText: "评教汇总报表" }).last().click();
  await reportPanel.locator(".filter-grid .el-select").nth(1).click();
  await page.locator(".el-select-dropdown__item").filter({ hasText: "通用课堂评教模板" }).last().click();
  const evaluationPrintPopupPromise = page.waitForEvent("popup", { timeout: 5000 }).catch(() => null);
  await reportPanel.getByRole("button", { name: "打印预览" }).click();
  const evaluationPrintPopup = await evaluationPrintPopupPromise;
  if (evaluationPrintPopup) {
    await expect(evaluationPrintPopup.getByText("评教汇总报表打印预览")).toBeVisible();
    await evaluationPrintPopup.close();
  }

  await reportTypeSelect.click();
  await page.locator(".el-select-dropdown__item").filter({ hasText: "班主任量化报表" }).last().click();
  await reportPanel.locator(".filter-grid .el-select").nth(1).click();
  await page.locator(".el-select-dropdown__item").filter({ hasText: "2025-2026 下学期" }).last().click();
  const adviserPrintPopupPromise = page.waitForEvent("popup", { timeout: 5000 }).catch(() => null);
  await reportPanel.getByRole("button", { name: "打印预览" }).click();
  const adviserPrintPopup = await adviserPrintPopupPromise;
  if (adviserPrintPopup) {
    await expect(adviserPrintPopup.getByText("班主任量化报表打印预览")).toBeVisible();
    await adviserPrintPopup.close();
  }
});

test("报表中心：可按志愿草稿打印预览并导出报表", async ({ page }) => {
  test.setTimeout(90000);
  const { draftName } = await createVolunteerDraft(page);

  await page.goto("/reports");
  await expect(page.getByRole("heading", { name: "报表中心" })).toBeVisible();

  const reportPanel = page.locator(".panel-block").filter({ hasText: "报表参数" });
  const selects = reportPanel.locator(".filter-grid .el-select");

  await selectDropdownOption(page, selects.first(), "学生志愿草稿");
  await selectDropdownOption(page, selects.nth(1), draftName);
  await expect(reportPanel.getByText("当前报表还缺少")).toHaveCount(0);

  const printPreviewPopupPromise = page.waitForEvent("popup", { timeout: 5000 }).catch(() => null);
  await reportPanel.getByRole("button", { name: "打印预览" }).click();
  const printPreviewPopup = await printPreviewPopupPromise;
  if (printPreviewPopup) {
    await expect(printPreviewPopup.getByText("志愿草稿打印预览")).toBeVisible();
    await printPreviewPopup.close();
  }

  const exportPopupPromise = page.waitForEvent("popup", { timeout: 5000 }).catch(() => null);
  await reportPanel.getByRole("button", { name: "生成报表" }).click();
  const exportPopup = await exportPopupPromise;
  if (exportPopup) {
    await exportPopup.close();
  }

  await expectToast(page, "报表已生成");
  await expect(page.locator(".el-table__row").filter({ hasText: "学生志愿草稿" }).first()).toBeVisible();
});

test("报表中心：推荐报告与志愿草稿在导出前显示摘要", async ({ page }) => {
  test.setTimeout(90000);
  const schemeName = `E2E-报表摘要-推荐-${Date.now()}`;
  const { draftName } = await createVolunteerDraft(page);
  const examsResponse = await page.request.get("/api/exams?page=1&page_size=100");
  expect(examsResponse.ok()).toBeTruthy();
  const examsPayload = (await examsResponse.json()) as { items: Array<{ id: number; name: string }> };
  const currentExam = examsPayload.items.find((item) => item.name === e2eExamName);
  expect(currentExam).toBeTruthy();

  const generateResponse = await apiPost(page, "/api/recommendations/generate", {
    data: {
      student_id: 1,
      exam_id: currentExam?.id,
      name: schemeName,
      province: "广东",
      score_input_mode: "estimated_score_and_rank",
      student_rank_override: 31000,
      comprehensive_score: 582,
      reference_exam_name: "2026届一模",
      use_historical_mapping: true,
      risk_preference: "balanced",
    },
  });
  expect(generateResponse.ok()).toBeTruthy();

  await page.goto("/reports");
  await expect(page.getByRole("heading", { name: "报表中心" })).toBeVisible();

  const reportPanel = page.locator(".panel-block").filter({ hasText: "报表参数" });
  await selectDropdownOption(page, reportPanel.locator(".filter-grid .el-select").first(), "学生推荐报告");
  await selectDropdownOption(page, reportPanel.locator(".filter-grid .el-select").nth(1), "2026001 - 张三");
  await selectDropdownOption(page, reportPanel.locator(".filter-grid .el-select").nth(2), schemeName);

  const recommendationInsightSection = reportPanel.locator(".report-insight-section");
  await expect(recommendationInsightSection).toBeVisible();
  await expect(recommendationInsightSection.locator(".report-insight-card").first()).toBeVisible();
  await expect(recommendationInsightSection).toContainText("推荐");

  await selectDropdownOption(page, reportPanel.locator(".filter-grid .el-select").first(), "学生志愿草稿");
  await selectDropdownOption(page, reportPanel.locator(".filter-grid .el-select").nth(1), draftName);

  const draftInsightSection = reportPanel.locator(".report-insight-section");
  await expect(draftInsightSection).toBeVisible();
  await expect(draftInsightSection.locator(".report-insight-card").first()).toBeVisible();
  await expect(draftInsightSection).toContainText("草稿");
});

test("报表异常提示：缺少必填参数时阻止导出", async ({ page }) => {
  await page.goto("/reports");
  await expect(page.getByRole("heading", { name: "报表中心" })).toBeVisible();

  const reportPanel = page.locator(".panel-block").filter({ hasText: "报表参数" });
  const selects = reportPanel.locator(".filter-grid .el-select");

  await selects.nth(2).click();
  await page.locator(".el-select-dropdown__item").filter({ hasText: "2026001 - 张三" }).last().click();

  await expect(reportPanel.getByText("当前报表还缺少：考试")).toBeVisible();
  await reportPanel.getByRole("button", { name: "生成报表" }).click();
  await expectToast(page, "请先补齐：考试");
});
