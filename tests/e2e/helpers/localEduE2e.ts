import path from "node:path";
import fs from "node:fs";

import { expect } from "@playwright/test";
import type { APIRequestContext, APIResponse, Locator, Page } from "@playwright/test";

const scoresFixture = path.resolve(process.cwd(), "tests/e2e/fixtures/scores-import.xlsx");
const invalidScoresFixture = path.resolve(process.cwd(), "tests/e2e/fixtures/scores-invalid.xlsx");
const scoreQuestionDetailsFixture = path.resolve(process.cwd(), "tests/e2e/fixtures/score-question-details-import.xlsx");
const scoreQuestionTrendFixtureOne = path.resolve(process.cwd(), "tests/e2e/fixtures/score-question-details-trend-1.xlsx");
const scoreQuestionTrendFixtureTwo = path.resolve(process.cwd(), "tests/e2e/fixtures/score-question-details-trend-2.xlsx");
const admissionsFixture = path.resolve(process.cwd(), "tests/e2e/fixtures/admissions-import.xlsx");
const crossProvinceAdmissionsFixture = path.resolve(process.cwd(), "tests/e2e/fixtures/admissions-cross-province.xlsx");
const enrollmentPlansFixture = path.resolve(process.cwd(), "tests/e2e/fixtures/enrollment-plans-import.xlsx");
const e2eExamName = "2026届高一4月月考";
const e2eKnowledgeTrendExamOneName = "E2E知识点趋势一";
const e2eKnowledgeTrendExamTwoName = "E2E知识点趋势二";
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
  scoreInputMode?: string;
  majorKeyword?: string;
  subjectCombination?: string;
  studentRankOverride?: string;
  fillRankOverride?: boolean;
}

type ApiRequestOptions = Parameters<APIRequestContext["post"]>[1];

async function getCsrfToken(page: Page): Promise<string> {
  const response = await page.request.get("/api/auth/me");
  expect(response.ok()).toBeTruthy();
  const payload = (await response.json()) as { csrf_token?: string };
  expect(payload.csrf_token).toBeTruthy();
  return payload.csrf_token as string;
}

async function withCsrf(page: Page, options: ApiRequestOptions = {}): Promise<ApiRequestOptions> {
  const headers = {
    ...((options.headers as Record<string, string> | undefined) ?? {}),
    "X-CSRF-Token": await getCsrfToken(page),
  };
  return { ...options, headers };
}

async function apiPost(page: Page, url: string, options: ApiRequestOptions = {}): Promise<APIResponse> {
  return page.request.post(url, await withCsrf(page, options));
}

async function apiPut(page: Page, url: string, options: ApiRequestOptions = {}): Promise<APIResponse> {
  return page.request.put(url, await withCsrf(page, options));
}

async function expectToast(page: Page, text: string): Promise<void> {
  await expect(page.locator(".el-message__content").filter({ hasText: text }).last()).toBeVisible();
}

