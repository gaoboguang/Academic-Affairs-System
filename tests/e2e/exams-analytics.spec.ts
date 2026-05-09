import { expect, test } from "@playwright/test";
import {
  e2eExamName,
  e2eKnowledgeTrendExamOneName,
  e2eKnowledgeTrendExamTwoName,
  ensureExamWithScores,
  ensureExamWithSubjectsByApi,
  expectToast,
  importQuestionDetailsByApi,
  invalidScoresFixture,
  scoreQuestionDetailsFixture,
  scoreQuestionTrendFixtureOne,
  scoreQuestionTrendFixtureTwo,
  selectDropdownOption,
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

test("分析中心：导入题分明细后展示学生知识点诊断", async ({ page }) => {
  await ensureExamWithScores(page);
  await page.goto("/analytics");
  await expect(page.getByRole("heading", { name: "分析中心" })).toBeVisible();

  const examSelect = page.locator(".panel-block").filter({ hasText: "选择考试" }).locator(".el-select").first();
  await selectDropdownOption(page, examSelect, e2eExamName);

  await page.getByRole("tab", { name: "学生分析" }).click();
  const studentPanel = page.locator(".panel-block").filter({ hasText: "学生分析" });
  await selectDropdownOption(page, studentPanel.locator(".el-select").first(), "2026001 - 张三");

  await studentPanel
    .locator(".el-upload")
    .filter({ hasText: "导入题分明细" })
    .locator('input[type="file"]')
    .setInputFiles(scoreQuestionDetailsFixture);
  await expectToast(page, "题分明细导入完成");

  await studentPanel.getByRole("button", { name: "查询" }).click();
  const knowledgePanel = page.locator(".knowledge-panel");
  await expect(knowledgePanel.getByRole("heading", { name: "知识点诊断" })).toBeVisible();
  await expect(knowledgePanel.locator(".el-table__row").filter({ hasText: "函数单调性" }).first()).toContainText("优先补弱");
  await expect(knowledgePanel.locator(".el-table__row").filter({ hasText: "函数单调性" }).first()).toContainText("12、18");
  await expect(studentPanel.getByText("知识点清单")).toBeVisible();
});

test("分析中心：成绩报表展示本次考试学生单科和综合成绩", async ({ page }) => {
  await ensureExamWithScores(page);
  await page.goto("/analytics");
  await expect(page.getByRole("heading", { name: "分析中心" })).toBeVisible();

  const examSelect = page.locator(".panel-block").filter({ hasText: "选择考试" }).locator(".el-select").first();
  await selectDropdownOption(page, examSelect, e2eExamName);

  await page.getByRole("tab", { name: "成绩报表" }).click();
  const reportPanel = page.locator(".score-report-panel");
  await expect(reportPanel.getByRole("heading", { name: "成绩报表" })).toBeVisible();
  await reportPanel.getByRole("button", { name: "加载成绩报表" }).click();

  await expect(reportPanel.getByText("校内名次（本次有效导入样本）")).toBeVisible();
  const firstRow = reportPanel.locator(".el-table__row").filter({ hasText: "张三" }).first();
  await expect(firstRow).toBeVisible();
  await expect(firstRow).toContainText("2026001");
  await expect(firstRow).toContainText("118");
  await expect(firstRow).toContainText("125");
  await expect(firstRow).toContainText("243");
  await expect(reportPanel.getByText("学生数", { exact: true })).toBeVisible();
});

test("分析中心：多次题分明细可展示连续知识点趋势", async ({ page }) => {
  await ensureExamWithScores(page);
  const trendExamOneId = await ensureExamWithSubjectsByApi(page, e2eKnowledgeTrendExamOneName, "2026-02-10");
  const trendExamTwoId = await ensureExamWithSubjectsByApi(page, e2eKnowledgeTrendExamTwoName, "2026-03-10");
  await importQuestionDetailsByApi(page, trendExamOneId, scoreQuestionTrendFixtureOne);
  await importQuestionDetailsByApi(page, trendExamTwoId, scoreQuestionTrendFixtureTwo);

  await page.goto("/analytics");
  await expect(page.getByRole("heading", { name: "分析中心" })).toBeVisible();

  const examSelect = page.locator(".panel-block").filter({ hasText: "选择考试" }).locator(".el-select").first();
  await selectDropdownOption(page, examSelect, e2eExamName);

  await page.getByRole("tab", { name: "学生分析" }).click();
  const studentPanel = page.locator(".panel-block").filter({ hasText: "学生分析" });
  await selectDropdownOption(page, studentPanel.locator(".el-select").first(), "2026001 - 张三");

  await studentPanel
    .locator(".el-upload")
    .filter({ hasText: "导入题分明细" })
    .locator('input[type="file"]')
    .setInputFiles(scoreQuestionDetailsFixture);
  await expectToast(page, "题分明细导入完成");

  await studentPanel.getByRole("button", { name: "查询" }).click();
  const knowledgePanel = page.locator(".knowledge-panel");
  await expect(knowledgePanel.getByRole("heading", { name: "连续知识点趋势" })).toBeVisible();
  const trendRow = knowledgePanel.locator(".el-table__row").filter({ hasText: "函数单调性" }).filter({ hasText: "持续薄弱" }).first();
  await expect(trendRow).toBeVisible();
  await expect(trendRow).toContainText("E2E知识点趋势一");
  await expect(trendRow).toContainText("E2E知识点趋势二");
  await expect(studentPanel.getByText("连续薄弱")).toBeVisible();
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
  await page.goto("/exams");
  await expect(page.getByRole("heading", { name: "考试成绩中心" })).toBeVisible();
  const examRow = page.locator(".el-table__row").filter({ hasText: e2eExamName }).filter({ hasText: "导入成绩" }).first();
  await expect(examRow).toBeVisible();
  await examRow.getByRole("button", { name: "导入成绩" }).click();

  const importDialog = page.locator('[role="dialog"]').filter({ hasText: "导入成绩" });
  await expect(importDialog).toBeVisible();
  await importDialog
    .locator(".el-upload")
    .filter({ hasText: "按统一模板导入" })
    .locator('input[type="file"]')
    .setInputFiles(invalidScoresFixture);

  await expectToast(page, "成绩导入模板表头不匹配");
});
