import path from "node:path";

import { expect, test } from "@playwright/test";
import type { Locator, Page } from "@playwright/test";

const scoresFixture = path.resolve(process.cwd(), "tests/e2e/fixtures/scores-import.xlsx");
const invalidScoresFixture = path.resolve(process.cwd(), "tests/e2e/fixtures/scores-invalid.xlsx");
const admissionsFixture = path.resolve(process.cwd(), "tests/e2e/fixtures/admissions-import.xlsx");
const crossProvinceAdmissionsFixture = path.resolve(process.cwd(), "tests/e2e/fixtures/admissions-cross-province.xlsx");
const enrollmentPlansFixture = path.resolve(process.cwd(), "tests/e2e/fixtures/enrollment-plans-import.xlsx");
const e2eExamName = "2026届高一4月月考";
const gaokaoTargetYear = "2026";

interface VolunteerRuleOptions {
  province?: string;
  year?: string;
  examMode?: string;
  batch?: string;
  volunteerLimit?: number;
  volunteerUnitType?: string;
  note?: string;
}

interface VolunteerWorkbenchContextOptions {
  studentText?: string;
  examText?: string;
  batch?: string;
  examMode?: string;
  majorKeyword?: string;
  subjectCombination?: string;
  studentRankOverride?: string;
}

async function expectToast(page: Page, text: string): Promise<void> {
  await expect(page.locator(".el-message__content").filter({ hasText: text }).last()).toBeVisible();
}

async function selectDropdownOption(page: Page, select: Locator, optionText: string): Promise<void> {
  await select.click();
  const option = page.locator(".el-select-dropdown:visible .el-select-dropdown__item").filter({ hasText: optionText }).first();
  await expect(option).toBeVisible();
  await option.click();
}

async function confirmDialogIfVisible(
  page: Page,
  title: string,
  confirmText: string,
  timeout = 1500,
): Promise<boolean> {
  const dialog = page.getByRole("dialog", { name: title });
  try {
    await dialog.waitFor({ state: "visible", timeout });
  } catch {
    return false;
  }
  await dialog.getByRole("button", { name: confirmText }).click();
  await expect(dialog).toBeHidden();
  return true;
}

async function ensureExamWithScores(page: Page): Promise<void> {
  await page.goto("/exams");
  await expect(page.getByRole("heading", { name: "考试成绩中心" })).toBeVisible();

  const examRows = page.locator(".el-table__row").filter({ hasText: e2eExamName });
  if ((await examRows.count()) === 0) {
    const createButton = page.getByRole("button", { name: "新建考试" });
    await createButton.click();
    const examDialog = page.locator('[role="dialog"]').filter({ hasText: "新建考试" });
    if (!(await examDialog.isVisible().catch(() => false))) {
      await createButton.click();
    }
    await expect(examDialog).toBeVisible({ timeout: 15000 });

    await examDialog.locator(".el-form-item").filter({ hasText: "考试名称" }).locator("input").fill(e2eExamName);
    await examDialog.locator(".el-form-item").filter({ hasText: "考试日期" }).locator("input").fill("2026-04-10");
    await examDialog.locator(".el-form-item").filter({ hasText: "学期" }).locator(".el-select").click();
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("Enter");

    await examDialog.getByRole("button", { name: "保存" }).click();
    await expect(page.getByText("考试保存成功")).toBeVisible();
  }

  const examRow = page.locator(".el-table__row").filter({ hasText: e2eExamName }).first();
  await expect(examRow).toBeVisible();

  await examRow.getByRole("button", { name: "科目配置" }).click();
  const subjectDialog = page.locator('[role="dialog"]').filter({ hasText: "科目配置" });
  await expect(subjectDialog).toBeVisible();

  if ((await subjectDialog.locator(".el-table__row").count()) === 0) {
    await subjectDialog.getByRole("button", { name: "常规九科" }).click();
    await expect(subjectDialog.locator(".el-table__row").filter({ hasText: "语文" }).first()).toBeVisible();
    await expect(subjectDialog.locator(".el-table__row").filter({ hasText: "数学" }).first()).toBeVisible();
    await subjectDialog.getByRole("button", { name: "保存科目配置" }).click();
    await expect(page.getByText("考试科目保存成功")).toBeVisible();
  } else {
    await subjectDialog.getByRole("button", { name: "取消" }).click();
  }

  await examRow.getByRole("button", { name: "导入成绩" }).click();
  const importDialog = page.locator('[role="dialog"]').filter({ hasText: "导入成绩" });
  await expect(importDialog).toBeVisible();
  await importDialog.locator('input[type="file"]').setInputFiles(scoresFixture);
  await expect(importDialog.locator(".el-alert").getByText("成绩导入完成", { exact: false })).toBeVisible();
  await expect(importDialog.locator(".el-table__row").first()).toBeVisible();
}

async function ensureAdmissionsImported(page: Page): Promise<void> {
  const admissionsPanel = page.locator(".panel-block").filter({ hasText: "历年录取数据" });
  const targetAdmissionRow = admissionsPanel.locator(".el-table__row").filter({ hasText: "岭南科技大学" });
  if ((await targetAdmissionRow.count()) > 0) {
    return;
  }
  await admissionsPanel.locator('input[type="file"]').setInputFiles(admissionsFixture);
  await expect(page.getByText("成功 4 行", { exact: false })).toBeVisible();
  await expect(targetAdmissionRow.first()).toBeVisible();
}

