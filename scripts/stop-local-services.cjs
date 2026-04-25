#!/usr/bin/env node

const fs = require("node:fs");
const path = require("node:path");

const rootDir = path.resolve(__dirname, "..");
const logDir = path.join(rootDir, "data", "logs", "local-services");

const services = [
  { name: "frontend", label: "前端", port: 5173 },
  { name: "backend", label: "后端", port: 8000 },
];

function pidPathFor(service) {
  return path.join(logDir, `${service.name}.pid.json`);
}

function readPid(service) {
  const pidPath = pidPathFor(service);
  if (!fs.existsSync(pidPath)) return null;
  try {
    const data = JSON.parse(fs.readFileSync(pidPath, "utf8"));
    return Number(data.pid) || null;
  } catch {
    return null;
  }
}

function stopPidGroup(pid) {
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

function main() {
  console.log("正在停止本地教务工具后台服务...");
  for (const service of services) {
    const pid = readPid(service);
    if (!pid) {
      console.log(`[${service.label}] 没有找到后台启动记录，跳过。`);
      continue;
    }

    const stopped = stopPidGroup(pid);
    if (stopped) {
      console.log(`[${service.label}] 已发送停止信号，pid=${pid}`);
      continue;
    }

    console.log(`[${service.label}] pid=${pid} 已不存在或无须停止。`);
  }
  console.log("如果页面仍可访问，说明服务不是由后台启动器创建的，可重新检查端口占用。");
}

main();
