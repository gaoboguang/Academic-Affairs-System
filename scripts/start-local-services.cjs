#!/usr/bin/env node

const { spawn } = require("node:child_process");
const fs = require("node:fs");
const http = require("node:http");
const net = require("node:net");
const path = require("node:path");

const rootDir = path.resolve(__dirname, "..");
const isWindows = process.platform === "win32";
const isMac = process.platform === "darwin";
const npmCommand = isWindows ? "npm.cmd" : "npm";
const defaultHost = "127.0.0.1";
const logDir = path.join(rootDir, "data", "logs", "local-services");
const shouldOpen = !process.argv.includes("--no-open") && process.env.NO_OPEN !== "1";

const services = [
  {
    name: "backend",
    label: "后端",
    port: 8000,
    healthPath: "/api/system/health",
    startArgs: ["run", "backend:dev"],
    url: "http://127.0.0.1:8000",
  },
  {
    name: "frontend",
    label: "前端",
    port: 5173,
    healthPath: "/",
    startArgs: ["run", "frontend:dev"],
    url: "http://127.0.0.1:5173",
  },
];

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function ensureLogDir() {
  fs.mkdirSync(logDir, { recursive: true });
}

function checkHttpHealth(host, port, requestPath) {
  return new Promise((resolve) => {
    const request = http.get(
      {
        host,
        port,
        path: requestPath,
        timeout: 1000,
      },
      (response) => {
        response.resume();
        resolve({
          ok: Boolean(response.statusCode && response.statusCode >= 200 && response.statusCode < 400),
          statusCode: response.statusCode,
          message: null,
        });
      },
    );

    request.on("timeout", () => {
      request.destroy();
      resolve({ ok: false, statusCode: null, message: "健康检查超时" });
    });
    request.on("error", (error) => {
      resolve({ ok: false, statusCode: null, message: error.message });
    });
  });
}

function checkPortAvailability(host, port) {
  return new Promise((resolve) => {
    const server = net.createServer();

    server.once("error", (error) => {
      resolve({
        ok: false,
        code: error.code || "UNKNOWN",
        message: error.message,
      });
    });

    server.once("listening", () => {
      server.close(() => {
        resolve({ ok: true, code: null, message: null });
      });
    });

    server.listen(port, host);
  });
}

function logPathFor(service) {
  return path.join(logDir, `${service.name}.log`);
}

function pidPathFor(service) {
  return path.join(logDir, `${service.name}.pid.json`);
}

