import { expect, test } from "@playwright/test";
import {
  confirmDialogIfVisible,
  e2eExamName,
  ensureCrossProvinceAdmissionsImported,
  ensureStudentOriginProvince,
  expectToast,
  generateRecommendationScheme,
  openRecommendationCenter,
  selectDropdownOption,
  setRecommendationFormForE2E,
} from "./helpers/localEduE2e";

test("推荐主流程：导入录取数据、生成方案并导出推荐报告", async ({ page }) => {
  const generatePanel = await openRecommendationCenter(page);
  await generateRecommendationScheme(page, generatePanel, { name: "E2E-推荐主流程-基准方案" });

  await expectToast(page, "推荐方案生成成功");
  await expect(page.getByRole("heading", { name: "方案结果" })).toBeVisible();

  const printPreviewPopupPromise = page.waitForEvent("popup", { timeout: 5000 }).catch(() => null);
  await page.getByRole("button", { name: "打印预览" }).click();
  await confirmDialogIfVisible(page, "打印前复核", "仍要打印");
  const printPreviewPopup = await printPreviewPopupPromise;
  if (printPreviewPopup) {
    await expect(printPreviewPopup.getByText("推荐报告打印预览")).toBeVisible();
    await printPreviewPopup.close();
  }

  const popupPromise = page.waitForEvent("popup", { timeout: 5000 }).catch(() => null);
  await page.getByRole("button", { name: "导出推荐单" }).click();
  await confirmDialogIfVisible(page, "导出前复核", "仍要导出");
  const popup = await popupPromise;
  if (popup) {
    await popup.close();
  }

  await expectToast(page, "推荐报告已生成");
});

test("推荐导出失败回退：导出报错后仍保留当前方案并可继续打印", async ({ page }) => {
  const generatePanel = await openRecommendationCenter(page);
  await generateRecommendationScheme(page, generatePanel, { name: "E2E-推荐导出失败-基线方案" });

  await expectToast(page, "推荐方案生成成功");
  const resultPanel = page.locator(".panel-block").filter({ hasText: "方案结果" });
  await expect(resultPanel.getByText("E2E-推荐导出失败-基线方案")).toBeVisible();

  await page.route("**/api/reports/export", async (route) => {
    await route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ detail: "推荐报告导出模拟失败" }),
    });
  });

  await page.getByRole("button", { name: "导出推荐单" }).click();
  await confirmDialogIfVisible(page, "导出前复核", "仍要导出");
  await expectToast(page, "导出推荐报告失败。原因：推荐报告导出模拟失败");
  await expect(resultPanel.getByText("E2E-推荐导出失败-基线方案")).toBeVisible();
  await expect(resultPanel.getByRole("button", { name: "打印预览" })).toBeEnabled();

  const printPreviewPopupPromise = page.waitForEvent("popup", { timeout: 5000 }).catch(() => null);
  await resultPanel.getByRole("button", { name: "打印预览" }).click();
  await confirmDialogIfVisible(page, "打印前复核", "仍要打印");
  const printPreviewPopup = await printPreviewPopupPromise;
  if (printPreviewPopup) {
    await expect(printPreviewPopup.getByText("推荐报告打印预览")).toBeVisible();
    await printPreviewPopup.close();
  }
});

test("推荐空状态：按无历史学生筛选时显示空历史", async ({ page }) => {
  await openRecommendationCenter(page);

  await page.getByRole("button", { name: "历史方案" }).click();
  const historyPanel = page.locator(".panel-block").filter({ hasText: "推荐历史" });
  await selectDropdownOption(page, historyPanel.locator(".filter-grid .el-select").first(), "2026002 - 李四");
  await historyPanel.getByRole("button", { name: "查询历史" }).click();

  await expect(historyPanel.getByText("暂无推荐历史")).toBeVisible();
});

