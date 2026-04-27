import path from "node:path";
import fs from "node:fs";

import { expect } from "@playwright/test";
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

interface ProvinceVolunteerRulePayload {
  province: string;
  year: number;
  exam_mode: string;
  batch: string;
  candidate_type: string;
  batch_order?: number;
  total_score: number;
  volunteer_limit: number;
  volunteer_unit_type: string;
  subject_requirement_mode?: string | null;
  required_subjects_json: string[];
  first_choice_subjects_json: string[];
  reselect_subjects_json: string[];
  score_rule_summary?: string | null;
  parallel_rule_mode?: string | null;
  max_major_per_unit?: number;
  is_parallel: boolean;
  allow_adjustment: boolean;
  support_collect_round: boolean;
  special_rules_json: string[];
  note: string | null;
  is_active: boolean;
}

interface ProvinceVolunteerRuleRead extends ProvinceVolunteerRulePayload {
  id: number;
}

interface VolunteerWorkbenchContextOptions {
  studentText?: string;
  examText?: string;
  province?: string;
  targetYear?: string;
  batch?: string;
  examMode?: string;
  majorKeyword?: string;
  subjectCombination?: string;
  studentRankOverride?: string;
}

async function expectToast(page: Page, text: string): Promise<void> {
  await expect(page.locator(".el-message__content").filter({ hasText: text }).last()).toBeVisible();
}

async function importFixtureByApi(page: Page, url: string, fixturePath: string): Promise<void> {
  const response = await page.request.post(url, {
    multipart: {
      file: {
        name: path.basename(fixturePath),
        mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        buffer: fs.readFileSync(fixturePath),
      },
    },
  });
  expect(response.ok()).toBeTruthy();
}

async function selectDropdownOption(page: Page, select: Locator, optionText: string): Promise<void> {
  await select.click();
  const option = page.locator(".el-select-dropdown:visible .el-select-dropdown__item").filter({ hasText: optionText }).first();
  if (!(await option.isVisible({ timeout: 1000 }).catch(() => false))) {
    const filterInput = select.locator("input").first();
    const canFill =
      (await filterInput.count()) > 0
      && (await filterInput
        .evaluate((element) => {
          const input = element as HTMLInputElement;
          return !input.readOnly && !input.disabled;
        })
        .catch(() => false));
    if (canFill) {
      await filterInput.fill(optionText, { timeout: 1000 }).catch(async () => {
        await page.keyboard.type(optionText);
      });
    } else {
      const matchingOption = page.locator(".el-select-dropdown__item").filter({ hasText: optionText }).last();
      if ((await matchingOption.count()) > 0) {
        await matchingOption.evaluate((element) => element.scrollIntoView({ block: "center" })).catch(() => undefined);
      } else {
        await page.keyboard.type(optionText);
      }
    }
  }
  await expect(option).toBeVisible();
  await option.click();
}

interface RecommendationFormE2EFields {
  province?: string;
  student_ids?: number[];
}

async function setRecommendationFormForE2E(generatePanel: Locator, fields: RecommendationFormE2EFields): Promise<void> {
  await generatePanel.evaluate((element, nextFields) => {
    let instance = (element as HTMLElement & {
      __vueParentComponent?: {
        parent?: unknown;
        props?: { form?: RecommendationFormE2EFields };
        setupState?: { form?: RecommendationFormE2EFields };
      };
    }).__vueParentComponent;

    while (instance) {
      const form = instance.props?.form ?? instance.setupState?.form;
      if (form && ("province" in form || "student_ids" in form)) {
        Object.assign(form, nextFields);
        return;
      }
      instance = instance.parent as typeof instance;
    }

    throw new Error("Recommendation form instance not found");
  }, fields);
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
  let response = await page.request.get("/api/admissions?province=广东");
  expect(response.ok()).toBeTruthy();
  let payload = (await response.json()) as Array<{ college_name?: string }>;
  if (!payload.some((item) => item.college_name === "岭南科技大学")) {
    await importFixtureByApi(page, "/api/admissions/import", admissionsFixture);
    response = await page.request.get("/api/admissions?province=广东");
    expect(response.ok()).toBeTruthy();
    payload = (await response.json()) as Array<{ college_name?: string }>;
  }
  expect(payload.some((item) => item.college_name === "岭南科技大学")).toBeTruthy();
}

