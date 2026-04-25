#!/usr/bin/env node

const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const rootDir = path.resolve(__dirname, "..");
const backendDir = path.join(rootDir, "apps", "backend");
const isWindows = process.platform === "win32";
const venvDir = path.join(rootDir, ".venv");
const venvBinDir = path.join(venvDir, isWindows ? "Scripts" : "bin");

function resolveVenvExecutable(name) {
  const suffix = isWindows ? ".exe" : "";
  const direct = path.join(venvBinDir, `${name}${suffix}`);
  if (fs.existsSync(direct)) {
    return direct;
  }

  if (isWindows) {
    const commandShim = path.join(venvBinDir, `${name}.cmd`);
    if (fs.existsSync(commandShim)) {
      return commandShim;
    }
  }

  return null;
}

function requireExecutable(name, installHint) {
  const executable = resolveVenvExecutable(name);
  if (executable) {
    return executable;
  }

  console.error(`未找到 ${name} 对应的虚拟环境可执行文件。`);
  console.error(`期望位置：${path.join(venvBinDir, name)}`);
  console.error(installHint);
  process.exit(1);
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd ?? rootDir,
    stdio: "inherit",
    env: process.env,
  });

  if (result.error) {
    throw result.error;
  }

  process.exit(result.status ?? 1);
}

function printUsage() {
  console.log(`用法: node scripts/backend-cli.cjs <command>

支持命令:
  dev        启动后端开发服务
  migrate    执行 Alembic 迁移
  merge-handoff  把 handoff 高考原始表并入主库
  materialize-gaokao  把 raw 高考表整理到业务表
  bootstrap-special-types  装载山东特殊类型规则字典
  bootstrap-pathways  装载山东升学路径和 D2 官方规则字典
  gaokao-sources  登记山东高考官方来源并准备导入目录
  gaokao-import-official  登记人工下载的高考官方文件和导入批次
  gaokao-import-shandong-core  导入 2023-2025 山东官方投档表、一分一段和省控线
  data-health  检查 data/app.db 的 P0 数据健康状态
  p0-check  执行 P0 本地交付验收
  init-demo  初始化模板、基础数据和演示数据
  test       运行后端测试
`);
}

const command = process.argv[2];
const extraArgs = process.argv.slice(3);

if (!command || command === "--help" || command === "-h") {
  printUsage();
  process.exit(command ? 0 : 1);
}

switch (command) {
  case "dev": {
    const python = requireExecutable(
      "python",
      "请先创建 `.venv` 并安装后端依赖，例如运行 `./scripts/dev.sh` 或手工执行 `pip install -e \"./apps/backend[dev]\"`。",
    );
    run(python, ["-m", "uvicorn", "app.main:app", "--app-dir", "apps/backend", "--host", "127.0.0.1", "--port", "8000", ...extraArgs]);
    break;
  }
  case "migrate": {
    const alembic = requireExecutable(
      "alembic",
      "请先安装后端依赖，例如执行 `pip install -e \"./apps/backend[dev]\"`。",
    );
    run(alembic, ["upgrade", "head", ...extraArgs], { cwd: backendDir });
    break;
  }
  case "init-demo": {
    const python = requireExecutable(
      "python",
      "请先创建 `.venv` 并安装后端依赖，例如运行 `./scripts/dev.sh` 或手工执行 `pip install -e \"./apps/backend[dev]\"`。",
    );
    run(python, ["scripts/init_data.py", "--demo", ...extraArgs]);
    break;
  }
  case "merge-handoff": {
    const python = requireExecutable(
      "python",
      "请先创建 `.venv` 并安装后端依赖，例如运行 `./scripts/dev.sh` 或手工执行 `pip install -e \"./apps/backend[dev]\"`。",
    );
    run(python, ["scripts/merge_handoff_gaokao_db.py", ...extraArgs]);
    break;
  }
  case "materialize-gaokao": {
    const python = requireExecutable(
      "python",
      "请先创建 `.venv` 并安装后端依赖，例如运行 `./scripts/dev.sh` 或手工执行 `pip install -e \"./apps/backend[dev]\"`。",
    );
    run(python, ["scripts/materialize_gaokao_structured_data.py", ...extraArgs]);
    break;
  }
  case "bootstrap-special-types": {
    const python = requireExecutable(
      "python",
      "请先创建 `.venv` 并安装后端依赖，例如运行 `./scripts/dev.sh` 或手工执行 `pip install -e \"./apps/backend[dev]\"`。",
    );
    run(python, ["scripts/bootstrap_special_type_rules.py", ...extraArgs]);
    break;
  }
  case "bootstrap-pathways": {
    const python = requireExecutable(
      "python",
      "请先创建 `.venv` 并安装后端依赖，例如运行 `./scripts/dev.sh` 或手工执行 `pip install -e \"./apps/backend[dev]\"`。",
    );
    run(python, ["scripts/bootstrap_gaokao_pathways.py", ...extraArgs]);
    break;
  }
  case "gaokao-sources": {
    const python = requireExecutable(
      "python",
      "请先创建 `.venv` 并安装后端依赖，例如运行 `./scripts/dev.sh` 或手工执行 `pip install -e \"./apps/backend[dev]\"`。",
    );
    run(python, ["scripts/manage_gaokao_sources.py", ...extraArgs]);
    break;
  }
  case "gaokao-import-official": {
    const python = requireExecutable(
      "python",
      "请先创建 `.venv` 并安装后端依赖，例如运行 `./scripts/dev.sh` 或手工执行 `pip install -e \"./apps/backend[dev]\"`。",
    );
    run(python, ["scripts/import_gaokao_official.py", ...extraArgs]);
    break;
  }
  case "gaokao-import-shandong-core": {
    const python = requireExecutable(
      "python",
      "请先创建 `.venv` 并安装后端依赖，例如运行 `./scripts/dev.sh` 或手工执行 `pip install -e \"./apps/backend[dev]\"`。",
    );
    run(python, ["scripts/import_shandong_gaokao_core_data.py", ...extraArgs]);
    break;
  }
  case "data-health": {
    const python = requireExecutable(
      "python",
      "请先创建 `.venv` 并安装后端依赖，例如运行 `./scripts/dev.sh` 或手工执行 `pip install -e \"./apps/backend[dev]\"`。",
    );
    run(python, ["scripts/check_data_health.py", ...extraArgs]);
    break;
  }
  case "p0-check": {
    const python = requireExecutable(
      "python",
      "请先创建 `.venv` 并安装后端依赖，例如运行 `./scripts/dev.sh` 或手工执行 `pip install -e \"./apps/backend[dev]\"`。",
    );
    run(python, ["scripts/p0_delivery_check.py", ...extraArgs]);
    break;
  }
  case "test": {
    const pytest = requireExecutable(
      "pytest",
      "请先安装后端开发依赖，例如执行 `pip install -e \"./apps/backend[dev]\"`。",
    );
    run(pytest, extraArgs.length ? extraArgs : ["apps/backend/tests"]);
    break;
  }
  default:
    console.error(`不支持的命令: ${command}`);
    printUsage();
    process.exit(1);
}