async function ensureCrossProvinceAdmissionsImported(page: Page): Promise<void> {
  const admissionsPanel = page.locator(".panel-block").filter({ hasText: "历年录取数据" });
  const targetAdmissionRow = admissionsPanel.locator(".el-table__row").filter({ hasText: "华北信息大学" });
  if ((await targetAdmissionRow.count()) > 0) {
    return;
  }
  await admissionsPanel.locator('input[type="file"]').setInputFiles(crossProvinceAdmissionsFixture);
  await expect(page.getByText("成功 2 行", { exact: false })).toBeVisible();
  await expect(targetAdmissionRow.first()).toBeVisible();
}

async function ensureEnrollmentPlansImported(page: Page): Promise<void> {
  const enrollmentPlansPanel = page.locator(".panel-block").filter({ hasText: "招生计划库" });
  const targetPlanRow = enrollmentPlansPanel.locator(".el-table__row").filter({ hasText: "岭南科技大学" });
  if ((await targetPlanRow.count()) > 0) {
    return;
  }
  await enrollmentPlansPanel.locator('input[type="file"]').setInputFiles(enrollmentPlansFixture);
  await expect(page.getByText("成功 3 行", { exact: false })).toBeVisible();
  await expect(targetPlanRow.first()).toBeVisible();
}

async function ensureStudentOriginProvince(page: Page, studentId = 1, province = "广东"): Promise<void> {
  const detailResponse = await page.request.get(`/api/students/${studentId}`);
  expect(detailResponse.ok()).toBeTruthy();
  const payload = (await detailResponse.json()) as Record<string, unknown>;
  if (payload.origin_province === province) {
    return;
  }

  const updateResponse = await page.request.put(`/api/students/${studentId}`, {
    data: {
      ...payload,
      origin_province: province,
    },
  });
  expect(updateResponse.ok()).toBeTruthy();
  const updatedPayload = (await updateResponse.json()) as { origin_province?: string | null };
  expect(updatedPayload.origin_province).toBe(province);
}

async function ensureVolunteerRuleConfigured(page: Page, options: VolunteerRuleOptions = {}): Promise<void> {
  const config = {
    province: "广东",
    year: gaokaoTargetYear,
    examMode: "物理类",
    batch: "本科批",
    volunteerLimit: 45,
    volunteerUnitType: "院校专业组",
    note: "",
    ...options,
  };

  await page.getByRole("tab", { name: "省份规则" }).click();

  const rulesPanel = page.locator(".panel-block").filter({ hasText: "省份规则配置" });
  const targetRuleRow = rulesPanel
    .locator(".el-table__row")
    .filter({ hasText: config.province })
    .filter({ hasText: config.year })
    .filter({ hasText: config.batch })
    .filter({ hasText: config.examMode });
  if ((await targetRuleRow.count()) > 0) {
    const targetRow = targetRuleRow.first();
    const rowText = await targetRow.textContent();
    const needsUpdate = !rowText?.includes(String(config.volunteerLimit))
      || !rowText.includes(config.volunteerUnitType)
      || (config.note ? !rowText.includes(config.note) : false);
    if (!needsUpdate) {
      return;
    }

    await targetRow.getByRole("button", { name: "编辑" }).click();
    const dialog = page.locator('[role="dialog"]').filter({ hasText: "编辑省份规则" });
    await expect(dialog).toBeVisible();

    await selectDropdownOption(
      page,
      dialog.locator(".el-form-item").filter({ hasText: "年份" }).locator(".el-select"),
      config.year,
    );
    await selectDropdownOption(
      page,
      dialog.locator(".el-form-item").filter({ hasText: "高考模式" }).locator(".el-select"),
      config.examMode,
    );
    await dialog.getByRole("textbox", { name: "批次" }).fill(config.batch);
    await dialog.locator(".el-form-item").filter({ hasText: "志愿上限" }).locator("input").first().fill(String(config.volunteerLimit));
    await selectDropdownOption(
      page,
      dialog.locator(".el-form-item").filter({ hasText: "单位类型" }).locator(".el-select"),
      config.volunteerUnitType,
    );
    await dialog.locator(".el-form-item").filter({ hasText: "备注" }).locator("textarea").fill(config.note);
    await dialog.getByRole("button", { name: "保存" }).click();

    await expectToast(page, "省份规则保存成功");
    await expect(targetRuleRow.first()).toBeVisible();
    return;
  }

  await rulesPanel.getByRole("button", { name: "新增规则" }).click();
  const dialog = page.locator('[role="dialog"]').filter({ hasText: "新增省份规则" });
  await expect(dialog).toBeVisible();

  await selectDropdownOption(
    page,
    dialog.locator(".el-form-item").filter({ hasText: "年份" }).locator(".el-select"),
    config.year,
  );
  await selectDropdownOption(
    page,
    dialog.locator(".el-form-item").filter({ hasText: "高考模式" }).locator(".el-select"),
    config.examMode,
  );
  await dialog.getByRole("textbox", { name: "批次" }).fill(config.batch);
  await dialog.locator(".el-form-item").filter({ hasText: "志愿上限" }).locator("input").first().fill(String(config.volunteerLimit));
  await selectDropdownOption(
    page,
    dialog.locator(".el-form-item").filter({ hasText: "单位类型" }).locator(".el-select"),
    config.volunteerUnitType,
  );
  await dialog.locator(".el-form-item").filter({ hasText: "备注" }).locator("textarea").fill(config.note);
  await dialog.getByRole("button", { name: "保存" }).click();

  await expectToast(page, "省份规则保存成功");
  await expect(targetRuleRow.first()).toBeVisible();
}

