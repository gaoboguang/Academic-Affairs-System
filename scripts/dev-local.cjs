#!/usr/bin/env node

const { spawn } = require("node:child_process");
const http = require("node:http");
const net = require("node:net");
const path = require("node:path");

const rootDir = path.resolve(__dirname, "..");
const isWindows = process.platform === "win32";
const npmCommand = isWindows ? "npm.cmd" : "npm";
const childProcesses = [];
const defaultHost = "127.0.0.1";
const services = [
  {
    name: "backend",
    port: 8000,
    healthPath: "/api/system/health",
    startArgs: ["run", "backend:dev"],
    url: "http://127.0.0.1:8000",
  },
  {
    name: "frontend",
    port: 5173,
    healthPath: "/",
    startArgs: ["run", "frontend:dev"],
    url: "http://127.0.0.1:5173",
  },
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
    cwd: rootDir,
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

function checkHttpHealth(host, port, path) {
  return new Promise((resolve) => {
    const request = http.get(
      {
        host,
        port,
        path,
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

function formatPortError(serviceName, portInfo) {
  if (portInfo.code === "EADDRINUSE") {
    return `[${serviceName}] 端口 ${defaultHost}:${portInfo.port} 已被占用，但健康检查未通过。请先关闭占用进程，或检查该端口上的服务日志。`;
  }
  if (portInfo.code === "EPERM") {
    return `[${serviceName}] 当前上下文没有权限监听 ${defaultHost}:${portInfo.port}。请换一个启动上下文，或改为单独启动前后端。`;
  }
  return `[${serviceName}] 无法监听 ${defaultHost}:${portInfo.port}：${portInfo.message || portInfo.code || "未知错误"}`;
}

async function preflightServices() {
  const results = await Promise.all(
    services.map(async (item) => {
      const health = await checkHttpHealth(defaultHost, item.port, item.healthPath);
      if (health.ok) {
        return {
          ...item,
          ok: true,
          running: true,
          code: null,
          message: null,
        };
      }

      const port = await checkPortAvailability(defaultHost, item.port);
      return {
        ...item,
        ...port,
        running: false,
      };
    }),
  );
  const failed = results.filter((item) => !item.ok);
  if (!failed.length) {
    return results;
  }

  console.error("启动前检查失败：");
  for (const item of failed) {
    console.error(formatPortError(item.name, item));
  }
  return null;
}

async function main() {
  console.log("正在启动本地教务工具开发服务...");
  console.log(`前端默认地址: http://${defaultHost}:5173`);
  console.log(`后端默认地址: http://${defaultHost}:8000`);

  const serviceStates = await preflightServices();
  if (!serviceStates) {
    process.exit(1);
  }

  const runningServices = serviceStates.filter((item) => item.running);
  for (const item of runningServices) {
    console.log(`[${item.name}] 已在运行，复用 ${item.url}`);
  }

  const servicesToStart = serviceStates.filter((item) => !item.running);
  if (!servicesToStart.length) {
    console.log("前后端服务均已可用，无需重复启动。");
    return;
  }

  for (const item of servicesToStart) {
    spawnNamedProcess(item.name, item.startArgs);
  }
}

main().catch((error) => {
  console.error(`启动失败: ${error.message}`);
  shutdown(1);
});
