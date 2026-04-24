# 仓库审计与状态锁定（2026-04-24）

- 执行窗口：窗口 0
- 文档来源：按 `docs/Codex-App-基于仓库的后续开发执行文档-v3.md` 补齐指定 dated 审计文件
- 去重说明：已有窗口 0 已生成 `docs/repo-audit.md`、`docs/mac-dev-setup.md`、`docs/development-roadmap.md`；本文不重复重写那些公共文档，只把 v3 指定的审计要点按当前仓库真实状态锁定下来

## 1. 当前技术栈

### 前端

- Vue 3、TypeScript、Vite
- Element Plus、Pinia、Vue Router、ECharts
- ESLint、Vitest、Playwright
- 主要目录：`apps/frontend`

### 后端

- Python 3.11+、FastAPI
- SQLAlchemy 2.x、Pydantic 2、Alembic
- SQLite、pandas、openpyxl
- pytest、httpx
- 主要目录：`apps/backend`

### 桌面端

- Electron 桌面壳
- 后端独立二进制打包链
- 主要目录：`apps/desktop`

### 数据库与本地文件

- 应用主库：`data/app.db`
- 高考 handoff / fallback 来源：`data/local_edu_tool/local_edu.sqlite3`
- 高考 raw 表已并入主库后，应用优先走单库；handoff 库保留为同步来源和 fallback
- 备份、上传、模板、导出、日志目录位于 `data/`

## 2. 当前目录结构

| 路径 | 当前职责 |
| --- | --- |
| `apps/backend/app/api/routes` | FastAPI 路由，覆盖 dashboard、base_data、students、teachers、exams、analytics、workload、evaluation、reports、recommendations、gaokao、system 等入口 |
| `apps/backend/app/models` | SQLAlchemy 模型 |
| `apps/backend/app/schemas` | Pydantic schema |
| `apps/backend/app/services` | 业务服务；推荐、评教、工作量等已拆出多个私有 helper/facade |
| `apps/backend/app/importers` | Excel / 数据导入逻辑 |
| `apps/backend/app/exporters` | 报表、推荐、工作量等导出逻辑 |
| `apps/backend/app/utils` | 数据健康、并库、物化等本地工具函数 |
| `apps/frontend/src/pages` | 主页面和打印页 |
| `apps/frontend/src/components` | analytics、evaluation、exams、recommendations、reports、workload 等业务组件 |
| `apps/frontend/src/api` | 前端 API 客户端 |
| `apps/frontend/src/router` | 前端路由 |
| `apps/desktop` | Electron 主进程、开发/准备/打包脚本 |
| `scripts` | 根级启动、后端命令包装、数据健康、P0 验收、并库、物化等脚本 |
| `tests/e2e` | Playwright 跨端流程和固定 Excel fixture |
| `memory-bank` | 当前上下文、进展、决策、交接 |
| `.rulesync` | `AGENTS.md` 的规则来源 |

## 3. 后端模块结构

当前后端不是早期单文件状态，已形成分层：

- 路由层：`apps/backend/app/api/routes/*.py`
- 服务层 facade：`analytics.py`、`base_data.py`、`students.py`、`teachers.py`、`exams.py`、`workload.py`、`evaluation.py`、`recommendations.py`、`reports.py`、`gaokao.py`、`system.py`
- 推荐服务已细分到：
  - `_recommendations_generation.py`
  - `_recommendations_workbench.py`
  - `_recommendations_result_builder.py`
  - `_recommendations_rules.py`
  - `_recommendations_special_type_rules.py`
  - `_recommendations_fallback_priority.py`
  - `_recommendations_score_lines.py`
  - `_recommendations_employment.py`
  - `_recommendations_history.py`
  - `_recommendations_drafts.py`
- 评教服务已细分到：
  - `_evaluation_templates.py`
  - `_evaluation_batches.py`
  - `_evaluation_batch_stats.py`
  - `_evaluation_adviser_quant.py`
- 工作量计算已拆到 `_workload_calculation.py`
- 高考数据健康与结构化链路已落到 `apps/backend/app/utils/data_health.py`、`gaokao_sync.py`、`gaokao_materialize.py`

## 4. 前端页面结构

主页面：

- `DashboardPage.vue`
- `BaseDataPage.vue`
- `StudentsPage.vue`、`StudentDetailPage.vue`
- `TeachersPage.vue`、`TeacherDetailPage.vue`
- `ExamsPage.vue`
- `AnalyticsPage.vue`
- `TimetableWorkloadPage.vue`
- `GrowthArchivePage.vue`
- `EvaluationQuantPage.vue`
- `RecommendationsPage.vue`
- `GaokaoDataPage.vue`
- `ReportsPage.vue`
- `SystemToolsPage.vue`

打印 / 预览页面：

- `RecommendationPrintPage.vue`
- `VolunteerDraftPrintPage.vue`
- `GrowthSummaryPrintPage.vue`
- `StudentAnalysisPrintPage.vue`
- `ClassAnalysisPrintPage.vue`
- `GradeSummaryPrintPage.vue`
- `TeacherAnalysisPrintPage.vue`
- `WorkloadPrintPage.vue`
- `EvaluationSummaryPrintPage.vue`
- `AdviserQuantPrintPage.vue`

高复杂业务已经按组件目录拆分，不应再把逻辑塞回页面主文件：

- `components/recommendations`
- `components/evaluation`
- `components/workload`
- `components/analytics`
- `components/reports`

## 5. 桌面端结构

- `apps/desktop/main.cjs`：Electron 主进程
- `apps/desktop/scripts/dev.cjs`：桌面开发入口
- `apps/desktop/scripts/prepare.cjs`：桌面打包准备
- `apps/desktop/scripts/dist.cjs`：桌面打包
- `apps/desktop/package.json`：桌面端脚本与依赖