async function fillVolunteerWorkbenchContext(
  page: Page,
  workbenchPanel: Locator,
  options: VolunteerWorkbenchContextOptions = {},
): Promise<void> {
  const config = {
    studentText: "2026001 - 张三",
    examText: e2eExamName,
    batch: "本科批",
    examMode: "物理类",
    majorKeyword: "",
    subjectCombination: "物理+化学",
    studentRankOverride: "31000",
    ...options,
  };

  const filterSelects = workbenchPanel.locator(".filter-grid .el-select");
  await selectDropdownOption(page, filterSelects.nth(0), config.studentText);
  await selectDropdownOption(page, filterSelects.nth(1), config.examText);
  await selectDropdownOption(page, filterSelects.nth(4), config.batch);
  await selectDropdownOption(page, filterSelects.nth(5), config.examMode);
  await workbenchPanel.getByPlaceholder("专业方向关键词，可选").fill(config.majorKeyword);
  await workbenchPanel.getByPlaceholder("选科组合，可选").fill(config.subjectCombination);
  await workbenchPanel.getByPlaceholder("位次覆盖").fill(config.studentRankOverride);
}

async function openRecommendationCenter(
  page: Page,
  options: { ensureDefaultOriginProvince?: boolean } = {},
): Promise<Locator> {
  const { ensureDefaultOriginProvince = true } = options;
  await ensureExamWithScores(page);
  if (ensureDefaultOriginProvince) {
    await ensureStudentOriginProvince(page);
  }
  await page.goto("/recommendations");
  await expect(page.getByRole("heading", { name: "高考志愿" })).toBeVisible();

  await page.getByRole("tab", { name: "录取库" }).click();
  await ensureAdmissionsImported(page);
  await page.getByRole("tab", { name: "推荐中心" }).click();

  return page.locator(".panel-block").filter({ hasText: "生成推荐方案" }).first();
}

async function fillRecommendationContext(page: Page, generatePanel: Locator, studentText = "2026001 - 张三"): Promise<void> {
  const generateSelects = generatePanel.locator(".filter-grid .el-select");
  await selectDropdownOption(page, generateSelects.nth(0), studentText);
  await selectDropdownOption(page, generateSelects.nth(1), e2eExamName);
  await generatePanel.getByPlaceholder("位次覆盖").fill("31000");
}

async function generateRecommendationScheme(
  page: Page,
  generatePanel: Locator,
  options: { name: string; majorKeyword?: string; studentText?: string },
): Promise<void> {
  await fillRecommendationContext(page, generatePanel, options.studentText);
  await generatePanel.getByPlaceholder("方案名称，可选").fill(options.name);
  await generatePanel.getByPlaceholder("专业方向关键词，可选").fill(options.majorKeyword ?? "");
  await generatePanel.getByRole("button", { name: "生成推荐" }).click();
  await confirmDialogIfVisible(page, "生成前复核", "继续生成");
}

async function openVolunteerWorkbench(page: Page): Promise<Locator> {
  await ensureExamWithScores(page);
  await page.goto("/recommendations");
  await expect(page.getByRole("heading", { name: "高考志愿" })).toBeVisible();

  await page.getByRole("tab", { name: "录取库" }).click();
  await ensureAdmissionsImported(page);

  await page.getByRole("tab", { name: "招生计划库" }).click();
  await ensureEnrollmentPlansImported(page);

  await ensureVolunteerRuleConfigured(page);

  await page.getByRole("tab", { name: "学生志愿工作台" }).click();
  const workbenchPanel = page.locator(".panel-block").filter({ hasText: "学生志愿工作台" }).first();
  await expect(workbenchPanel.getByRole("heading", { name: "学生志愿工作台" })).toBeVisible();
  return workbenchPanel;
}

async function createVolunteerDraft(page: Page): Promise<{
  workbenchPanel: Locator;
  candidatePanel: Locator;
  draftPanel: Locator;
  draftName: string;
}> {
  const workbenchPanel = await openVolunteerWorkbench(page);
  const candidatePanel = workbenchPanel.locator(".nested-panel").first();
  const draftPanel = workbenchPanel.locator(".nested-panel").nth(1);
  const draftName = `E2E-志愿草稿-张三-${Date.now()}`;

  await fillVolunteerWorkbenchContext(page, workbenchPanel);
  await workbenchPanel.getByRole("button", { name: "刷新候选池" }).click();
  await expectToast(page, "候选池已刷新");
  await expect(workbenchPanel.getByText("张三 · 普通生 · 2026届高一4月月考")).toBeVisible();
  await expect(candidatePanel.locator(".el-table__row").filter({ hasText: "岭南科技大学" }).first()).toBeVisible();

  await candidatePanel.locator(".el-table__row").filter({ hasText: "软件工程" }).first().getByRole("button", { name: "加入" }).click();
  await expectToast(page, "已加入志愿表");
  await candidatePanel.locator(".el-table__row").filter({ hasText: "人工智能" }).first().getByRole("button", { name: "加入" }).click();
  await expectToast(page, "已加入志愿表");

  await expect(draftPanel.locator(".el-table__row").filter({ hasText: "软件工程" }).first()).toBeVisible();
  await expect(draftPanel.locator(".el-table__row").filter({ hasText: "人工智能" }).first()).toBeVisible();

  await workbenchPanel.getByPlaceholder("草稿名称，例如：张三-本科批第一版").fill(draftName);
  await workbenchPanel.getByRole("button", { name: "保存草稿" }).click();
  await expectToast(page, "志愿草稿已保存");
  await expect(workbenchPanel.getByText("当前已保存草稿，可直接打印或导出。")).toBeVisible();
  await expect(draftPanel.locator(".saved-draft-card").filter({ hasText: draftName }).first()).toBeVisible();

  return { workbenchPanel, candidatePanel, draftPanel, draftName };
}

