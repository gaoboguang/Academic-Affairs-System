#!/usr/bin/env node

const { spawn } = require("node:child_process");
const net = require("node:net");

const isWindows = process.platform === "win32";
const npmCommand = isWindows ? "npm.cmd" : "npm";
const childProcesses = [];
const defaultHost = "127.0.0.1";
const defaultPorts = [
  { name: "frontend", port: 5173 },
  { name: "backend", port: 8000 },
];

function printUsage() {
  console.log(`用法: npm run dev

说明:
  同时启动本地教务工具前后端开发服务
  前端默认地址: http://127.0.0.1:5173
  后端默认地址: http://127.0.0.1:8000
`);
}

if (process.argv.includes("--help") || process.argv.includes("-h")) {
  printUsage();
  process.exit(0);
}

function spawnNamedProcess(name, args) {
  const child = spawn(npmCommand, args, {
    stdio: "inherit",
    env: process.env,
  });

  childProcesses.push(child);
  child.on("exit", (code, signal) => {
    if (signal) {
      console.log(`[${name}] 已结束 (${signal})`);
    } else if (code && code !== 0) {
      console.error(`[${name}] 退出码 ${code}`);
      shutdown(code);
    }
  });
  child.on("error", (error) => {
    console.error(`[${name}] 启动失败: ${error.message}`);
    shutdown(1);
  });
  return child;
}

let shuttingDown = false;

function shutdown(code = 0) {
  if (shuttingDown) return;
  shuttingDown = true;
  for (const child of childProcesses) {
    if (!child.killed) {
      child.kill("SIGTERM");
    }
  }
  setTimeout(() => process.exit(code), 100);
}

process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));

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

function formatPortError(serviceName, portInfo) {
  if (portInfo.code === "EADDRINUSE") {
    return `[${serviceName}] 端口 ${defaultHost}:${portInfo.port} 已被占用。请先关闭现有进程，或直接复用当前已启动的服务。`;
  }
  if (portInfo.code === "EPERM") {
    return `[${serviceName}] 当前上下文没有权限监听 ${defaultHost}:${portInfo.port}。请换一个启动上下文，或改为单独启动前后端。`;
  }
  return `[${serviceName}] 无法监听 ${defaultHost}:${portInfo.port}：${portInfo.message || portInfo.code || "未知错误"}`;
}

async function preflightPorts() {
  const results = await Promise.all(
    defaultPorts.map(async (item) => ({
      ...item,
      ...(await checkPortAvailability(defaultHost, item.port)),
    })),
  );
  const failed = results.filter((item) => !item.ok);
  if (!failed.length) {
    return true;
  }

  console.error("启动前检查失败：");
  for (const item of failed) {
    console.error(formatPortError(item.name, item));
  }
  return false;
}

async function main() {
  console.log("正在启动本地教务工具开发服务...");
  console.log(`前端默认地址: http://${defaultHost}:5173`);
  console.log(`后端默认地址: http://${defaultHost}:8000`);

  const portsReady = await preflightPorts();
  if (!portsReady) {
    process.exit(1);
  }

  spawnNamedProcess("backend", ["run", "backend:dev"]);
  spawnNamedProcess("frontend", ["run", "frontend:dev"]);
}

main().catch((error) => {
  console.error(`启动失败: ${error.message}`);
  shutdown(1);
});