function readPidInfo(service) {
  const pidPath = pidPathFor(service);
  if (!fs.existsSync(pidPath)) return null;
  try {
    const data = JSON.parse(fs.readFileSync(pidPath, "utf8").replace(/^\uFEFF/, ""));
    const pid = Number(data.pid);
    if (!Number.isInteger(pid) || pid <= 0) return null;
    return { ...data, pid, pidPath };
  } catch {
    return null;
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

function removePidFile(service) {
  try {
    fs.rmSync(pidPathFor(service), { force: true });
  } catch {
    // 清理失败不阻断启动，后续健康检查仍会给出真实状态。
  }
}

function getLogTail(service, maxLines = 30) {
  const logPath = logPathFor(service);
  if (!fs.existsSync(logPath)) return "暂无日志。";
  const content = fs.readFileSync(logPath, "utf8").trimEnd();
  if (!content) return "日志为空。";
  return content.split(/\r?\n/).slice(-maxLines).join("\n");
}

function cleanupStalePidFile(service, pidInfo, health) {
  if (!pidInfo) return;
  if (health.ok || isProcessRunning(pidInfo.pid)) return;
  removePidFile(service);
  console.log(`[${service.label}] 已清理过期启动记录，旧 pid=${pidInfo.pid}`);
}

async function inspectService(service) {
  const pidInfo = readPidInfo(service);
  const health = await checkHttpHealth(defaultHost, service.port, service.healthPath);
  if (health.ok) {
    return { ...service, running: true, ok: true, health, pidInfo };
  }
  cleanupStalePidFile(service, pidInfo, health);

  const portState = await checkPortAvailability(defaultHost, service.port);
  return {
    ...service,
    running: false,
    ok: portState.ok,
    health,
    portState,
    pidInfo,
  };
}

function startDetachedService(service) {
  const logPath = logPathFor(service);
  const out = fs.openSync(logPath, "a");
  const err = fs.openSync(logPath, "a");
  fs.appendFileSync(logPath, `\n\n===== ${new Date().toISOString()} start ${service.name} =====\n`);

  const command = isWindows ? (process.env.ComSpec || "cmd.exe") : npmCommand;
  const args = isWindows ? ["/d", "/s", "/c", npmCommand, ...service.startArgs] : service.startArgs;

  const child = spawn(command, args, {
    cwd: rootDir,
    detached: true,
    stdio: ["ignore", out, err],
    env: process.env,
  });

  child.unref();

  fs.writeFileSync(
    pidPathFor(service),
    JSON.stringify(
      {
        pid: child.pid,
        command: `${command} ${args.join(" ")}`,
        url: service.url,
        log: logPath,
        startedAt: new Date().toISOString(),
      },
      null,
      2,
    ),
  );

  return child.pid;
}

async function waitForService(service, timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const health = await checkHttpHealth(defaultHost, service.port, service.healthPath);
    if (health.ok) return true;
    await sleep(1000);
  }
  return false;
}

function openFrontend() {
  if (!shouldOpen) return;

  if (isMac) {
    const child = spawn("open", ["http://127.0.0.1:5173"], {
      detached: true,
      stdio: "ignore",
    });
    child.unref();
    return;
  }

  if (isWindows) {
    const child = spawn("cmd", ["/c", "start", "", "http://127.0.0.1:5173"], {
      detached: true,
      stdio: "ignore",
    });
    child.unref();
  }
}

function formatBlockedPort(service, state) {
  const code = state.portState?.code || "UNKNOWN";
  const message = state.portState?.message || state.health?.message || "未知错误";
  if (code === "EADDRINUSE") {
    return `${service.label}端口 ${defaultHost}:${service.port} 已被占用，但健康检查没有通过。请先关闭占用该端口的异常进程。`;
  }
  return `${service.label}无法监听 ${defaultHost}:${service.port}：${message}`;
}

async function main() {
  ensureLogDir();

  console.log("正在检查本地教务工具服务...");
  console.log(`前端页面: http://${defaultHost}:5173`);
  console.log(`后端服务: http://${defaultHost}:8000`);
  console.log(`日志目录: ${logDir}`);
  console.log("");

  const states = await Promise.all(services.map(inspectService));
  const blocked = states.filter((state) => !state.running && !state.ok);
  if (blocked.length) {
    for (const state of blocked) {
      console.error(formatBlockedPort(state, state));
    }
    process.exit(1);
  }

  const started = [];
  for (const state of states) {
    if (state.running) {
      console.log(`[${state.label}] 已在运行，复用 ${state.url}`);
      continue;
    }
    const pid = startDetachedService(state);
    started.push(state);
    console.log(`[${state.label}] 已后台启动，pid=${pid}，日志=${logPathFor(state)}`);
  }

  for (const service of started) {
    const ok = await waitForService(service);
    if (!ok) {
      console.error(`[${service.label}] 启动后健康检查未通过，请查看日志：${logPathFor(service)}`);
      console.error("");
      console.error(`[${service.label}] 最近日志：`);
      console.error(getLogTail(service));
      process.exit(1);
    }
  }

  const finalStates = await Promise.all(services.map(inspectService));
  const notReady = finalStates.filter((state) => !state.running);
  if (notReady.length) {
    for (const state of notReady) {
      console.error(`[${state.label}] 仍不可用：${state.health?.message || "未知错误"}`);
    }
    process.exit(1);
  }

  openFrontend();
  console.log("");
  console.log("本地教务工具已可用。");
  console.log("浏览器地址: http://127.0.0.1:5173");
  console.log("后台日志:");
  for (const service of services) {
    console.log(`- ${service.label}: ${logPathFor(service)}`);
  }
}

main().catch((error) => {
  console.error(`启动失败: ${error.message}`);
  process.exit(1);
});