async function ensureMajorEmploymentProfile(
  page: Page,
  majorName: string,
  profile: { direction: string; careerPath: string; note: string },
): Promise<void> {
  const majorResponse = await page.request.get(`/api/majors?keyword=${encodeURIComponent(majorName)}`);
  expect(majorResponse.ok()).toBeTruthy();
  const majorsPayload = (await majorResponse.json()) as Array<{
    id: number;
    name: string;
    major_code?: string | null;
    category?: string | null;
    is_art_related: boolean;
    is_active: boolean;
  }>;
  const targetMajor = majorsPayload.find((item) => item.name === majorName);
  if (!targetMajor) {
    const createResponse = await page.request.post("/api/majors", {
      data: {
        name: majorName,
        major_code: null,
        category: null,
        direction: profile.direction,
        career_path: profile.careerPath,
        is_art_related: false,
        note: profile.note,
        is_active: true,
      },
    });
    expect(createResponse.ok()).toBeTruthy();
    return;
  }

  const updateResponse = await page.request.put(`/api/majors/${targetMajor?.id}`, {
    data: {
      name: targetMajor?.name,
      major_code: targetMajor?.major_code ?? null,
      category: targetMajor?.category ?? null,
      direction: profile.direction,
      career_path: profile.careerPath,
      is_art_related: targetMajor?.is_art_related ?? false,
      note: profile.note,
      is_active: targetMajor?.is_active ?? true,
    },
  });
  expect(updateResponse.ok()).toBeTruthy();
}

test("工作台冒烟：可加载概况并进入学生中心", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "先确认最近状态，再进入具体模块" })).toBeVisible();
  await expect(page.locator(".page-chip-row").first()).toContainText("3");
  await expect(page.getByRole("heading", { name: "最近考试" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "最近导入" })).toBeVisible();

  await page.getByRole("button", { name: "学生中心", exact: true }).click();

  await expect(page).toHaveURL(/\/students$/);
  await expect(page.getByRole("heading", { name: "学生中心" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "学生列表" })).toBeVisible();
});

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

test("系统设置主流程：创建备份后备份数量增加", async ({ page }) => {
  await page.goto("/system-tools");

  await expect(page.getByRole("heading", { name: "系统设置" })).toBeVisible();

  const backupCountLocator = page.locator(".metric-grid .stat-card").filter({ hasText: "备份数量" }).locator("strong");
  const initialBackupCount = Number((await backupCountLocator.textContent()) ?? "0");

  await page.getByRole("button", { name: "立即备份" }).click();
  await expect(page.getByText("备份完成")).toBeVisible();
  await expect(backupCountLocator).toHaveText(String(initialBackupCount + 1));

  await page.getByRole("tab", { name: "备份恢复" }).click();
  await expect(page.getByRole("heading", { name: "备份记录" })).toBeVisible();
  await expect(page.getByText("local_edu_backup", { exact: false }).first()).toBeVisible();
});

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
  await expectToast(page, "推荐报告导出失败：推荐报告导出模拟失败");
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

test("Stage B 主链路：生源地回退的模拟推荐可同步到工作台并保存草稿", async ({ page }) => {
  await ensureStudentOriginProvince(page);

  const generatePanel = await openRecommendationCenter(page);
  const generateSelects = generatePanel.locator(".filter-grid .el-select");
  const schemeName = `E2E-StageB-模拟链路-${Date.now()}`;
  const draftName = `E2E-StageB-草稿-${Date.now()}`;

  await selectDropdownOption(page, generateSelects.nth(0), "2026001 - 张三");
  await expect(generateSelects.nth(3)).toContainText("广东");
  await selectDropdownOption(page, generateSelects.nth(1), e2eExamName);
  await selectDropdownOption(page, generateSelects.nth(4), "预估分 + 预估位次");
  await generatePanel.getByPlaceholder("方案名称，可选").fill(schemeName);
  await generatePanel.getByPlaceholder("预估位次").fill("31000");
  await generatePanel.getByPlaceholder("预估分数").fill("582");
  await generatePanel.getByPlaceholder("参考考试，如一模/二模").fill("2026届一模");
  await generatePanel.getByRole("button", { name: "生成推荐" }).click();
  await confirmDialogIfVisible(page, "生成前复核", "继续生成");

  await expectToast(page, "推荐方案生成成功");
  const resultPanel = page.locator(".panel-block").filter({ hasText: "方案结果" });
  await expect(resultPanel.getByText(schemeName)).toBeVisible();

  const historyPanel = page.locator(".panel-block").filter({ hasText: "推荐历史" });
  await historyPanel.getByRole("button", { name: "查询历史" }).click();
  const historyRow = historyPanel.locator(".el-table__row").filter({ hasText: schemeName }).first();
  await expect(historyRow).toContainText("广东");
  await expect(historyRow).toContainText("2026");
  await expect(historyRow).toContainText("预估分数 + 预估位次");
  await expect(historyRow).toContainText("参考 2026届一模");

  await page.getByRole("tab", { name: "招生计划库" }).click();
  await ensureEnrollmentPlansImported(page);
  await ensureVolunteerRuleConfigured(page);
  await page.getByRole("tab", { name: "学生志愿工作台" }).click();
  const workbenchPanel = page.locator(".panel-block").filter({ hasText: "学生志愿工作台" }).first();
  await expect(workbenchPanel.getByRole("heading", { name: "学生志愿工作台" })).toBeVisible();
  await workbenchPanel.getByRole("button", { name: "沿用推荐条件" }).click();

  const workbenchSelects = workbenchPanel.locator(".filter-grid .el-select");
  await expect(workbenchSelects.nth(0)).toContainText("2026001 - 张三");
  await expect(workbenchSelects.nth(1)).toContainText(e2eExamName);
  await expect(workbenchSelects.nth(2)).toContainText("广东");
  await expect(workbenchSelects.nth(3)).toContainText("2026");
  await selectDropdownOption(page, workbenchSelects.nth(4), "本科批");
  await selectDropdownOption(page, workbenchSelects.nth(5), "物理类");
  await expect(workbenchSelects.nth(7)).toContainText("预估分 + 预估位次");
  await expect(workbenchPanel.getByPlaceholder("参考考试说明，可选")).toHaveValue("2026届一模");
  await expect(workbenchPanel.getByPlaceholder("预估位次")).toHaveValue("31000");
  await expect(workbenchPanel.getByPlaceholder("预估分数")).toHaveValue("582");

  await workbenchPanel.getByRole("button", { name: "刷新候选池" }).click();
  await expectToast(page, "候选池已刷新");
  await expect(workbenchPanel.getByText("当前分数输入模式为“预估分 + 预估位次”。")).toBeVisible();
  await expect(workbenchPanel.getByText("先按 广东 / 2026 / 本科批 / 物理类 限定招生计划范围。")).toBeVisible();

  const candidatePanel = workbenchPanel.locator(".nested-panel").first();
  const draftPanel = workbenchPanel.locator(".nested-panel").nth(1);
  await candidatePanel.locator(".el-table__row").filter({ hasText: "软件工程" }).first().getByRole("button", { name: "加入" }).click();
  await expectToast(page, "已加入志愿表");
  await expect(draftPanel.locator(".el-table__row").filter({ hasText: "软件工程" }).first()).toBeVisible();

  await workbenchPanel.getByPlaceholder("草稿名称，例如：张三-本科批第一版").fill(draftName);
  await workbenchPanel.getByRole("button", { name: "保存草稿" }).click();
  await expectToast(page, "志愿草稿已保存");
  await expect(draftPanel.locator(".saved-draft-card").filter({ hasText: draftName }).first()).toBeVisible();
});