async function importFixtureByApi(page: Page, url: string, fixturePath: string): Promise<void> {
  const response = await apiPost(page, url, {
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

async function getCurrentSemesterId(page: Page): Promise<number> {
  const semestersResponse = await page.request.get("/api/base/semesters");
  expect(semestersResponse.ok()).toBeTruthy();
  const semesters = (await semestersResponse.json()) as Array<{ id: number; is_current?: boolean }>;
  const semesterId = semesters.find((item) => item.is_current)?.id ?? semesters[0]?.id;
  expect(semesterId).toBeTruthy();
  return semesterId;
}

async function getCoreSubjectIds(page: Page): Promise<{ chineseId: number; mathId: number }> {
  const subjectsResponse = await page.request.get("/api/base/subjects");
  expect(subjectsResponse.ok()).toBeTruthy();
  const subjects = (await subjectsResponse.json()) as Array<{ id: number; name: string }>;
  const chinese = subjects.find((item) => item.name === "语文");
  const math = subjects.find((item) => item.name === "数学");
  expect(chinese?.id).toBeTruthy();
  expect(math?.id).toBeTruthy();
  return { chineseId: chinese!.id, mathId: math!.id };
}

async function importScoresByApi(page: Page, examId: number, fixturePath: string): Promise<void> {
  const response = await apiPost(page, `/api/exams/${examId}/scores/import`, {
    multipart: {
      strategy: "overwrite",
      rebuild: "true",
      file: {
        name: path.basename(fixturePath),
        mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        buffer: fs.readFileSync(fixturePath),
      },
    },
  });
  expect(response.ok()).toBeTruthy();
}

async function ensureExamWithSubjectsByApi(page: Page, examName: string, examDate: string): Promise<number> {
  const examListResponse = await page.request.get(`/api/exams?page=1&page_size=200&name=${encodeURIComponent(examName)}`);
  expect(examListResponse.ok()).toBeTruthy();
  const examListPayload = (await examListResponse.json()) as { items: Array<{ id: number; name: string; subject_count?: number }> };
  const existing = examListPayload.items.find((item) => item.name === examName && (item.subject_count ?? 0) > 0)
    ?? examListPayload.items.find((item) => item.name === examName);
  let examId = existing?.id;
  if (!examId) {
    const semesterId = await getCurrentSemesterId(page);
    const createResponse = await apiPost(page, "/api/exams", {
      data: {
        name: examName,
        exam_type: "阶段测试",
        exam_date: examDate,
        semester_id: semesterId,
        grade_scope_json: [1],
        is_trend_enabled: true,
        status: "published",
        note: "",
        is_active: true,
      },
    });
    expect(createResponse.ok()).toBeTruthy();
    const created = (await createResponse.json()) as { id: number };
    examId = created.id;
  }

  const { chineseId, mathId } = await getCoreSubjectIds(page);
  const subjectResponse = await apiPost(page, `/api/exams/${examId}/subjects`, {
    data: [
      {
        subject_id: chineseId,
        full_score: 150,
        is_in_total: true,
        excellent_line: 110,
        pass_line: 90,
        sort_order: 1,
        is_active: true,
      },
      {
        subject_id: mathId,
        full_score: 150,
        is_in_total: true,
        excellent_line: 110,
        pass_line: 90,
        sort_order: 2,
        is_active: true,
      },
    ],
  });
  expect(subjectResponse.ok()).toBeTruthy();
  return examId;
}

async function importQuestionDetailsByApi(page: Page, examId: number, fixturePath: string): Promise<void> {
  const response = await apiPost(page, `/api/exams/${examId}/score-questions/import`, {
    multipart: {
      strategy: "overwrite",
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
  for (let attempt = 0; attempt < 3; attempt += 1) {
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
    try {
      await option.click({ timeout: 1500 });
      return;
    } catch (error) {
      if (attempt === 2) throw error;
      await page.keyboard.press("Escape").catch(() => undefined);
      await page.waitForTimeout(100);
    }
  }
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
  const examId = await ensureExamWithSubjectsByApi(page, e2eExamName, "2026-04-10");
  await importScoresByApi(page, examId, scoresFixture);
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

  const updateResponse = await apiPut(page, `/api/students/${studentId}`, {
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
    ? await apiPut(page, `/api/province-volunteer-rules/${existing.id}`, { data: payload })
    : await apiPost(page, "/api/province-volunteer-rules", { data: payload });
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
    scoreInputMode: "正式位次",
    majorKeyword: "",
    subjectCombination: "物理+化学",
    studentRankOverride: "31000",
    fillRankOverride: true,
    ...options,
  };

  const filterSelects = workbenchPanel.locator(".filter-grid .el-select");
  await selectDropdownOption(page, filterSelects.nth(0), config.studentText);
  await selectDropdownOption(page, filterSelects.nth(1), config.examText);
  await selectDropdownOption(page, filterSelects.nth(2), config.province);
  await selectDropdownOption(page, filterSelects.nth(3), config.targetYear);
  await selectDropdownOption(page, filterSelects.nth(4), config.batch);
  await selectDropdownOption(page, filterSelects.nth(5), config.examMode);
  await expect(workbenchPanel.getByText("校内考试口径，仅作模拟参考").first()).toBeVisible();
  if (config.scoreInputMode) {
    await selectDropdownOption(page, filterSelects.nth(7), config.scoreInputMode);
  }
  await workbenchPanel.getByPlaceholder("专业方向关键词，可选").fill(config.majorKeyword);
  await workbenchPanel.getByPlaceholder("选科组合，可选").fill(config.subjectCombination);
  if (config.fillRankOverride) {
    await workbenchPanel.getByPlaceholder(/位次/).fill(config.studentRankOverride);
  }
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

  await ensureAdmissionsImported(page);
  await openAdvancedTool(page, "推荐中心");

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

async function openAdvancedTool(page: Page, name: string): Promise<void> {
  await page.getByTestId("recommendation-advanced-tools-button").click();
  const item = page.locator(".recommendation-advanced-menu .el-dropdown-menu__item").filter({ hasText: name }).first();
  await expect(item).toBeVisible();
  await item.click();
}

async function returnToVolunteerGuide(page: Page): Promise<Locator> {
  const button = page.getByRole("button", { name: "回到推荐向导" });
  if (await button.isVisible().catch(() => false)) {
    await button.click();
  }
  const workbenchPanel = page.locator(".panel-block").filter({ hasText: "志愿推荐向导" }).first();
  await expect(workbenchPanel.getByRole("heading", { name: "志愿推荐向导" })).toBeVisible();
  return workbenchPanel;
}

async function openVolunteerWorkbench(page: Page): Promise<Locator> {
  await ensureExamWithScores(page);
  await page.goto("/recommendations");
  await expect(page.getByRole("heading", { name: "高考志愿" })).toBeVisible();

  await ensureAdmissionsImported(page);

  await ensureEnrollmentPlansImported(page);

  await ensureVolunteerRuleConfigured(page);

  return returnToVolunteerGuide(page);
}

function getCandidateCard(candidatePanel: Locator, text: string): Locator {
  return candidatePanel.locator(".candidate-card").filter({ hasText: text }).first();
}

async function addCandidateCard(candidatePanel: Locator, text: string): Promise<void> {
  await getCandidateCard(candidatePanel, text).getByRole("button", { name: "加入" }).click();
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
  await workbenchPanel.getByRole("button", { name: "生成智能筛选" }).click();
  await expectToast(page, "智能筛选已生成");
  await expect(workbenchPanel.getByText("张三 · 普通生 · 2026届高一4月月考")).toBeVisible();
  await expect(getCandidateCard(candidatePanel, "岭南科技大学")).toBeVisible();
  await expect(candidatePanel.getByText("近三年招生/录取情况").first()).toBeVisible();

  await addCandidateCard(candidatePanel, "软件工程");
  await expectToast(page, "已加入志愿表");
  await addCandidateCard(candidatePanel, "人工智能");
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
    const createResponse = await apiPost(page, "/api/majors", {
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

  const updateResponse = await apiPut(page, `/api/majors/${targetMajor?.id}`, {
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
  apiPost,
  apiPut,
  confirmDialogIfVisible,
  createVolunteerDraft,
  e2eExamName,
  e2eKnowledgeTrendExamOneName,
  e2eKnowledgeTrendExamTwoName,
  ensureAdmissionsImported,
  ensureCrossProvinceAdmissionsImported,
  ensureEnrollmentPlansImported,
  ensureExamWithScores,
  ensureExamWithSubjectsByApi,
  ensureMajorEmploymentProfile,
  ensureStudentOriginProvince,
  ensureVolunteerRuleConfigured,
  expectToast,
  fillRecommendationContext,
  fillVolunteerWorkbenchContext,
  gaokaoTargetYear,
  generateRecommendationScheme,
  addCandidateCard,
  getCandidateCard,
  importFixtureByApi,
  importQuestionDetailsByApi,
  invalidScoresFixture,
  scoreQuestionTrendFixtureOne,
  scoreQuestionTrendFixtureTwo,
  scoreQuestionDetailsFixture,
  openAdvancedTool,
  openRecommendationCenter,
  openVolunteerWorkbench,
  returnToVolunteerGuide,
  scoresFixture,
  selectDropdownOption,
  setRecommendationFormForE2E,
};
