/**
 * Standalone analytics smoke test against the running dev servers (:8000 + :5173).
 */
import { expect, test, type Page } from "@playwright/test";

const FRONTEND = "http://localhost:5173";

test.describe.configure({ mode: "serial" });

async function gotoAnalytics(page: Page): Promise<void> {
  await page.goto(`${FRONTEND}/analytics`, { waitUntil: "networkidle" });
  // Page already auto-selects the latest exam; just wait for the tablist.
  await page.getByRole("tab", { name: "学生分析" }).waitFor({ timeout: 10_000 });
}

async function clickTab(page: Page, name: string): Promise<void> {
  await page.getByRole("tab", { name }).click();
}

test("学生分析 - 趋势/结构/同分段/目标线四张新卡片渲染", async ({ page }) => {
  await gotoAnalytics(page);
  await clickTab(page, "学生分析");

  // The student tab auto-selects the first student from the option list and
  // fills the combobox; we just need to click 查询 to trigger the API call.
  await page.getByRole("button", { name: "查询" }).first().waitFor({ state: "visible", timeout: 8000 });
  await page.getByRole("button", { name: "查询" }).first().click();
  await page.waitForLoadState("networkidle");

  // The four new cards should render. Use first-matched headings to dodge any
  // duplicates inside collapsed sub-panels.
  await expect(page.getByRole("heading", { name: "趋势与稳定性" })).toBeVisible({ timeout: 10_000 });
  await expect(page.getByRole("heading", { name: "学科结构与短板" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "同分段对比" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "目标线达成进度" })).toBeVisible();

  // Snapshot for human review.
  await page.screenshot({
    path: "test-results/analytics-student-cards.png",
    fullPage: true,
  });
});

test("年级分析页签可正常打开", async ({ page }) => {
  await gotoAnalytics(page);
  await clickTab(page, "年级分析");
  await page.waitForLoadState("networkidle");
  // Headers from the existing layout should be present.
  await expect(page.getByRole("heading", { name: "年级分析" })).toBeVisible();
  await page.screenshot({
    path: "test-results/analytics-grade-tab.png",
    fullPage: true,
  });
});

test("班级分析页签可正常打开", async ({ page }) => {
  // We skip the heatmap interaction here because the dropdown's class options
  // depend on the active dataset's class naming. The heatmap component is
  // covered by chart-options.test.ts and the API by test_knowledge_v22.py.
  await gotoAnalytics(page);
  await clickTab(page, "班级分析");
  await expect(page.getByRole("heading", { name: "班级分析", level: 3 })).toBeVisible();
  await page.screenshot({
    path: "test-results/analytics-class-tab.png",
    fullPage: true,
  });
});