当前已有 macOS / Windows 打包脚本入口，但窗口 0 本轮不重新做 Windows 实机验收。

## 6. 数据库、Alembic、seed、migration 结构

迁移文件位于 `apps/backend/alembic/versions`，当前已到：

- `20260424_0015_special_type_rule_schema.py`

关键迁移阶段：

- `0001-0007`：基础教务、考试成绩、工作量、档案报表、推荐、评教、附件
- `0008-0013`：高考志愿、志愿草稿、就业方向、职业意向、Stage B 分数规则、生源地
- `0014`：Stage B 赋分规则与选科字典
- `0015`：特殊类型规则字典

当前数据库操作规则：

- 不直接手工改 `data/app.db` 表结构，结构变更必须走 Alembic
- 会改主库的脚本包括 `backend:merge-handoff`、`backend:materialize-gaokao`、`backend:bootstrap-special-types`
- 补数据、并库、物化前后应运行 `npm run backend:data-health` 或 `npm run backend:data-health -- --json`
- P0 交付验收用 `npm run backend:p0-check`

## 7. 已完成模块

不要从零重复开发以下能力：

- monorepo、FastAPI、Vue、SQLite、Alembic 基础工程
- 基础数据、学生、教师、任教关系
- 考试管理、成绩导入、成绩分析
- 课表导入、映射修正、工作量规则、工作量计算
- 成长档案、评教模板、评教批次、班主任量化
- 报表中心、打印预览、Excel 导出
- 推荐中心、高考志愿工作台、志愿草稿、推荐历史、策略模板
- 高考数据只读驾驶舱、山东覆盖矩阵、数据健康接口
- 特殊类型规则字典、赋分规则、选科字典只读核对入口
- P0 数据健康检查、备份恢复演练、恢复后接口检查
- Electron 桌面壳和打包入口
- ESLint、Vitest、pytest、Playwright 检查体系

## 8. 半完成模块

- 山东数据底座：普通类结果较完整，但招生计划年份、一分一段、省控线、政策参考和章程复核仍有缺口
- 特殊类型推荐：已有安全初筛和规则字典，但缺专门录取结果，不能作为录取把握
- 规则管理：已有查看和 bootstrap，完整编辑维护还没收齐
- 高考数据工作台：只读审计已可用，低风险补数据 / 冲突处理 / 待审处理仍主要依赖命令或后续窗口
- Mac 普通用户启动说明：已有 `docs/mac-dev-setup.md` 和双击脚本，下一窗口仍应复核“从零安装到启动”
- Windows 交付：脚本和打包目标存在，但不是当前主开发阵地，交付前需单独验收

## 9. 明显风险点

1. 多窗口重复修改公共文件：`README.md`、`AGENTS.md`、`.rulesync/rules/overview.md`、`package.json`、`.env.example`
2. 数据库写入风险：`data/app.db`、Alembic 迁移、并库、物化、bootstrap 必须串行
3. 推荐主链高风险：`_recommendations_generation.py`、`_recommendations_workbench.py`、`RecommendationsPage.vue`
4. 高考数据页高冲突：`gaokao.py`、`GaokaoDataPage.vue`
5. 特殊类型数据缺口不能被页面文案包装成录取概率
6. Playwright 主流程前置容易影响多条 E2E，用例 helper 变更必须谨慎
7. `apps/desktop/node_modules` 当前存在于本地目录中，不应把依赖目录当成需要维护的源码

## 10. AGENTS.md 来源维护方式

- `rulesync.jsonc` 当前配置：
  - `targets`: `codexcli`
  - `features`: `rules`
  - `baseDirs`: `.`
- 当前项目规则来源文件：`.rulesync/rules/overview.md`
- `AGENTS.md` 是 rulesync 生成结果；后续如需改 agent 规则，应先改 `.rulesync/rules/overview.md`，再按 rulesync 流程同步，不要直接手改生成结果
- 本轮窗口 0 补缺没有继续修改 `AGENTS.md`

## 11. 当前最应该继续开发的 5 个方向

1. Mac 普通用户启动收口：复核 `npm run dev`、`start-local-edu.command`、从零安装、失败提示和用户文档
2. 山东数据底座补齐：2021-2023 招生计划、一分一段 2020-2023、省控线 2020-2023、政策参考、章程复核
3. 高考数据健康和审计深化：让补数据前后差异、重复、冲突、待审能更直观看到
4. 推荐 / 志愿山东真实样例验收：普通类完整走通，特殊类型继续保持初筛性质
5. 交付前质量门：最终窗口集中跑 `npm run check:all`、`npm run backend:p0-check -- --json`，并核对文档、备份、启动、恢复

## 12. 本轮窗口 0 验证结果

按 v3 文档要求，本轮补缺后已运行：

| 命令 | 结果 |
| --- | --- |
| `npm run backend:test` | 通过，`66 passed` |
| `npm run frontend:lint` | 通过 |
| `npm run frontend:test` | 首次发现 `recommendations-helpers.test.ts` 仍期待广东默认规则；已按当前山东交付口径修正后重跑通过，`20 passed / 114 passed` |
| `npm run frontend:build` | 通过 |
| `npm run backend:data-health` | 通过，当前摘要仍为核心表缺失 `0`、空表 `0`、需关注表 `2`、P0 缺口 `6` |
| `npm run backend:p0-check -- --json` | 通过，`ok: true`，备份包 `data/backups/p0_delivery_backup_20260424_155211.zip` |
| `git diff --check` | 通过 |

本轮只修正了一处前端测试期望，未修改业务逻辑。
