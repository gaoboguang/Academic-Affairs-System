#!/usr/bin/env node

const fs = require("node:fs");
const { spawnSync } = require("node:child_process");
const http = require("node:http");
const net = require("node:net");
const path = require("node:path");

const rootDir = path.resolve(__dirname, "..");
const logDir = path.join(rootDir, "data", "logs", "local-services");
const defaultHost = "127.0.0.1";
const isWindows = process.platform === "win32";

const services = [
  { name: "frontend", label: "前端", port: 5173, healthPath: "/" },
  { name: "backend", label: "后端", port: 8000, healthPath: "/api/system/health" },
];

function pidPathFor(service) {
  return path.join(logDir, `${service.name}.pid.json`);
}

function readPid(service) {
  const pidPath = pidPathFor(service);
  if (!fs.existsSync(pidPath)) return null;
  try {
    const data = JSON.parse(fs.readFileSync(pidPath, "utf8").replace(/^\uFEFF/, ""));
    return Number(data.pid) || null;
  } catch {
    return null;
  }
}

function findWindowsPidByPort(port) {
  if (!isWindows) return null;
  const command = [
    "$conn = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort",
    String(port),
    "-State Listen -ErrorAction SilentlyContinue | Select-Object -First 1;",
    "if ($conn) { [Console]::Write($conn.OwningProcess) }",
  ].join(" ");
  const result = spawnSync("powershell.exe", ["-NoProfile", "-Command", command], {
    encoding: "utf8",
    windowsHide: true,
  });
  const pid = Number(String(result.stdout || "").trim());
  return Number.isInteger(pid) && pid > 0 ? pid : null;
}

function removePidFile(service) {
  try {
    fs.rmSync(pidPathFor(service), { force: true });
  } catch {
    // 停止流程不因清理记录失败而中断。
  }
}

function isProcessRunning(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch (error) {
    return error && error.code === "EPERM";
  }
}

function stopPidGroup(pid) {
  if (isWindows) {
    const result = spawnSync("taskkill.exe", ["/PID", String(pid), "/T", "/F"], {
      stdio: "ignore",
    });
    return result.status === 0;
  }

  try {
    process.kill(-pid, "SIGTERM");
    return true;
  } catch {
    try {
      process.kill(pid, "SIGTERM");
      return true;
    } catch {
      return false;
    }
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function checkHttpHealth(service) {
  return new Promise((resolve) => {
    const request = http.get(
      {
        host: defaultHost,
        port: service.port,
        path: service.healthPath,
        timeout: 1000,
      },
      (response) => {
        response.resume();
        resolve(Boolean(response.statusCode && response.statusCode >= 200 && response.statusCode < 400));
      },
    );

    request.on("timeout", () => {
      request.destroy();
      resolve(false);
    });
    request.on("error", () => resolve(false));
  });
}

function checkPortAvailability(service) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once("error", () => resolve(false));
    server.once("listening", () => {
      server.close(() => resolve(true));
    });
    server.listen(service.port, defaultHost);
  });
}

async function waitUntilStopped(service, timeoutMs = 10000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const healthy = await checkHttpHealth(service);
    const portAvailable = await checkPortAvailability(service);
    if (!healthy && portAvailable) return true;
    await sleep(500);
  }
  return false;
}

async function main() {
  console.log("正在停止本地教务工具后台服务...");
  for (const service of services) {
    const pid = readPid(service);
    if (!pid) {
      removePidFile(service);
      const healthy = await checkHttpHealth(service);
      if (healthy) {
        const portPid = findWindowsPidByPort(service.port);
        if (portPid && stopPidGroup(portPid)) {
          const stoppedCleanly = await waitUntilStopped(service);
          console.log(
            stoppedCleanly
              ? `[${service.label}] 已按端口停止，pid=${portPid}`
              : `[${service.label}] 已按端口发送停止请求，pid=${portPid}；端口可能仍在释放中`,
          );
        } else {
          console.log(`[${service.label}] 没有后台启动记录，但端口仍有可用服务：${defaultHost}:${service.port}`);
        }
      } else {
        console.log(`[${service.label}] 没有找到后台启动记录，跳过。`);
      }
      continue;
    }

    if (!isProcessRunning(pid)) {
      removePidFile(service);
      console.log(`[${service.label}] 旧 pid=${pid} 已不存在，已清理启动记录。`);
      continue;
    }

    const stopped = stopPidGroup(pid);
    if (stopped) {
      const stoppedCleanly = await waitUntilStopped(service);
      if (stoppedCleanly) {
        removePidFile(service);
        console.log(`[${service.label}] 已停止，pid=${pid}`);
      } else {
        if (isProcessRunning(pid)) {
          console.log(`[${service.label}] 已发送停止信号，pid=${pid}；进程仍在退出中，可稍后再次执行停止。`);
        } else {
          removePidFile(service);
          console.log(`[${service.label}] 进程已结束，但端口可能被其它程序占用：${defaultHost}:${service.port}`);
        }
      }
      continue;
    }

    removePidFile(service);
    console.log(`[${service.label}] pid=${pid} 已不存在或无须停止，已清理启动记录。`);
  }
  console.log("如果页面仍可访问，说明服务不是由后台启动器创建的，可重新检查端口占用。");
}

main().catch((error) => {
  console.error(`停止失败: ${error.message}`);
  process.exit(1);
});
