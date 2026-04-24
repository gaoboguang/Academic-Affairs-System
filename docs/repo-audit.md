# 仓库审计报告

- 审计日期：2026-04-24
- 执行窗口：窗口 0，仓库审计与总控规划
- 仓库路径：`/Users/gao/local-edu-tool`
- 当前分支：`codex/00-audit-roadmap`

## 1. 真实技术栈

### 前端

- 框架：Vue 3、TypeScript、Vue Router、Pinia
- UI 与图表：Element Plus、`@element-plus/icons-vue`、ECharts
- 构建：Vite、`vue-tsc`
- 检查与测试：ESLint、Vitest、Playwright
- 目录：`apps/frontend`

### 后端

- 框架：FastAPI
- 数据访问：SQLAlchemy 2.x，Pydantic 2，`pydantic-settings`
- 数据处理：pandas、openpyxl
- 迁移：Alembic
- 测试：pytest、httpx
- 目录：`apps/backend`

### 数据库和本地存储

- 主库：SQLite，默认 `data/app.db`
- 迁移目录：`apps/backend/alembic/versions`
- 当前迁移版本：`20260424_0015`
- 高考原始表：`gaokao_*`、`score_rank_segment` 等已经并入 `data/app.db`
- 高考 handoff/fallback 入口：`data/local_edu_tool/local_edu.sqlite3`
- 本地文件：`data/uploads`、`data/backups`、`data/templates`、`data/exports`、`data/logs`

### 包管理和运行入口

- 根包管理器：npm workspace
- workspaces：`apps/frontend`、`apps/desktop`
- 根级常用命令：
  - `npm run dev`
  - `npm run backend:migrate`
  - `npm run backend:data-health`
  - `npm run backend:p0-check`
  - `npm run backend:test`
  - `npm run frontend:lint`
  - `npm run frontend:test`
  - `npm run frontend:build`
  - `npm run check`
  - `npm run check:e2e`
  - `npm run check:all`

## 2. 当前目录结构

| 路径 | 职责 |
| --- | --- |
| `apps/frontend` | Vue 前端应用、页面、组件、前端单测 |
| `apps/backend` | FastAPI 后端、SQLAlchemy 模型、服务、路由、迁移、后端测试 |
| `apps/desktop` | Electron 桌面壳和桌面打包脚本 |
| `data` | 本地运行数据库、上传、备份、模板、导出、日志 |
| `docs` | 规格、审计、运行、路线图、交付计划和历史 bundle |
| `handoffs` | 外部数据库接管包与审计材料 |
| `scripts` | 启动、迁移包装、数据健康、并库、物化、验收脚本 |
| `tests/e2e` | Playwright 跨端流程 |
| `memory-bank` | 当前上下文、进展、决策和交接 |
| `.rulesync` | `AGENTS.md` 的规则来源 |

## 3. 当前功能状态

### 已完成或基本可用

- 基础数据：学年、学期、年级、班级、科目、字典、配置项。
- 学生中心：学生档案、导入导出、附件、成长档案、职业意向。
- 教师中心：教师档案、职称历史、任教关系、教师画像。
- 考试成绩：考试管理、科目配置、成绩导入、成绩快照。
- 分析中心：学生、班级、年级、教师分析，以及多学年全景看板。
- 课表工作量：课表导入、映射修正、规则配置、工作量计算、导出。
- 评教量化：评教模板、批次导入、教师趋势、班主任量化。
- 报表中心：核心分析、工作量、评教、成长档案、推荐、志愿草稿导出和打印预览。
- 系统工具：模板下载、文件上传、备份恢复、数据修复、审计日志。
- 高考数据页：只读总览、数据健康、山东覆盖矩阵、导入审计、审阅摘要、院校证据、山东监控。
- 高考志愿：院校库、专业库、招生计划、录取库、省份规则、赋分规则、选科字典、特殊类型规则、志愿工作台、草稿、打印和导出。
- P0 安全底座：数据健康检查、SQLite 完整性检查、备份包生成、恢复演练、恢复库接口检查。
- 桌面壳：已有 Electron 打包入口和 macOS/Windows 产物脚本。

### 半完成或需要继续打磨

- 山东数据底座：普通类录取结果覆盖较好，但招生计划年份、一分一段、省控线、政策参考、章程复核仍有缺口。
- 特殊类型推荐：已有省控线资格参考、计划清单初筛和规则字典，但缺完整专门录取结果，不能当作录取把握。
- 规则管理：`province_volunteer_rule`、`special_type_rule`、`province_score_transform_rule`、`subject_requirement_dict` 已有核对和 bootstrap 入口，完整编辑维护还没收齐。
- 高考数据工作台：当前以只读驾驶舱和审计摘要为主，补数据、冲突处理、物化触发还主要依赖命令。
- Windows 交付：脚本和打包配置存在，但本轮窗口 0 未重新执行 Windows 环境验收。
- 桌面分发：macOS/Windows 打包入口存在，签名、安装体验和普通用户交付说明还需要收尾。

