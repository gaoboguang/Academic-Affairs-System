import { expect, test } from "@playwright/test";
import {
  confirmDialogIfVisible,
  createVolunteerDraft,
  e2eExamName,
  ensureEnrollmentPlansImported,
  ensureMajorEmploymentProfile,
  ensureStudentOriginProvince,
  ensureVolunteerRuleConfigured,
  expectToast,
  fillVolunteerWorkbenchContext,
  addCandidateCard,
  getCandidateCard,
  openAdvancedTool,
  openRecommendationCenter,
  openVolunteerWorkbench,
  returnToVolunteerGuide,
  selectDropdownOption,
} from "./helpers/localEduE2e";

test("Stage B 主链路：生源地回退的模拟推荐可同步到工作台并保存草稿", async ({ page }) => {
  test.setTimeout(60000);
  await ensureStudentOriginProvince(page);

  const generatePanel = await openRecommendationCenter(page);
  const generateSelects = generatePanel.locator(".filter-grid .el-select");
  const schemeName = `E2E-StageB-模拟链路-${Date.now()}`;
  const draftName = `E2E-StageB-草稿-${Date.now()}`;

  await selectDropdownOption(page, generateSelects.nth(0), "2026001 - 张三");
  await selectDropdownOption(page, generateSelects.nth(3), "广东");
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

  await openAdvancedTool(page, "历史方案");
  const historyPanel = page.locator(".panel-block").filter({ hasText: "推荐历史" });
  await historyPanel.getByRole("button", { name: "查询历史" }).click();
  const historyRow = historyPanel.locator(".el-table__row").filter({ hasText: schemeName }).first();
  await expect(historyRow).toContainText("广东");
  await expect(historyRow).toContainText("2026");
  await expect(historyRow).toContainText("预估分数 + 预估位次");
  await expect(historyRow).toContainText("参考 2026届一模");

  await openAdvancedTool(page, "数据与规则");
  await page.getByRole("tab", { name: "招生计划库" }).click();
  await ensureEnrollmentPlansImported(page);
  await ensureVolunteerRuleConfigured(page);
  const workbenchPanel = await returnToVolunteerGuide(page);
  await expect(workbenchPanel.getByRole("heading", { name: "志愿推荐向导" })).toBeVisible();
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

  await workbenchPanel.getByRole("button", { name: "生成智能筛选" }).click();
  await expectToast(page, "智能筛选已生成");
  await workbenchPanel.getByText("查看依据与复核明细").click();
  await expect(workbenchPanel.getByText("当前成绩/位次来源为“预估分 + 预估位次（本次考试/模拟推荐）”。")).toBeVisible();
  await expect(workbenchPanel.getByText("先按 广东 / 2026 / 本科批 / 物理类 限定招生计划范围。")).toBeVisible();

  const candidatePanel = workbenchPanel.locator(".nested-panel").first();
  const draftPanel = workbenchPanel.locator(".nested-panel").nth(1);
  await expect(candidatePanel.getByText("近三年招生/录取情况").first()).toBeVisible();
  await addCandidateCard(candidatePanel, "软件工程");
  await expectToast(page, "已加入志愿表");
  await expect(draftPanel.locator(".el-table__row").filter({ hasText: "软件工程" }).first()).toBeVisible();

  await workbenchPanel.getByPlaceholder("草稿名称，例如：张三-本科批第一版").fill(draftName);
  await workbenchPanel.getByRole("button", { name: "保存草稿" }).click();
  await expectToast(page, "志愿草稿已保存");
  await expect(draftPanel.locator(".saved-draft-card").filter({ hasText: draftName }).first()).toBeVisible();
});

test("高考志愿主流程：可生成智能筛选、保存草稿并打印导出志愿表", async ({ page }) => {
  test.setTimeout(60000);
  const { workbenchPanel, draftPanel, draftName } = await createVolunteerDraft(page);
  await expect(workbenchPanel.getByText("校内考试口径，仅作模拟参考").first()).toBeVisible();
  await workbenchPanel.getByText("查看依据与复核明细").click();
  await expect(workbenchPanel.getByRole("heading", { name: "筛选解释" })).toBeVisible();
  await expect(workbenchPanel.getByRole("heading", { name: "风险校验" })).toBeVisible();
  await expect(workbenchPanel.getByText("当前草稿已纳入 2 条志愿")).toBeVisible();
  await expect(workbenchPanel.getByText("院校代码").first()).toBeVisible();
  await expect(workbenchPanel.getByText("专业代码").first()).toBeVisible();
  await draftPanel.locator(".el-table__row").filter({ hasText: "人工智能" }).first().getByRole("button", { name: "上移" }).click();
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
  await expect(workbenchPanel.getByRole("heading", { name: "志愿推荐向导" })).toBeVisible();

  await openAdvancedTool(page, "数据与规则");
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

  await returnToVolunteerGuide(page);
  await expect(workbenchPanel.getByRole("heading", { name: "志愿推荐向导" })).toBeVisible();

  await fillVolunteerWorkbenchContext(page, workbenchPanel, { majorKeyword: "软件" });
  await workbenchPanel.getByRole("button", { name: "生成智能筛选" }).click();
  await expectToast(page, "智能筛选已生成");
  await expect(workbenchPanel.locator(".el-alert").filter({ hasText: "已匹配 1 条候选计划" }).first()).toBeVisible();
  await expect(getCandidateCard(candidatePanel, "软件工程")).toBeVisible();
  await expect(candidatePanel.locator(".candidate-card").filter({ hasText: "人工智能" })).toHaveCount(0);

  await fillVolunteerWorkbenchContext(page, workbenchPanel, {
    examMode: "历史类",
    majorKeyword: "",
    subjectCombination: "历史",
  });
  await workbenchPanel.getByRole("button", { name: "生成智能筛选" }).click();
  await expectToast(page, "当前条件下暂无可加入志愿表的候选");
  await expect(candidatePanel.getByText("当前条件下暂无可加入志愿表的候选计划，请查看生成前复核提示。")).toBeVisible();
  await expect(workbenchPanel.getByText("已匹配 0 条候选计划")).toBeVisible();
  await expect(workbenchPanel.getByText("1 条省份规则")).toBeVisible();
  await expect(draftPanel.locator(".el-alert")).toContainText("广东 2026 历史类 · 本科批");
});

