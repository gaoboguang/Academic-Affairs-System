#!/usr/bin/env node

const { spawnSync } = require("node:child_process");
const path = require("node:path");

const rootDir = path.resolve(__dirname, "..");
const isWindows = process.platform === "win32";
const npmCommand = isWindows ? "npm.cmd" : "npm";

const steps = {
  backend: {
    label: "后端测试",
    command: npmCommand,
    args: ["run", "backend:test"],
    purpose: "验证后端接口、服务、导入导出、数据健康和推荐工作流没有回退。",
    failureHint:
      "先看上方第一个失败用例。若提示找不到 pytest 或虚拟环境，请先按 Mac 开发说明创建 `.venv` 并安装后端依赖；若是业务断言失败，优先修复代码或测试数据，不要删除测试。",
  },
  frontendLint: {
    label: "前端静态检查",
    command: npmCommand,
    args: ["run", "frontend:lint"],
    purpose: "验证前端 TypeScript/Vue 代码风格和明显静态问题。",
    failureHint: "先按上方文件路径修复 lint 报错。若提示找不到 eslint 或依赖，请先执行 `npm install`。",
  },
  frontendTest: {
    label: "前端单元测试",
    command: npmCommand,
    args: ["run", "frontend:test"],
    purpose: "验证前端 helper、文案映射、报表摘要、推荐解释和页面状态逻辑。",
    failureHint:
      "先看失败测试名称和期望值差异。若是业务文案变化，应同步更新共享 helper 和对应测试，不要只改页面局部文案。",
  },
  frontendBuild: {
    label: "前端生产构建",
    command: npmCommand,
    args: ["run", "frontend:build"],
    purpose: "验证前端类型检查和 Vite 生产构建可以通过。",
    failureHint: "先修复上方 TypeScript 或构建错误。若提示找不到依赖，请执行 `npm install`；不要用跳过类型检查来绕过问题。",
  },
  e2e: {
    label: "跨端 E2E 回归",
    command: npmCommand,
    args: ["run", "e2e", "--", "tests/e2e"],
    purpose: "按业务域验证浏览器里工作台、学生、考试分析、报表、推荐、高考志愿和系统备份等主流程。",
    failureHint:
      "先看失败文件名定位业务域，再看 Playwright 给出的失败截图、trace 或第一个失败步骤。若提示浏览器缺失，执行 `npm run e2e:install`；若是页面等待超时，先确认后端临时服务、前端页面和测试前置数据是否正常。",
  },
};

const gates = {
  check: {
    label: "常规质量门禁",
    description: "后端全量测试 + 前端 lint + 前端单测 + 前端构建。",
    stepKeys: ["backend", "frontendLint", "frontendTest", "frontendBuild"],
  },
  e2e: {
    label: "跨端质量门禁",
    description: "运行 Playwright 分域跨端流程。",
    stepKeys: ["e2e"],
  },
  all: {
    label: "完整质量门禁",
    description: "先跑常规质量门禁，再跑跨端 E2E。",
    stepKeys: ["backend", "frontendLint", "frontendTest", "frontendBuild", "e2e"],
  },
};

function printUsage() {
  console.log(`用法: node scripts/quality-gate.cjs <check|e2e|all|--list>

说明:
  check  = ${gates.check.description}
  e2e    = ${gates.e2e.description}
  all    = ${gates.all.description}

这只是把现有检查命令按阶段包装起来，便于非程序员看懂通过/失败位置。`);
}

function printList() {
  for (const [key, gate] of Object.entries(gates)) {
    console.log(`${key}: ${gate.label}`);
    console.log(`  ${gate.description}`);
    for (const stepKey of gate.stepKeys) {
      const step = steps[stepKey];
      console.log(`  - ${step.label}: ${formatCommand(step.command, step.args)}`);
    }
  }
}

function ensureNodeVersion() {
  const major = Number(process.versions.node.split(".")[0]);
  if (Number.isFinite(major) && major >= 20) {
    return true;
  }
  console.error("Node.js 版本过低，无法可靠运行当前项目检查。");
  console.error(`当前版本: ${process.version}`);
  console.error("请安装 Node.js 20 或更高版本后重试。");
  return false;
}

function formatCommand(command, args) {
  return [command, ...args].join(" ");
}

function runStep(step, index, total) {
  const start = Date.now();
  console.log("");
  console.log(`== ${index}/${total} ${step.label} ==`);
  console.log(`作用: ${step.purpose}`);
  console.log(`命令: ${formatCommand(step.command, step.args)}`);

  const result = spawnSync(step.command, step.args, {
    cwd: rootDir,
    env: process.env,
    stdio: "inherit",
  });

  const seconds = ((Date.now() - start) / 1000).toFixed(1);
  if (result.error) {
    console.error("");
    console.error(`${step.label} 未能启动。`);
    console.error(`原因: ${result.error.message}`);
    console.error(step.failureHint);
    return false;
  }

  if (result.status !== 0) {
    console.error("");
    console.error(`${step.label} 未通过，退出码 ${result.status ?? "未知"}，耗时 ${seconds}s。`);
    console.error(step.failureHint);
    return false;
  }

  console.log(`${step.label} 通过，耗时 ${seconds}s。`);
  return true;
}

function main() {
  const gateName = process.argv[2] || "check";
  if (gateName === "--help" || gateName === "-h") {
    printUsage();
    return 0;
  }
  if (gateName === "--list") {
    printList();
    return 0;
  }

  const gate = gates[gateName];
  if (!gate) {
    console.error(`未知质量门禁: ${gateName}`);
    printUsage();
    return 1;
  }
  if (!ensureNodeVersion()) {
    return 1;
  }

  console.log(gate.label);
  console.log(gate.description);

  const selectedSteps = gate.stepKeys.map((key) => steps[key]);
  for (let index = 0; index < selectedSteps.length; index += 1) {
    const ok = runStep(selectedSteps[index], index + 1, selectedSteps.length);
    if (!ok) {
      console.error("");
      console.error("质量门禁未通过。请先处理上面的第一个失败点，再重新运行本命令。");
      return 1;
    }
  }

  console.log("");
  console.log("质量门禁通过。");
  return 0;
}

process.exitCode = main();