test("Stage B 批量场景：混合生源地学生可分别生成方案并写入历史", async ({ page }) => {
  await ensureStudentOriginProvince(page, 1, "山东");
  await ensureStudentOriginProvince(page, 2, "河北");

  const generatePanel = await openRecommendationCenter(page, { ensureDefaultOriginProvince: false });
  await page.getByRole("tab", { name: "录取库" }).click();
  await ensureCrossProvinceAdmissionsImported(page);
  await page.getByRole("tab", { name: "推荐中心" }).click();

  await generatePanel.locator(".el-radio-button").filter({ hasText: "批量学生" }).first().click();
  const generateSelects = generatePanel.locator(".filter-grid .el-select");
  const batchSchemeName = `E2E-StageB-批量跨省-${Date.now()}`;

  await selectDropdownOption(page, generateSelects.nth(0), "2026001 - 张三");
  await selectDropdownOption(page, generateSelects.nth(0), "2026002 - 李四");
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

  const historyPanel = page.locator(".panel-block").filter({ hasText: "推荐历史" });
  const historyStudentSelect = historyPanel.locator(".filter-grid .el-select").first();

  await selectDropdownOption(page, historyStudentSelect, "2026001 - 张三");
  await historyPanel.getByRole("button", { name: "查询历史" }).click();
  await expect(historyPanel.locator(".el-table__row").filter({ hasText: batchSchemeName }).first()).toContainText("山东");

  await selectDropdownOption(page, historyStudentSelect, "2026002 - 李四");
  await historyPanel.getByRole("button", { name: "查询历史" }).click();
  await expect(historyPanel.locator(".el-table__row").filter({ hasText: batchSchemeName }).first()).toContainText("河北");
});

test("高考志愿主流程：可刷新候选池、保存草稿并打印导出志愿表", async ({ page }) => {
  const { workbenchPanel, draftPanel, draftName } = await createVolunteerDraft(page);
  await expect(workbenchPanel.getByRole("heading", { name: "筛选解释" })).toBeVisible();
  await expect(workbenchPanel.getByRole("heading", { name: "风险校验" })).toBeVisible();
  await expect(workbenchPanel.getByText("当前草稿已纳入 2 条志愿")).toBeVisible();
  await expect(workbenchPanel.getByText("院校代码").first()).toBeVisible();
  await expect(workbenchPanel.getByText("专业代码").first()).toBeVisible();
  const softwareDragHandle = draftPanel.locator(".el-table__row").filter({ hasText: "软件工程" }).first().locator(".drag-handle");
  const aiDragHandle = draftPanel.locator(".el-table__row").filter({ hasText: "人工智能" }).first().locator(".drag-handle");
  await aiDragHandle.dragTo(softwareDragHandle);
  await expect(draftPanel.locator(".el-table__row").first()).toContainText("人工智能");
  await workbenchPanel.getByRole("button", { name: "保存草稿" }).click();
  await expectToast(page, "志愿草稿已保存");
  await draftPanel.locator(".el-radio-group").getByText("冲稳保视图").click();
  await expect(draftPanel.getByText("冲稳保视图只改变查看方式，不改变全表顺序")).toBeVisible();
  await expect(draftPanel.getByRole("heading", { name: "冲刺志愿" })).toBeVisible();
  await expect(draftPanel.getByRole("heading", { name: "稳妥志愿" })).toBeVisible();
  await expect(draftPanel.getByRole("heading", { name: "保底志愿" })).toBeVisible();

  const printPreviewPopupPromise = page.waitForEvent("popup", { timeout: 5000 }).catch(() => null);
  await workbenchPanel.getByRole("button", { name: "打印预览" }).click();
  await confirmDialogIfVisible(page, "打印前复核", "仍要打印");
  const printPreviewPopup = await printPreviewPopupPromise;
  if (printPreviewPopup) {
    await expect(printPreviewPopup.getByText("志愿草稿打印预览")).toBeVisible();
    await printPreviewPopup.close();
  }

  const exportPopupPromise = page.waitForEvent("popup", { timeout: 5000 }).catch(() => null);
  await workbenchPanel.getByRole("button", { name: "导出 Excel" }).click();
  await confirmDialogIfVisible(page, "导出前复核", "仍要导出");
  const exportPopup = await exportPopupPromise;
  if (exportPopup) {
    await exportPopup.close();
  }
  await expectToast(page, "志愿草稿已导出");

  await draftPanel.locator(".saved-draft-card").filter({ hasText: draftName }).first().getByRole("button", { name: "加载" }).click();
  await expectToast(page, "已加载志愿草稿");
  await expect(draftPanel.locator(".el-table__row").first()).toContainText("人工智能");
});

