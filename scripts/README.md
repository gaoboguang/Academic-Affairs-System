# 脚本导航

根目录脚本分成两类：优先从 `npm run ...` 统一入口调用的脚本，以及少数需要直接执行的辅助脚本。

## 优先使用的统一入口

- 双击 [`../start-local-edu.command`](../start-local-edu.command)
  macOS 下的图形化启动入口；会在仓库根目录执行 `npm run start:local`，把前后端拉到后台运行，适合日常直接点开用。普通用户步骤见 [`../docs/mac-user-startup-guide.md`](../docs/mac-user-startup-guide.md)。
- `npm run start:local`
  后台启动或复用前后端服务，启动完成后可关闭终端；日志写入 `data/logs/local-services/`。
- `npm run stop:local`
  停止由 `start:local` 后台启动的服务。
- `npm run dev`
  同时拉起前后端开发服务，内部调用 `scripts/dev-local.cjs`；这是开发调试模式，终端关闭后前端服务会停止。
- `npm run clean:local`
  清理仓库内明确可再生的本地噪音，如 `.DS_Store`、`__pycache__`、`.pytest_cache`、`*.egg-info`、`test-results`。
- `npm run clean:slim`
  在 `clean:local` 基础上，额外清理可再生构建产物，如 `apps/frontend/dist`、`apps/desktop/.dist`、`dist/desktop`。
- `npm run backend:dev`
- `npm run backend:migrate`
- `npm run backend:merge-handoff`
- `npm run backend:materialize-gaokao`
- `npm run backend:bootstrap-special-types -- --year 2025 --year 2026`
- `npm run backend:gaokao-sources -- --json`
- `npm run backend:gaokao-import-official -- --source-document-id <id> --file data/imports/gaokao/official/<year>/<file>`
- `npm run backend:gaokao-import-shandong-core -- --json`
- `npm run backend:data-health`
- `npm run backend:p0-check`
- `npm run backend:init-demo`
- `npm run backend:test`
- `npm run check`
  常规质量门禁：后端全量测试、前端静态检查、前端单测和前端构建。内部由 `scripts/quality-gate.cjs` 分阶段输出，失败时会提示下一步。
- `npm run check:e2e`
  跨端质量门禁：运行 `tests/e2e/dashboard-smoke.spec.ts`。
- `npm run check:all`
  完整质量门禁：先运行 `check`，再运行 `check:e2e`。

如果只是日常开发，优先用上面这些入口，不要先记具体脚本名。

## 脚本职责

- [`../start-local-edu.command`](../start-local-edu.command)
  macOS 双击启动器；会先检查本机 `5173 / 8000` 是否已是可用服务，未启动时再执行 `npm run start:local`，启动后服务留在后台。
- [`start-local-services.cjs`](./start-local-services.cjs)
  本地后台启动器，负责复用或后台启动前后端服务，并把日志写入 `data/logs/local-services/`。
- [`stop-local-services.cjs`](./stop-local-services.cjs)
  根据 `data/logs/local-services/*.pid.json` 停止后台启动器创建的服务。
- [`backend-cli.cjs`](./backend-cli.cjs)
  后端统一命令入口，负责迁移、初始化、测试、开发启动。
- [`check_data_health.py`](./check_data_health.py)
  检查 `data/app.db` 的 P0 数据健康状态，输出核心表数量、山东年份覆盖、考生类型覆盖和缺口摘要；支持 `--json`。
- [`p0_delivery_check.py`](./p0_delivery_check.py)
  执行 P0 本地交付验收：数据健康、SQLite 完整性、备份包结构、临时恢复、恢复库健康检查和恢复后应用启动。
- [`quality-gate.cjs`](./quality-gate.cjs)
  把 `check / check:e2e / check:all` 包装成分阶段质量门禁，保留原有检查强度，同时让失败原因和下一步更容易读懂。
- [`dev-local.cjs`](./dev-local.cjs)
  根目录统一开发启动器，负责前后端一起启动和端口预检；直接调用时也会从仓库根目录启动子命令。
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
- [`manage_gaokao_sources.py`](./manage_gaokao_sources.py)
  登记山东高考官方来源文档，准备 `data/imports/gaokao/official/`、`manual/`、错误报告和 raw 快照目录；后续 B1/B2 导入器应先复用这里的 `source_document_id`。
- [`import_gaokao_official.py`](./import_gaokao_official.py)
  登记人工下载的官方文件，写入文件路径、SHA256 和导入批次；B1 后可加 `--parse` 解析单个文件，或加 `--b1-shandong-core --no-download` 批量导入 2023-2025 山东普通类投档表、一分一段和省控线。
- [`import_shandong_gaokao_core_data.py`](./import_shandong_gaokao_core_data.py)
  B1 官方核心数据导入器；复用 A1 的来源文档，自动下载或读取 `data/imports/gaokao/official/{year}/` 下的文件，解析 2023-2025 山东普通类投档表、一分一段和省控线，并生成 `docs/gaokao-shandong-2023-2025-coverage.md`。
- [`run_e2e_backend.py`](./run_e2e_backend.py)
  给 Playwright / E2E 提供临时后端服务。
- [`backup.ps1`](./backup.ps1)
  Windows 下的备份辅助脚本。

## 什么时候直接跑脚本

- 需要排查 `npm run dev` 的行为时，再直接看 `dev-local.cjs`。
- 需要只处理后端某个动作时，再看 `backend-cli.cjs`。
- 需要跨平台初始化细节时，再看 `dev.sh` / `dev.ps1`。
- 需要给下一位开发窗口交接启动和验证步骤时，看 `docs/mac-developer-checklist.md`。

## 不要把这些当源码主线

- `scripts/__pycache__/` 是本地运行产物，不是需要维护的源码。
- 新增脚本前，先判断能不能挂到现有 `backend-cli.cjs` 或根目录 `package.json`，避免入口继续分散。
