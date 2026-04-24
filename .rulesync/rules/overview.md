---
root: true
targets: ["codexcli"]
description: "Local Edu Tool project overview, constraints, and memory workflow"
globs: ["**/*"]
---

# 本地教务工具 Agent Guide

## 开始任何工作前

1. 阅读 `docs/local_edu_tool_dev_spec.md`。
2. 阅读 `memory-bank/project-context.md`、`memory-bank/active-context.md`、`memory-bank/handoff.md`。
3. 如果任务涉及结构调整、重构或工程化，补充阅读 `memory-bank/decision-log.md` 与 `docs/development_recommendations_2026-04-05.md`。

## 项目定位

- 本项目是本地、单用户、离线优先的高中教务决策台。
- 默认运行在 `127.0.0.1`，不依赖必须联网才能运行的在线服务。
- 数据库存储使用 SQLite。
- 所有页面默认中文。
- 关键目标环境优先兼容 Windows。

## 工程结构

- 前端位于 `apps/frontend`。
- 后端位于 `apps/backend`。
- 桌面壳位于 `apps/desktop`。
- 本地运行数据位于 `data/`。
- 文档位于 `docs/`。
- 后端测试位于 `apps/backend/tests`。
- 前端单测位于 `apps/frontend/tests`。
- 跨端 E2E 位于 `tests/e2e`。

## 当前技术栈

- 根目录：npm workspace。
- 前端：Vue 3、TypeScript、Vite、Element Plus、Pinia、Vue Router、ECharts。
- 后端：Python 3.11+、FastAPI、SQLAlchemy 2.x、Pydantic 2、Alembic、pandas、openpyxl。
- 数据库：SQLite，主库默认 `data/app.db`。
- 测试：pytest、ESLint、Vitest、Playwright。
- 桌面：Electron + 后端独立二进制打包链。

## 推荐命令

- 一键开发启动：`npm run dev`
- 后端迁移：`npm run backend:migrate`
- 后端开发服务：`npm run backend:dev`
- 后端测试：`npm run backend:test`
- 高考数据健康检查：`npm run backend:data-health`
- P0 交付验收：`npm run backend:p0-check`
- 前端静态检查：`npm run frontend:lint`
- 前端单测：`npm run frontend:test`
- 前端构建：`npm run frontend:build`
- 跨端 E2E：`npm run check:e2e`
- 统一检查：`npm run check`、`npm run check:all`

## 数据库与数据安全

- 不要在没有 Alembic 迁移的情况下直接修改应用表结构。
- `data/app.db` 是当前应用主库；高考 `gaokao_*` raw 表已并入主库。
- `data/local_edu_tool/local_edu.sqlite3` 只作为 handoff 同步来源和 fallback。
- 会改主库的命令包括 `backend:merge-handoff`、`backend:materialize-gaokao`、`backend:bootstrap-special-types`；执行前后必须保留备份和健康摘要。
- 高考特殊类型在缺少专门录取结果时只能做初筛，不得把省控线或计划清单包装成录取把握。

## 强制约束

- 附件文件不得直接存入数据库，只保存本地路径和元信息。
- 不要在没有迁移脚本的情况下直接改数据库结构。
- 不要把核心业务规则硬编码在前端页面中。
- 不要在没有测试保护的情况下重写推荐、量化、工作量、成绩分析等核心逻辑。
- 每次阶段性修改后，README 与相关说明应保持可用。

## 当前结构判断

- 仓库基础骨架可继续演进，不需要推倒重来。
- 当前主要风险不是目录混乱，而是复杂业务开始集中到少数超大文件。
- 前端高风险页面包括：
  - `apps/frontend/src/pages/RecommendationsPage.vue`
  - `apps/frontend/src/pages/EvaluationQuantPage.vue`
  - `apps/frontend/src/pages/TimetableWorkloadPage.vue`
- 后端高风险文件包括：
  - `apps/backend/app/services/evaluation.py`
  - `apps/backend/app/services/recommendations.py`
  - `apps/backend/app/services/students.py`

## 优先改造方向

1. 先拆一个前端超大页面，优先推荐中心页面。
2. 再拆一个后端超大 service，优先评教量化 service。
3. 然后统一测试目录说明与工程入口。
4. 避免同时大改前端、后端、测试布局和脚本系统。

## 多窗口开发注意事项

- 窗口 0 负责审计、路线图和公共文档；后续窗口先读 `docs/repo-audit.md`、`docs/mac-dev-setup.md`、`docs/development-roadmap.md`。
- 不要多个窗口同时修改 `package.json`、`README.md`、`AGENTS.md`、`.rulesync/rules/overview.md`。
- 不要多个窗口同时修改 Alembic 迁移、`apps/backend/app/models/recommendation.py` 或 `data/app.db`。
- 推荐页、高考数据页、推荐服务和 `tests/e2e/dashboard-smoke.spec.ts` 属于高冲突区域，改动前先确认其它窗口没有同时处理。
- 如果必须修改公共文件，在最终中文汇报中明确说明影响范围。

## 修改完成后的中文汇报格式

每次阶段性完成后，用中文说明：

1. 改了哪些文件。
2. 新增或修复了什么。
3. 为什么这样做。
4. 运行了哪些验证，结果是什么。
5. 还剩哪些风险或下一步。

## 记忆维护规则

- `memory-bank/project-context.md`：记录项目定位、技术栈、目录职责、长期约束。
- `memory-bank/active-context.md`：记录当前正在推进的重点、风险、临时约束。
- `memory-bank/progress.md`：记录已经完成的重要阶段和最近落地的工作。
- `memory-bank/decision-log.md`：记录影响后续开发的结构性决定。
- `memory-bank/handoff.md`：记录下一位 Codex 接手时最该先看的状态和下一步。

## 会话结束前

- 如果本次改动影响结构、流程、规则或接手成本，更新 `memory-bank/active-context.md`。
- 如果本次完成了明确阶段，更新 `memory-bank/progress.md`。
- 如果本次做了值得长期保留的决策，更新 `memory-bank/decision-log.md`。
- 始终更新 `memory-bank/handoff.md`，让下一次会话可以直接续做。