test("高考志愿草稿版本：可另存为新草稿并对比历史版本", async ({ page }) => {
  const { workbenchPanel, draftPanel, draftName } = await createVolunteerDraft(page);
  const versionedDraftName = `${draftName}-第二版`;

  await draftPanel.locator(".el-table__row").filter({ hasText: "人工智能" }).first().getByRole("button", { name: "上移" }).click();
  await expect(draftPanel.locator(".el-table__row").first()).toContainText("人工智能");

  await workbenchPanel.getByPlaceholder("草稿名称，例如：张三-本科批第一版").fill(versionedDraftName);
  await workbenchPanel.getByRole("button", { name: "另存为新草稿" }).click();
  await expectToast(page, "已另存为新草稿");
  await expect(draftPanel.locator(".saved-draft-card").filter({ hasText: draftName }).first()).toBeVisible();
  await expect(draftPanel.locator(".saved-draft-card").filter({ hasText: versionedDraftName }).first()).toBeVisible();

  const comparisonPanel = workbenchPanel.locator(".draft-comparison-panel");
  await selectDropdownOption(page, comparisonPanel.locator(".el-select").first(), draftName);
  await expect(comparisonPanel.locator(".comparison-summary-card").filter({ hasText: "顺序变化" })).toContainText("2");
  await expect(comparisonPanel.locator(".comparison-summary-card").filter({ hasText: "共同志愿" })).toContainText("2");
  await expect(comparisonPanel.locator(".comparison-column").filter({ hasText: "顺序变化" })).toContainText("软件工程");
  await expect(comparisonPanel.locator(".comparison-column").filter({ hasText: "顺序变化" })).toContainText("人工智能");
  await expect(comparisonPanel.locator(".comparison-column").filter({ hasText: "顺序变化" })).toContainText("当前第 1 位，对比稿第 2 位");
  await expect(comparisonPanel.locator(".comparison-column").filter({ hasText: "顺序变化" })).toContainText("当前第 2 位，对比稿第 1 位");
});

test("高考志愿就业增强列：默认展示画像列并提供扩展列入口", async ({ page }) => {
  await ensureMajorEmploymentProfile(page, "软件工程", {
    direction: "企业软件与平台开发",
    careerPath: "企业应用开发、系统实施，部分岗位需要读研或资格证",
    note: "建议关注软件架构与项目管理路径",
  });
  await ensureMajorEmploymentProfile(page, "人工智能", {
    direction: "智能系统与算法应用",
    careerPath: "算法工程、模型训练，可先就业也可继续深造",
    note: "可延展到机器人与计算机视觉岗位",
  });

  const { draftPanel } = await createVolunteerDraft(page);
  const columnControls = draftPanel.locator(".draft-column-controls");
  await expect(columnControls).toContainText("就业增强列");
  await expect(columnControls).toContainText("需读研");
  await expect(columnControls).toContainText("需资格证");
  await expect(columnControls).toContainText("说明摘要");

  await expect(draftPanel.locator(".el-table__header")).toContainText("对应就业方向");
  await expect(draftPanel.locator(".el-table__header")).toContainText("匹配强度");

  const softwareRow = draftPanel.locator(".el-table__row").filter({ hasText: "软件工程" }).first();
  await expect(softwareRow).toContainText("企业软件与平台开发");
  await expect(softwareRow).toContainText("核心相关");

  const aiRow = draftPanel.locator(".el-table__row").filter({ hasText: "人工智能" }).first();
  await expect(aiRow).toContainText("智能系统与算法应用");
  await expect(aiRow).toContainText("核心相关");
});

