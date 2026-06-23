import fs from "node:fs";
import path from "node:path";

import { request } from "@playwright/test";

const backendPort = process.env.LOCAL_EDU_E2E_BACKEND_PORT ?? "8001";
const storagePath = path.resolve(process.cwd(), ".tmp/e2e-auth-state.json");

async function globalSetup(): Promise<void> {
  fs.mkdirSync(path.dirname(storagePath), { recursive: true });
  const context = await request.newContext({
    baseURL: `http://127.0.0.1:${backendPort}`,
  });
  const response = await context.post("/api/auth/login", {
    data: {
      username: "admin",
      password: "AdminPass123!",
    },
  });
  if (!response.ok()) {
    throw new Error(`E2E 管理员登录失败：${response.status()} ${await response.text()}`);
  }
  await context.storageState({ path: storagePath });
  await context.dispose();
}

export default globalSetup;