test("推荐策略模板：可保存、应用并删除模板", async ({ page }) => {
  await openRecommendationCenter(page);

  const strategyPanel = page.locator(".panel-block").filter({ hasText: "推荐策略" });
  const safeInput = strategyPanel.getByPlaceholder("保底阈值");
  const steadyInput = strategyPanel.getByPlaceholder("稳妥阈值");
  const rushInput = strategyPanel.getByPlaceholder("冲刺阈值");
  const presetName = `E2E-策略模板-${Date.now()}`;

  await safeInput.fill("0.83");
  await steadyInput.fill("0.97");
  await rushInput.fill("1.11");

  const whitelistSelect = strategyPanel.locator(".strategy-filter-grid .el-select").first();
  await selectDropdownOption(page, whitelistSelect, "岭南科技大学");
  await page.keyboard.press("Escape");

  await strategyPanel.getByPlaceholder("模板名称").fill(presetName);
  await strategyPanel.getByPlaceholder("模板说明，可选").fill("E2E 策略模板说明");
  await strategyPanel.getByRole("button", { name: "保存为模板" }).click();
  await expectToast(page, "策略模板已保存");

  const presetCard = strategyPanel.locator(".preset-card").filter({ hasText: presetName }).first();
  await expect(presetCard).toBeVisible();

  await safeInput.fill("0.72");
  await steadyInput.fill("0.9");
  await rushInput.fill("1.2");
  await presetCard.click();
  await strategyPanel.getByRole("button", { name: "应用模板" }).click();
  await confirmDialogIfVisible(page, "应用策略模板", "继续应用");
  await expectToast(page, `已应用模板：${presetName}`);
  await expect(safeInput).toHaveValue("0.83");
  await expect(steadyInput).toHaveValue("0.97");
  await expect(rushInput).toHaveValue("1.11");

  await strategyPanel.getByRole("button", { name: "删除模板" }).click();
  const confirmDialog = page.locator('[role="dialog"]').filter({ hasText: "删除策略模板" });
  await expect(confirmDialog).toBeVisible();
  await confirmDialog.getByRole("button", { name: "确定" }).click();
  await expectToast(page, "策略模板已删除");
  await expect(strategyPanel.locator(".preset-card").filter({ hasText: presetName })).toHaveCount(0);
});

test("推荐对比：可生成多版方案并查看单方案和批量差异", async ({ page }) => {
  const generatePanel = await openRecommendationCenter(page, { ensureDefaultOriginProvince: false });

  await generateRecommendationScheme(page, generatePanel, {
    name: "E2E-推荐对比-软件方案",
    majorKeyword: "软件",
  });
  await expectToast(page, "推荐方案生成成功");

  await generateRecommendationScheme(page, generatePanel, {
    name: "E2E-推荐对比-信息方案",
    majorKeyword: "信息",
  });
  await expectToast(page, "推荐方案生成成功");

  await generateRecommendationScheme(page, generatePanel, {
    name: "E2E-推荐对比-全量方案",
    majorKeyword: "",
  });
  await expectToast(page, "推荐方案生成成功");

  const resultPanel = page.locator(".panel-block").filter({ hasText: "方案结果" });
  await expect(resultPanel.getByText("E2E-推荐对比-全量方案")).toBeVisible();

  const comparisonSelects = resultPanel.locator(".comparison-controls .el-select");
  await selectDropdownOption(page, comparisonSelects.first(), "E2E-推荐对比-软件方案");
  await expect(resultPanel.locator(".comparison-summary-card").filter({ hasText: "新增志愿" })).toContainText("2");
  await expect(resultPanel.locator(".comparison-column").filter({ hasText: "新增" })).toContainText("湾区信息大学");
  await expect(resultPanel.locator(".comparison-column").filter({ hasText: "新增" })).toContainText("南方应用大学");

  await comparisonSelects.nth(1).click();
  await page.locator(".el-select-dropdown:visible .el-select-dropdown__item").filter({ hasText: "E2E-推荐对比-软件方案" }).first().click();
  await page.locator(".el-select-dropdown:visible .el-select-dropdown__item").filter({ hasText: "E2E-推荐对比-信息方案" }).first().click();
  await page.keyboard.press("Escape");

  await expect(resultPanel.locator(".el-table__row").filter({ hasText: "E2E-推荐对比-软件方案" }).first()).toBeVisible();
  await expect(resultPanel.locator(".el-table__row").filter({ hasText: "E2E-推荐对比-信息方案" }).first()).toBeVisible();
});

test("推荐失败回退：无匹配结果时报错后仍可保留旧方案并继续生成", async ({ page }) => {
  const generatePanel = await openRecommendationCenter(page);

  await generateRecommendationScheme(page, generatePanel, { name: "E2E-推荐回退-基线方案" });
  await expectToast(page, "推荐方案生成成功");

  const resultPanel = page.locator(".panel-block").filter({ hasText: "方案结果" });
  await expect(resultPanel.getByText("E2E-推荐回退-基线方案")).toBeVisible();

  await generateRecommendationScheme(page, generatePanel, {
    name: "E2E-推荐回退-无结果方案",
    majorKeyword: "不存在的专业方向",
  });
  await expectToast(page, "当前条件下暂无可推荐的录取数据");
  await expect(resultPanel.getByText("E2E-推荐回退-基线方案")).toBeVisible();

  await generateRecommendationScheme(page, generatePanel, {
    name: "E2E-推荐回退-恢复方案",
    majorKeyword: "软件",
  });
  await expectToast(page, "推荐方案生成成功");
  await expect(resultPanel.getByText("E2E-推荐回退-恢复方案")).toBeVisible();
});