test("高考志愿数据底座：可维护就业方向库和专业就业映射", async ({ page }) => {
  const directionName = `E2E-就业方向-${Date.now()}`;
  const workbenchPanel = await openVolunteerWorkbench(page);
  await expect(workbenchPanel.getByRole("heading", { name: "学生志愿工作台" })).toBeVisible();

  await page.getByRole("tab", { name: "就业方向库" }).click();
  const directionPanel = page.locator(".panel-block").filter({ hasText: "就业方向库" }).first();
  await expect(directionPanel.getByRole("heading", { name: "就业方向库" })).toBeVisible();

  await directionPanel.getByRole("button", { name: "新增方向" }).click();
  const directionDialog = page.locator('[role="dialog"]').filter({ hasText: "新增就业方向" });
  await expect(directionDialog).toBeVisible();
  await directionDialog.locator(".el-form-item").filter({ hasText: "方向名称" }).locator("input").fill(directionName);
  await selectDropdownOption(
    page,
    directionDialog.locator(".el-form-item").filter({ hasText: "方向分类" }).locator(".el-select"),
    "技术研发类",
  );
  await directionDialog.locator(".el-form-item").filter({ hasText: "风险提示" }).locator("textarea").fill("测试用就业方向说明");
  await directionDialog.getByRole("button", { name: "保存" }).click();
  await expectToast(page, "就业方向保存成功");
  await expect(directionPanel.locator(".el-table__row").filter({ hasText: directionName }).first()).toBeVisible();
  await expect(directionPanel.getByRole("heading", { name: "分类视图" })).toBeVisible();
  await expect(
    directionPanel.locator(".direction-group-card").filter({ hasText: "技术研发类" }).first(),
  ).toContainText(directionName);

  await page.getByRole("tab", { name: "专业就业映射" }).click();
  const mappingPanel = page.locator(".panel-block").filter({ hasText: "专业就业映射" }).first();
  await expect(mappingPanel.getByRole("heading", { name: "专业就业映射" })).toBeVisible();

  await mappingPanel.getByRole("button", { name: "新增映射" }).click();
  const mappingDialog = page.locator('[role="dialog"]').filter({ hasText: "新增专业就业映射" });
  await expect(mappingDialog).toBeVisible();
  await selectDropdownOption(
    page,
    mappingDialog.locator(".el-form-item").filter({ hasText: "专业" }).locator(".el-select"),
    "软件工程",
  );
  await selectDropdownOption(
    page,
    mappingDialog.locator(".el-form-item").filter({ hasText: "就业方向" }).locator(".el-select"),
    directionName,
  );
  await selectDropdownOption(
    page,
    mappingDialog.locator(".el-form-item").filter({ hasText: "映射强度" }).locator(".el-select"),
    "强相关",
  );
  await mappingDialog.locator(".el-form-item").filter({ hasText: "推荐说明" }).locator("textarea").fill("软件工程可作为该方向的优先专业入口");
  await mappingDialog.getByRole("button", { name: "保存" }).click();
  await expectToast(page, "专业就业映射保存成功");

  const targetRow = mappingPanel
    .locator(".el-table__row")
    .filter({ hasText: "软件工程" })
    .filter({ hasText: directionName })
    .first();
  await expect(targetRow).toBeVisible();
  await expect(targetRow).toContainText("强相关");
});