test("高考志愿：山东普通类推荐工作台可查看输入和数据质量", async ({ page }) => {
  await page.goto("/recommendations");
  await expect(page.getByRole("heading", { name: "高考志愿" })).toBeVisible();

  await openAdvancedTool(page, "山东普通类推荐");
  const shandongPanel = page.locator(".panel-block").filter({ hasText: "山东普通类推荐工作台" }).first();

  await expect(shandongPanel.getByRole("heading", { name: "山东普通类推荐工作台" })).toBeVisible();
  await expect(shandongPanel.getByText("选择学生与考试估算")).toBeVisible();
  await expect(shandongPanel.getByText("数据质量看板")).toBeVisible();
  await expect(shandongPanel.getByText("2023-2025 覆盖矩阵")).toBeVisible();
  await expect(shandongPanel.getByText("2026 发布状态", { exact: true })).toBeVisible();
});

test("高考志愿预估模式：分数区间可生成智能筛选并显示模拟说明", async ({ page }) => {
  const workbenchPanel = await openVolunteerWorkbench(page);
  const candidatePanel = workbenchPanel.locator(".nested-panel").first();

  await fillVolunteerWorkbenchContext(page, workbenchPanel);
  const filterSelects = workbenchPanel.locator(".filter-grid .el-select");
  await selectDropdownOption(page, filterSelects.nth(7), "分数区间");
  await workbenchPanel.getByPlaceholder("分数区间下限").fill("568");
  await workbenchPanel.getByPlaceholder("分数区间上限").fill("576");
  await workbenchPanel.getByPlaceholder("参考考试说明，可选").fill("2026届一模");
  await workbenchPanel.locator(".inline-switch-card .el-switch").click();

  await workbenchPanel.getByRole("button", { name: "生成智能筛选" }).click();
  await expectToast(page, "智能筛选已生成");
  await expect(workbenchPanel.locator(".el-alert").filter({ hasText: "当前按“分数区间”计算" }).first()).toBeVisible();
  await expect(workbenchPanel.locator(".el-alert").filter({ hasText: "2026届一模" }).first()).toBeVisible();
  await expect(candidatePanel.locator(".candidate-card").first()).toBeVisible();
});

test("高考志愿年份边界：缺少目标年份规则时提示人工复核", async ({ page }) => {
  const workbenchPanel = await openVolunteerWorkbench(page);

  await fillVolunteerWorkbenchContext(page, workbenchPanel);
  const filterSelects = workbenchPanel.locator(".filter-grid .el-select");
  await selectDropdownOption(page, filterSelects.nth(3), "2025");

  await workbenchPanel.getByRole("button", { name: "生成智能筛选" }).click();
  await expectToast(page, "当前条件下暂无可加入志愿表的候选");
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

  await workbenchPanel.getByRole("button", { name: "生成智能筛选" }).click();
  await expectToast(page, "智能筛选已生成");
  await expect(workbenchPanel.getByText("已匹配 2 条候选计划")).toBeVisible();
  await expect(
    workbenchPanel.locator(".el-alert").filter({ hasText: "当前未配置“3+1+2”精确规则，先按兼容模式" }).first(),
  ).toBeVisible();
  await expect(getCandidateCard(candidatePanel, "软件工程")).toBeVisible();
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
    await returnToVolunteerGuide(page);
    await expect(workbenchPanel.getByRole("heading", { name: "志愿推荐向导" })).toBeVisible();

    await fillVolunteerWorkbenchContext(page, workbenchPanel);
    await workbenchPanel.getByRole("button", { name: "生成智能筛选" }).click();
    await expectToast(page, "智能筛选已生成");

    await addCandidateCard(candidatePanel, "软件工程");
    await expectToast(page, "已加入志愿表");
    await expect(draftPanel.locator(".page-chip").filter({ hasText: "上限" }).first()).toContainText("1");
    await expect(draftPanel.locator(".page-chip").filter({ hasText: "剩余" }).first()).toContainText("0");

    await addCandidateCard(candidatePanel, "人工智能");
    await expectToast(page, "当前批次志愿上限为 1");

    await workbenchPanel.getByRole("button", { name: "保存草稿" }).click();
    await expectToast(page, "草稿名称不能为空");
  } finally {
    await ensureVolunteerRuleConfigured(page);
  }
});