test("推荐历史回放：可从历史记录重新载入已有方案", async ({ page }) => {
  const generatePanel = await openRecommendationCenter(page);

  await generateRecommendationScheme(page, generatePanel, {
    name: "E2E-历史回放-软件方案",
    majorKeyword: "软件",
  });
  await expectToast(page, "推荐方案生成成功");

  await generateRecommendationScheme(page, generatePanel, {
    name: "E2E-历史回放-信息方案",
    majorKeyword: "信息",
  });
  await expectToast(page, "推荐方案生成成功");

  await page.getByRole("button", { name: "历史方案" }).click();
  const historyPanel = page.locator(".panel-block").filter({ hasText: "推荐历史" });
  const resultPanel = page.locator(".panel-block").filter({ hasText: "方案结果" });
  await historyPanel.getByRole("button", { name: "查询历史" }).click();

  await historyPanel
    .locator(".el-table__row")
    .filter({ hasText: "E2E-历史回放-软件方案" })
    .first()
    .getByRole("button", { name: "查看" })
    .click();
  await expect(resultPanel.getByText("E2E-历史回放-软件方案")).toBeVisible();
  await expect(resultPanel.locator(".result-column").filter({ hasText: "软件工程" }).first()).toBeVisible();

  await historyPanel
    .locator(".el-table__row")
    .filter({ hasText: "E2E-历史回放-信息方案" })
    .first()
    .getByRole("button", { name: "查看" })
    .click();
  await expect(resultPanel.getByText("E2E-历史回放-信息方案")).toBeVisible();
  await expect(resultPanel.locator(".result-column").filter({ hasText: "南方应用大学" }).first()).toBeVisible();
});

test("Stage B 批量场景：混合生源地学生可分别生成方案并写入历史", async ({ page }) => {
  await ensureStudentOriginProvince(page, 1, "山东");
  await ensureStudentOriginProvince(page, 2, "河北");

  const generatePanel = await openRecommendationCenter(page, { ensureDefaultOriginProvince: false });
  await page.getByRole("button", { name: "打开数据与规则" }).click();
  await page.getByRole("tab", { name: "录取库" }).click();
  await ensureCrossProvinceAdmissionsImported(page);
  await page.getByRole("button", { name: "回到工作台" }).click();
  await page.getByRole("tab", { name: "推荐中心" }).click();

  await generatePanel.locator(".el-radio-button").filter({ hasText: "批量学生" }).first().click();
  const generateSelects = generatePanel.locator(".filter-grid .el-select");
  const batchSchemeName = `E2E-StageB-批量跨省-${Date.now()}`;

  await selectDropdownOption(page, generateSelects.nth(0), "2026001 - 张三");
  await selectDropdownOption(page, generateSelects.nth(0), "2026002 - 李四");
  await setRecommendationFormForE2E(generatePanel, { student_ids: [1, 2], province: "" });
  await expect(page.getByText("已选 2 名学生")).toBeVisible();
  await selectDropdownOption(page, generateSelects.nth(1), e2eExamName);
  await generatePanel.getByPlaceholder("方案名称，可选").fill(batchSchemeName);

  await expect(generatePanel.getByText("按各学生档案中的生源地分别生成")).toBeVisible();
  await expect(generatePanel.getByText("山东 / 河北")).toBeVisible();
  await generatePanel.getByRole("button", { name: "批量生成" }).click();
  await confirmDialogIfVisible(page, "生成前复核", "继续生成");

  await expectToast(page, "批量推荐完成，已按 2 个生源地分别生成");
  await expect(
    generatePanel.getByText("批量推荐完成，已按 2 个生源地分别生成，共生成 2 个方案，累计 2 条结果，覆盖 2 个生源地。"),
  ).toBeVisible();

  await page.getByRole("button", { name: "历史方案" }).click();
  const historyPanel = page.locator(".panel-block").filter({ hasText: "推荐历史" });
  const historyStudentSelect = historyPanel.locator(".filter-grid .el-select").first();

  await selectDropdownOption(page, historyStudentSelect, "2026001 - 张三");
  await historyPanel.getByRole("button", { name: "查询历史" }).click();
  await expect(historyPanel.locator(".el-table__row").filter({ hasText: batchSchemeName }).first()).toContainText("山东");

  await selectDropdownOption(page, historyStudentSelect, "2026002 - 李四");
  await historyPanel.getByRole("button", { name: "查询历史" }).click();
  await expect(historyPanel.locator(".el-table__row").filter({ hasText: batchSchemeName }).first()).toContainText("河北");
});

test("推荐异常提示：缺少学生与考试时阻止生成", async ({ page }) => {
  await page.goto("/recommendations");
  await expect(page.getByRole("heading", { name: "高考志愿" })).toBeVisible();

  await page.getByRole("tab", { name: "推荐中心" }).click();
  const generatePanel = page.locator(".panel-block").filter({ hasText: "生成推荐方案" }).first();
  await generatePanel.getByRole("button", { name: "生成推荐" }).click();

  await expectToast(page, "单个学生推荐需要学生和考试");
});