test("报表中心：可按志愿草稿打印预览并导出报表", async ({ page }) => {
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
  const schemeName = `E2E-报表摘要-推荐-${Date.now()}`;
  const { draftName } = await createVolunteerDraft(page);
  const examsResponse = await page.request.get("/api/exams?page=1&page_size=100");
  expect(examsResponse.ok()).toBeTruthy();
  const examsPayload = (await examsResponse.json()) as { items: Array<{ id: number; name: string }> };
  const currentExam = examsPayload.items.find((item) => item.name === e2eExamName);
  expect(currentExam).toBeTruthy();

  const generateResponse = await page.request.post("/api/recommendations/generate", {
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

test("高考志愿复杂筛选：关键词可缩小候选池，历史类规则下显示空状态", async ({ page }) => {
  const workbenchPanel = await openVolunteerWorkbench(page);
  const candidatePanel = workbenchPanel.locator(".nested-panel").first();
  const draftPanel = workbenchPanel.locator(".nested-panel").nth(1);

  await ensureVolunteerRuleConfigured(page, {
    examMode: "历史类",
    volunteerLimit: 30,
    volunteerUnitType: "专业",
    note: "E2E-历史类规则",
  });

  await page.getByRole("tab", { name: "学生志愿工作台" }).click();
  await expect(workbenchPanel.getByRole("heading", { name: "学生志愿工作台" })).toBeVisible();

  await fillVolunteerWorkbenchContext(page, workbenchPanel, { majorKeyword: "人工智能" });
  await workbenchPanel.getByRole("button", { name: "刷新候选池" }).click();
  await expectToast(page, "候选池已刷新");
  await expect(workbenchPanel.locator(".el-alert").filter({ hasText: "已匹配 1 条候选计划" }).first()).toBeVisible();
  await expect(candidatePanel.locator(".el-table__row").filter({ hasText: "人工智能" }).first()).toBeVisible();
  await expect(candidatePanel.locator(".el-table__row").filter({ hasText: "软件工程" })).toHaveCount(0);

  await fillVolunteerWorkbenchContext(page, workbenchPanel, {
    examMode: "历史类",
    majorKeyword: "",
    subjectCombination: "历史",
  });
  await workbenchPanel.getByRole("button", { name: "刷新候选池" }).click();
  await expectToast(page, "当前条件下暂无可加入候选池的招生计划");
  await expect(candidatePanel.getByText("当前条件下暂无可加入志愿表的候选计划。")).toBeVisible();
  await expect(workbenchPanel.getByText("已匹配 0 条候选计划")).toBeVisible();
  await expect(workbenchPanel.getByText("1 条省份规则")).toBeVisible();
  await expect(draftPanel.locator(".el-alert")).toContainText("广东 2026 历史类 · 本科批");
});

test("高考志愿预估模式：分数区间可刷新候选池并显示模拟说明", async ({ page }) => {
  const workbenchPanel = await openVolunteerWorkbench(page);
  const candidatePanel = workbenchPanel.locator(".nested-panel").first();

  await fillVolunteerWorkbenchContext(page, workbenchPanel);
  const filterSelects = workbenchPanel.locator(".filter-grid .el-select");
  await selectDropdownOption(page, filterSelects.nth(7), "分数区间");
  await workbenchPanel.getByPlaceholder("分数区间下限").fill("568");
  await workbenchPanel.getByPlaceholder("分数区间上限").fill("576");
  await workbenchPanel.getByPlaceholder("参考考试说明，可选").fill("2026届一模");
  await workbenchPanel.locator(".inline-switch-card .el-switch").click();

  await workbenchPanel.getByRole("button", { name: "刷新候选池" }).click();
  await expectToast(page, "候选池已刷新");
  await expect(workbenchPanel.locator(".el-alert").filter({ hasText: "当前按“分数区间”计算" }).first()).toBeVisible();
  await expect(workbenchPanel.locator(".el-alert").filter({ hasText: "2026届一模" }).first()).toBeVisible();
  await expect(candidatePanel.locator(".el-table__row").first()).toBeVisible();
});

test("高考志愿年份边界：缺少目标年份规则时提示人工复核", async ({ page }) => {
  const workbenchPanel = await openVolunteerWorkbench(page);

  await fillVolunteerWorkbenchContext(page, workbenchPanel);
  const filterSelects = workbenchPanel.locator(".filter-grid .el-select");
  await selectDropdownOption(page, filterSelects.nth(3), "2025");

  await workbenchPanel.getByRole("button", { name: "刷新候选池" }).click();
  await expectToast(page, "当前条件下暂无可加入候选池的招生计划");
  await expect(workbenchPanel.getByText("已匹配 0 条候选计划")).toBeVisible();
  await expect(workbenchPanel.getByText("0 条省份规则")).toBeVisible();
  await expect(
    workbenchPanel.locator(".el-alert").filter({ hasText: "当前未找到 广东 2025 年省份规则；该省现有 2026 年规则" }).first(),
  ).toBeVisible();
});

test("高考志愿模式兼容：3+1+2 可回退命中物理类规则与招生计划", async ({ page }) => {
  const workbenchPanel = await openVolunteerWorkbench(page);
  const candidatePanel = workbenchPanel.locator(".nested-panel").first();

  await fillVolunteerWorkbenchContext(page, workbenchPanel, {
    examMode: "3+1+2",
    subjectCombination: "物理+化学",
  });

  await workbenchPanel.getByRole("button", { name: "刷新候选池" }).click();
  await expectToast(page, "候选池已刷新");
  await expect(workbenchPanel.getByText("已匹配 2 条候选计划")).toBeVisible();
  await expect(
    workbenchPanel.locator(".el-alert").filter({ hasText: "当前未配置“3+1+2”精确规则，先按兼容模式" }).first(),
  ).toBeVisible();
  await expect(candidatePanel.locator(".el-table__row").filter({ hasText: "软件工程" }).first()).toBeVisible();
});

test("高考志愿规则校验：志愿上限和草稿名称校验生效", async ({ page }) => {
  const workbenchPanel = await openVolunteerWorkbench(page);
  const candidatePanel = workbenchPanel.locator(".nested-panel").first();
  const draftPanel = workbenchPanel.locator(".nested-panel").nth(1);

  await ensureVolunteerRuleConfigured(page, {
    examMode: "物理类",
    volunteerLimit: 1,
    volunteerUnitType: "专业",
    note: "E2E-单志愿限制",
  });

  try {
    await page.getByRole("tab", { name: "学生志愿工作台" }).click();
    await expect(workbenchPanel.getByRole("heading", { name: "学生志愿工作台" })).toBeVisible();

    await fillVolunteerWorkbenchContext(page, workbenchPanel);
    await workbenchPanel.getByRole("button", { name: "刷新候选池" }).click();
    await expectToast(page, "候选池已刷新");

    await candidatePanel.locator(".el-table__row").filter({ hasText: "软件工程" }).first().getByRole("button", { name: "加入" }).click();
    await expectToast(page, "已加入志愿表");
    await expect(draftPanel.locator(".page-chip").filter({ hasText: "上限" }).first()).toContainText("1");
    await expect(draftPanel.locator(".page-chip").filter({ hasText: "剩余" }).first()).toContainText("0");

    await candidatePanel.locator(".el-table__row").filter({ hasText: "人工智能" }).first().getByRole("button", { name: "加入" }).click();
    await expectToast(page, "当前批次志愿上限为 1");

    await workbenchPanel.getByRole("button", { name: "保存草稿" }).click();
    await expectToast(page, "草稿名称不能为空");
  } finally {
    await ensureVolunteerRuleConfigured(page);
  }
});

test("考试异常提示：错误成绩模板会给出明确失败原因", async ({ page }) => {
  await ensureExamWithScores(page);

  const importDialog = page.locator('[role="dialog"]').filter({ hasText: "导入成绩" });
  await expect(importDialog).toBeVisible();
  await importDialog.locator('input[type="file"]').setInputFiles(invalidScoresFixture);

  await expectToast(page, "成绩导入模板表头不匹配");
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

test("推荐异常提示：缺少学生与考试时阻止生成", async ({ page }) => {
  await page.goto("/recommendations");
  await expect(page.getByRole("heading", { name: "高考志愿" })).toBeVisible();

  const generatePanel = page.locator(".panel-block").filter({ hasText: "生成推荐方案" }).first();
  await generatePanel.getByRole("button", { name: "生成推荐" }).click();

  await expectToast(page, "单个学生推荐需要学生和考试");
});
