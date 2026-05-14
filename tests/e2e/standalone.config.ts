/**
 * Standalone Playwright config — uses the already-running dev servers
 * (backend :8000, frontend :5173). No webServer block, no auto-start.
 */
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  testMatch: ["analytics-smoke.spec.ts"],
  fullyParallel: false,
  retries: 1,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  reporter: "list",
  use: {
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
});