async function ensureCrossProvinceAdmissionsImported(page: Page): Promise<void> {
  let response = await page.request.get("/api/admissions?province=山东");
  expect(response.ok()).toBeTruthy();
  let payload = (await response.json()) as Array<{ college_name?: string }>;
  if (!payload.some((item) => item.college_name === "华北信息大学")) {
    await importFixtureByApi(page, "/api/admissions/import", crossProvinceAdmissionsFixture);
    response = await page.request.get("/api/admissions?province=山东");
    expect(response.ok()).toBeTruthy();
    payload = (await response.json()) as Array<{ college_name?: string }>;
  }
  expect(payload.some((item) => item.college_name === "华北信息大学")).toBeTruthy();
}

async function ensureEnrollmentPlansImported(page: Page): Promise<void> {
  let response = await page.request.get("/api/enrollment-plans?province=广东");
  expect(response.ok()).toBeTruthy();
  let payload = (await response.json()) as Array<{ college_name?: string }>;
  if (!payload.some((item) => item.college_name === "岭南科技大学")) {
    await importFixtureByApi(page, "/api/enrollment-plans/import", enrollmentPlansFixture);
    response = await page.request.get("/api/enrollment-plans?province=广东");
    expect(response.ok()).toBeTruthy();
    payload = (await response.json()) as Array<{ college_name?: string }>;
  }
  expect(payload.some((item) => item.college_name === "岭南科技大学")).toBeTruthy();
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

  const payload: ProvinceVolunteerRulePayload = {
    province: config.province,
    year: Number(config.year),
    exam_mode: config.examMode,
    batch: config.batch,
    candidate_type: "",
    batch_order: undefined,
    total_score: 750,
    volunteer_limit: config.volunteerLimit,
    volunteer_unit_type: config.volunteerUnitType,
    subject_requirement_mode: "unified_subject_requirement",
    required_subjects_json: ["物理", "化学", "生物", "政治", "历史", "地理"],
    first_choice_subjects_json: [],
    reselect_subjects_json: [],
    score_rule_summary: null,
    parallel_rule_mode: config.volunteerUnitType === "专业" ? "major_parallel" : "group_parallel",
    max_major_per_unit: undefined,
    is_parallel: true,
    allow_adjustment: true,
    support_collect_round: false,
    special_rules_json: [],
    note: config.note || null,
    is_active: true,
  };

  const query = new URLSearchParams({
    province: config.province,
    year: config.year,
    exam_mode: config.examMode,
  });
  const listResponse = await page.request.get(`/api/province-volunteer-rules?${query.toString()}`);
  expect(listResponse.ok()).toBeTruthy();
  const rules = (await listResponse.json()) as ProvinceVolunteerRuleRead[];
  const existing = rules.find((rule) => rule.batch === config.batch && rule.candidate_type === "");
  const response = existing
    ? await page.request.put(`/api/province-volunteer-rules/${existing.id}`, { data: payload })
    : await page.request.post("/api/province-volunteer-rules", { data: payload });
  expect(response.ok()).toBeTruthy();

  const saved = (await response.json()) as ProvinceVolunteerRuleRead;
  expect(saved.province).toBe(config.province);
  expect(saved.year).toBe(Number(config.year));
  expect(saved.exam_mode).toBe(config.examMode);
  expect(saved.batch).toBe(config.batch);
  expect(saved.volunteer_limit).toBe(config.volunteerLimit);
  expect(saved.volunteer_unit_type).toBe(config.volunteerUnitType);
}

async function fillVolunteerWorkbenchContext(
  page: Page,
  workbenchPanel: Locator,
  options: VolunteerWorkbenchContextOptions = {},
): Promise<void> {
  const config = {
    studentText: "2026001 - 张三",
    examText: e2eExamName,
    province: "广东",
    targetYear: gaokaoTargetYear,
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
  await selectDropdownOption(page, filterSelects.nth(2), config.province);
  await selectDropdownOption(page, filterSelects.nth(3), config.targetYear);
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
  await selectDropdownOption(page, generateSelects.nth(3), "广东");
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

  await ensureAdmissionsImported(page);

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

export {
  confirmDialogIfVisible,
  createVolunteerDraft,
  e2eExamName,
  ensureAdmissionsImported,
  ensureCrossProvinceAdmissionsImported,
  ensureEnrollmentPlansImported,
  ensureExamWithScores,
  ensureMajorEmploymentProfile,
  ensureStudentOriginProvince,
  ensureVolunteerRuleConfigured,
  expectToast,
  fillRecommendationContext,
  fillVolunteerWorkbenchContext,
  gaokaoTargetYear,
  generateRecommendationScheme,
  importFixtureByApi,
  invalidScoresFixture,
  openRecommendationCenter,
  openVolunteerWorkbench,
  scoresFixture,
  selectDropdownOption,
  setRecommendationFormForE2E,
};
