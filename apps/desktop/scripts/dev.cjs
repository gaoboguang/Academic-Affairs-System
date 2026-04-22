const { spawn } = require("node:child_process");
const path = require("node:path");
const electronBinary = require("electron");

const rootDir = path.resolve(__dirname, "..", "..", "..");
let viteProcess = null;
let electronProcess = null;

function waitForUrl(url, timeoutMs = 30000) {
  const startedAt = Date.now();
  return new Promise((resolve, reject) => {
    const check = async () => {
      if (Date.now() - startedAt > timeoutMs) {
        reject(new Error(`等待开发地址超时: ${url}`));
        return;
      }
      try {
        const response = await fetch(url);
        if (response.ok) {
          resolve();
          return;
        }
      } catch {}
      setTimeout(check, 500);
    };
    check();
  });
}

function cleanup() {
  if (electronProcess && !electronProcess.killed) {
    electronProcess.kill();
    electronProcess = null;
  }
  if (viteProcess && !viteProcess.killed) {
    viteProcess.kill();
    viteProcess = null;
  }
}

async function main() {
  viteProcess = spawn("npm", ["run", "frontend:dev"], {
    cwd: rootDir,
    stdio: "inherit",
    env: {
      ...process.env,
      LOCAL_EDU_API_BASE_URL: "http://127.0.0.1:18000",
    },
  });

  await waitForUrl("http://127.0.0.1:5173");

  electronProcess = spawn(electronBinary, ["apps/desktop/main.cjs"], {
    cwd: rootDir,
    stdio: "inherit",
    env: {
      ...process.env,
      LOCAL_EDU_DESKTOP_RENDERER_URL: "http://127.0.0.1:5173",
    },
  });

  electronProcess.on("exit", () => {
    cleanup();
    process.exit(0);
  });
}

process.on("SIGINT", () => {
  cleanup();
  process.exit(0);
});

process.on("SIGTERM", () => {
  cleanup();
  process.exit(0);
});

main().catch((error) => {
  cleanup();
  console.error(error);
  process.exit(1);
});
