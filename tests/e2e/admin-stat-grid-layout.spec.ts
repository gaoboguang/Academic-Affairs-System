import { expect, test } from "@playwright/test";

const pagesWithStatGrids = [
  { path: "/exams", heading: "考试成绩中心" },
  { path: "/analytics", heading: "分析中心" },
  { path: "/gaokao-pathways", heading: "山东升学方案中心" },
  { path: "/recommendations", heading: "高考志愿推荐向导" },
  { path: "/system-tools", heading: "系统设置" },
];

test.describe("后台指标卡布局", () => {
  for (const item of pagesWithStatGrids) {
    test(`${item.heading} 指标卡保持横向栅格`, async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 1000 });
      await page.goto(item.path);
      await expect(page.getByRole("heading", { name: item.heading })).toBeVisible();

      const cards = page.locator(".app-stat-grid .stat-card");
      await expect(cards.first()).toBeVisible();
      const firstRowCards = await cards.evaluateAll((elements) => {
        const visibleRects = elements
          .map((element) => element.getBoundingClientRect())
          .filter((rect) => rect.width > 0 && rect.height > 0);
        if (!visibleRects.length) return [];
        const firstTop = Math.min(...visibleRects.map((rect) => rect.top));
        return visibleRects
          .filter((rect) => Math.abs(rect.top - firstTop) < 8)
          .map((rect) => ({
            width: rect.width,
            height: rect.height,
          }));
      });

      expect(firstRowCards.length).toBeGreaterThanOrEqual(2);
      for (const rect of firstRowCards) {
        expect(rect.width).toBeGreaterThanOrEqual(160);
        expect(rect.height).toBeLessThan(260);
      }
    });
  }
});
