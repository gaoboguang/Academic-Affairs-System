# 脚本导航

根目录脚本分成两类：优先从 `npm run ...` 统一入口调用的脚本，以及少数需要直接执行的辅助脚本。

## 优先使用的统一入口

- 双击 [`../start-local-edu.command`](../start-local-edu.command)
  macOS 下的图形化启动入口；会在仓库根目录执行 `npm run dev`，适合日常直接点开用。
- `npm run dev`
  同时拉起前后端开发服务，内部调用 `scripts/dev-local.cjs`。
- `npm run clean:local`
  清理仓库内明确可再生的本地噪音，如 `.DS_Store`、`__pycache__`、`.pytest_cache`、`*.egg-info`、`test-results`。
- `npm run clean:slim`
  在 `clean:local` 基础上，额外清理可再生构建产物，如 `apps/frontend/dist`、`apps/desktop/.dist`、`dist/desktop`。
- `npm run backend:dev`
- `npm run backend:migrate`
- `npm run backend:merge-handoff`
- `npm run backend:materialize-gaokao`
- `npm run backend:bootstrap-special-types -- --year 2025 --year 2026`
- `npm run backend:data-health`
- `npm run backend:p0-check`
- `npm run backend:init-demo`
- `npm run backend:test`

如果只是日常开发，优先用上面这些入口，不要先记具体脚本名。

## 脚本职责

- [`../start-local-edu.command`](../start-local-edu.command)
  macOS 双击启动器；会先检查本机 `5173 / 8000` 是否已是可用服务，未启动时再执行 `npm run dev`。
- [`backend-cli.cjs`](./backend-cli.cjs)
  后端统一命令入口，负责迁移、初始化、测试、开发启动。
- [`check_data_health.py`](./check_data_health.py)
  检查 `data/app.db` 的 P0 数据健康状态，输出核心表数量、山东年份覆盖、考生类型覆盖和缺口摘要；支持 `--json`。
- [`p0_delivery_check.py`](./p0_delivery_check.py)
  执行 P0 本地交付验收：数据健康、SQLite 完整性、备份包结构、临时恢复、恢复库健康检查和恢复后应用启动。
- [`dev-local.cjs`](./dev-local.cjs)
  根目录统一开发启动器，负责前后端一起启动和端口预检。
- [`dev.sh`](./dev.sh)
  macOS / Linux 的一键初始化与开发脚本。
- [`dev.ps1`](./dev.ps1)
  Windows PowerShell 的一键初始化与开发脚本。
- [`init_data.py`](./init_data.py)
  初始化模板和演示数据。
- [`merge_handoff_gaokao_db.py`](./merge_handoff_gaokao_db.py)
  把 handoff 包内 `gaokao_*` 原始表、导入批次和分段表并入 `data/app.db`，执行前会自动备份主库，并输出执行前后的健康摘要。
- [`materialize_gaokao_structured_data.py`](./materialize_gaokao_structured_data.py)
  把已嵌入 `data/app.db` 的 raw 高考表整理到项目业务表；当前已覆盖普通类录取结果，以及普通类、春季高考、艺术类、单独招生、综合评价招生、体育类招生计划。执行前会自动备份主库，并输出执行前后的健康摘要。
- [`bootstrap_special_type_rules.py`](./bootstrap_special_type_rules.py)
  装载山东特殊类型规则字典；当前用于春考、综评、单招、艺术、体育 fallback 的细分类别、关键词、核对清单和初筛优先级。执行前默认备份主库，并输出执行前后的健康摘要。
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