### 未完成或暂不属于当前 P0

- 多用户登录、角色和权限：当前产品定位仍是本地单用户，尚未落地完整账号体系。
- 公网部署、在线协同、手机端、小程序、消息通知：规格文档明确当前不做。
- 全国多省份交付版：近期交付焦点是山东生源地，全国高校在山东招生数据。
- 完整数据编辑后台：部分规则和高考数据仍以只读核对、命令导入和审计为主。

## 4. 当前启动和验证状态

### 本轮已确认

- 后端当前在本机 `127.0.0.1:8000` 有健康响应：`/api/system/health` 返回 HTTP `200`。
- 前端 `127.0.0.1:5173` 在执行 `npm run dev` 后可用，返回 HTTP `200`；本次 `npm run dev` 检测到前后端都已在运行并直接复用。
- `npm run backend:data-health -- --json` 可读取真实 `data/app.db`，当前摘要为：核心表缺失 `0` 个，空表 `0` 个，需关注表 `2` 个，P0 缺口 `6` 条。
- 当前主库 schema 版本为 `20260424_0015`。
- `npm run backend:p0-check -- --json` 返回 `ok: true`，最新备份包为 `data/backups/p0_delivery_backup_20260424_153049.zip`。
- `npm run backend:test -- apps/backend/tests/test_data_health.py apps/backend/tests/test_gaokao_api.py -q` 通过，结果 `15 passed`。
- `npm run frontend:build` 通过。
- `git diff --check` 通过。

### 当前真实数据健康摘要

| 项目 | 当前状态 |
| --- | --- |
| 应用侧院校 | `3460` 条 |
| 应用侧专业 | `13960` 条 |
| 院校专业关联 | `60767` 条 |
| 应用侧招生计划 | `6341` 条 |
| 应用侧录取结果 | `170389` 条 |
| 省份志愿规则 | `162` 条 |
| 赋分/成绩转换规则 | `876` 条 |
| 选科要求字典 | `584` 条 |
| 特殊类型规则 | `62` 条 |
| 一分一段 | `7492` 条 |
| raw 招生计划 | `6895` 条 |
| raw 录取结果 | `178343` 条 |
| raw 省控线/批次线 | `26` 条 |
| raw 政策参考 | `4` 条，偏少 |
| raw 招生章程限制链 | `2052` 条，其中 `1748` 条待人工复核 |

### 当前主要缺口

1. 特殊类型已有招生计划，但缺专门录取结果。
2. 山东招生计划 2024 年数量偏少，且 2021-2023 年缺失。
3. 一分一段缺 2020-2023 年。
4. 省控线/批次线缺 2020-2023 年。
5. 政策参考仅 4 条，交付前不足以支撑完整边界说明。
6. 招生章程限制链仍有 1748 条待人工复核。

## 5. 后续开发建议

### 推荐顺序

1. 窗口 1：按 `docs/mac-dev-setup.md` 复核 Mac 从零启动、README、`.env.example` 和启动脚本。
2. 窗口 2：继续数据模型与高考数据底座，优先补山东招生计划、一分一段、省控线、政策参考和章程复核审计。
3. 窗口 3：整理前端导航、规则核对入口和高考数据工作台，只做已有数据的清晰展示与低风险维护。
4. 窗口 9：在基础稳定后做测试、验收、文档和交付手册。
5. 窗口 10：最后做代码审查、冲突检查和合并建议。

### 适合并行

- Mac 启动文档与环境复核。
- 只读规则核对页和 UI 空态说明。
- 后端数据健康/审计命令增强。
- 测试文档、用户操作手册、验收清单。

### 必须串行或谨慎串行

- Alembic 迁移和 SQLAlchemy model 改动。
- `data/app.db` 真实写库、并库、物化、恢复。
- `apps/backend/app/services/_recommendations_generation.py`、`_recommendations_workbench.py`、`gaokao.py`。
- `apps/frontend/src/pages/RecommendationsPage.vue`、`GaokaoDataPage.vue`。
- `tests/e2e/dashboard-smoke.spec.ts` 的共享前置和主链路。
- `package.json`、`AGENTS.md`、`README.md` 这类跨窗口公共入口。

### 窗口数量建议

- 窗口 0 完成后，第二批最多同时开 `2-3` 个窗口。
- 不建议超过 `3` 个窗口并行修改同一仓库；当前项目公共文件较多，过多窗口容易互相覆盖。
- 如果有窗口要改迁移、主库写入或核心推荐服务，其它窗口应避开数据库和推荐主链。
