# 脚本导航

根目录脚本分成两类：优先从 `npm run ...` 统一入口调用的脚本，以及少数需要直接执行的辅助脚本。

## 优先使用的统一入口

- `npm run dev`
  同时拉起前后端开发服务，内部调用 `scripts/dev-local.cjs`。
- `npm run clean:local`
  清理仓库内明确可再生的本地噪音，如 `.DS_Store`、`__pycache__`、`.pytest_cache`、`*.egg-info`、`test-results`。
- `npm run clean:slim`
  在 `clean:local` 基础上，额外清理可再生构建产物，如 `apps/frontend/dist`、`apps/desktop/.dist`、`dist/desktop`。
- `npm run backend:dev`
- `npm run backend:migrate`
- `npm run backend:init-demo`
- `npm run backend:test`

如果只是日常开发，优先用上面这些入口，不要先记具体脚本名。

## 脚本职责

- [`backend-cli.cjs`](./backend-cli.cjs)
  后端统一命令入口，负责迁移、初始化、测试、开发启动。
- [`dev-local.cjs`](./dev-local.cjs)
  根目录统一开发启动器，负责前后端一起启动和端口预检。
- [`dev.sh`](./dev.sh)
  macOS / Linux 的一键初始化与开发脚本。
- [`dev.ps1`](./dev.ps1)
  Windows PowerShell 的一键初始化与开发脚本。
- [`init_data.py`](./init_data.py)
  初始化模板和演示数据。
- [`run_e2e_backend.py`](./run_e2e_backend.py)
  给 Playwright / E2E 提供临时后端服务。
- [`backup.ps1`](./backup.ps1)
  Windows 下的备份辅助脚本。

## 什么时候直接跑脚本

- 需要排查 `npm run dev` 的行为时，再直接看 `dev-local.cjs`。
- 需要只处理后端某个动作时，再看 `backend-cli.cjs`。
- 需要跨平台初始化细节时，再看 `dev.sh` / `dev.ps1`。

## 不要把这些当源码主线

- `scripts/__pycache__/` 是本地运行产物，不是需要维护的源码。
- 新增脚本前，先判断能不能挂到现有 `backend-cli.cjs` 或根目录 `package.json`，避免入口继续分散。
