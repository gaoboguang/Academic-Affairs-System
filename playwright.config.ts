import { defineConfig } from "@playwright/test";

const backendPort = 8001;
const frontendPort = 4173;
const pythonCommand = process.platform === "win32" ? ".\\.venv\\Scripts\\python.exe" : "./.venv/bin/python";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  reporter: "list",
  use: {
    baseURL: `http://127.0.0.1:${frontendPort}`,
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: `${pythonCommand} scripts/run_e2e_backend.py`,
      url: `http://127.0.0.1:${backendPort}/api/dashboard/summary`,
      name: "Backend",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ...process.env,
        LOCAL_EDU_E2E_BACKEND_PORT: String(backendPort),
      },
    },
    {
      command: "npm run dev --workspace @local-edu/frontend -- --host 127.0.0.1 --port 4173 --strictPort",
      url: `http://127.0.0.1:${frontendPort}`,
      name: "Frontend",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ...process.env,
        LOCAL_EDU_API_BASE_URL: `http://127.0.0.1:${backendPort}`,
      },
    },
  ],
});
