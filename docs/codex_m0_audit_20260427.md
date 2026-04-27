# M0 仓库审计与基线锁定

- 审计日期：2026-04-27
- 审计窗口：M0
- 项目路径：`/Users/gao/local-edu-tool`
- 当前分支：`main`
- 当前 Git 状态：`main...origin/main`
- 本轮性质：只做审计文档和基线验证，不修改业务代码、不新增迁移、不写入 `data/app.db`

## 1. 已读取资料

按后续开发文档第 0 节和仓库规则，已读取：

- `AGENTS.md`
- `docs/local_edu_tool_dev_spec.md`
- `docs/README.md`
- `memory-bank/project-context.md`
- `memory-bank/active-context.md`
- `memory-bank/handoff.md`
- `memory-bank/progress.md`
- `memory-bank/decision-log.md`
- `/Users/gao/Desktop/本地教务工具项目全面检查汇报_2026-04-27.md`
- `/Users/gao/Downloads/本地教务工具后续开发文档_Codex执行版_基于项目报告重规划.md`
- `package.json`
- `apps/backend/pyproject.toml`
- `apps/backend/alembic.ini`
- `apps/frontend/package.json`
- `apps/desktop/package.json`

结论：本轮后续开发主线应从“继续堆数据库”转向真实试用、决策体验和交付稳定。当前 M0 只锁定真实状态，后续 M1 起再做功能改造。

## 2. 工作区与依赖基线

### Git 状态

审计开始时工作区已有未提交改动：

- `memory-bank/handoff.md`
- `memory-bank/progress.md`

这两处改动内容是 2026-04-27 项目全面检查记录，不是本轮业务代码变更；本轮后续只追加 M0 交接信息，不回滚已有内容。

### 根脚本

根目录为 npm workspace，包含 `apps/frontend` 和 `apps/desktop`。当前根脚本包括：

- 启动：`npm run start:local`、`npm run dev`、`npm run stop:local`
- 清理：`npm run clean:local`、`npm run clean:slim`
- 后端：`backend:dev`、`backend:migrate`、`backend:test`、`backend:data-health`、`backend:p0-check`
- 高考数据：`backend:merge-handoff`、`backend:materialize-gaokao`、`backend:bootstrap-special-types`、`backend:bootstrap-pathways`、`backend:gaokao-sources`、`backend:gaokao-import-official`、`backend:gaokao-import-shandong-core`
- 前端：`frontend:dev`、`frontend:lint`、`frontend:test`、`frontend:build`
- 桌面：`desktop:dev`、`desktop:prepare`、`desktop:dist`、`desktop:dist:mac`、`desktop:dist:win:dir`、`desktop:dist:win:nsis`
- 质量门禁：`npm run check`、`npm run check:e2e`、`npm run check:all`

### 依赖文件

- 后端依赖：`apps/backend/pyproject.toml`
  - Python `>=3.11`
  - FastAPI、SQLAlchemy、Alembic、Pydantic Settings、pandas、openpyxl、uvicorn、xlrd
  - dev 依赖含 pytest、httpx、pytest-cov
  - desktop 依赖含 pyinstaller
- 前端依赖：`apps/frontend/package.json`
  - Vue 3、Vite、TypeScript、Element Plus、Pinia、Vue Router、ECharts
  - ESLint、Vitest、vue-tsc
- 桌面依赖：`apps/desktop/package.json`
  - Electron `37.3.1`
  - electron-builder `26.0.12`

## 3. 数据与运行状态

当前主库：

- 数据库：`data/app.db`
- 大小：约 `525M`
- 仓库占用：约 `15G`
- `data/` 占用：约 `13G`
- Alembic 版本：`20260426_0019`
- SQLite 完整性：`ok`
- 表数量：`92`

关键教学业务数据：

| 数据项 | 当前数量 |
| --- | ---: |
| 学生 `student` | 806 |
| 教师 `teacher` | 2 |
| 考试 `exam` | 1 |
| 成绩记录 `score_record` | 0 |

判断：代码和数据结构可运行，但真实教学试用样本不足；后续 M2 应优先用真实或脱敏数据跑完整流程。

## 4. 当前实际前端页面

`apps/frontend/src/pages` 当前有 30 个页面文件。

主业务页面：

- `DashboardPage.vue`：工作台
- `BaseDataPage.vue`：基础数据
- `StudentsPage.vue`、`StudentDetailPage.vue`：学生中心与学生详情
- `GrowthArchivePage.vue`：成长档案
- `TeachersPage.vue`、`TeacherDetailPage.vue`：教师中心与教师详情
- `ExamsPage.vue`：考试成绩
- `AnalyticsPage.vue`：分析中心
- `ImportCenterPage.vue`：导入中心
- `GaokaoDataPage.vue`：高考数据看板
- `GaokaoPathwaysPage.vue`：升学方案
- `TimetableWorkloadPage.vue`：课表工作量
- `EvaluationQuantPage.vue`：评教与量化
- `RecommendationsPage.vue`：高考志愿 / 推荐中心
- `ReportsPage.vue`：报表中心
- `SystemToolsPage.vue`：系统设置

打印页：

- `RecommendationPrintPage.vue`
- `ShandongRecommendationPrintPage.vue`
- `GaokaoPathwayReportPrintPage.vue`
- `GaokaoDataCoveragePrintPage.vue`
- `StudentAnalysisPrintPage.vue`
- `ClassAnalysisPrintPage.vue`
- `GradeSummaryPrintPage.vue`
- `TeacherAnalysisPrintPage.vue`
- `WorkloadPrintPage.vue`
- `EvaluationSummaryPrintPage.vue`
- `AdviserQuantPrintPage.vue`
- `GrowthSummaryPrintPage.vue`
- `VolunteerDraftPrintPage.vue`

路由已确认位于 `apps/frontend/src/router/index.ts`，导航入口位于 `apps/frontend/src/layouts/navigation.ts`。

## 5. 当前实际后端 API

后端入口为 `apps/backend/app/main.py`，统一挂载 `api_router` 到 `/api`。

实际路由模块 14 个：

- `dashboard.py`：工作台摘要
- `base_data.py`：学年、学期、年级、班级、学科、字典、配置项
- `students.py`：学生 CRUD、导入导出、批量删除、批量调班、附件、职业偏好、调班历史
- `teachers.py`：教师 CRUD、导入导出、任教关系、教师档案、职称历史
- `archives.py`：成长档案、成长记录附件、成长摘要导出
- `exams.py`：考试、科目配置、成绩导入、成绩批次、重算
- `analytics.py`：学生、班级、年级、教师分析与全景对比
- `evaluation.py`：评教模板、评教导入、评教分析、班主任量化
- `gaokao.py`：高考数据总览、数据健康、升学路径、画像、路径评估、导入批次、审阅和证据
- `recommendations.py`：院校、专业、录取库、招生计划、省份规则、赋分规则、选科字典、特殊类型规则、预估分、山东冲稳保、志愿工作台、草稿、推荐生成、历史
- `reports.py`：报表导出、山东推荐报告、升学路径报告、导出记录下载
- `workload.py`：课表导入、课表批次、规则、附加工作量、计算、结果导出
- `system.py`：文件、备份恢复、审计日志、系统配置、模板、导入中心、数据修复
- `health.py`：系统健康和文件目录检查

按装饰器粗略统计，当前路由端点约 174 个；其中 `recommendations.py` 是最大路由模块，约 53 个端点。

## 6. 后端模型、服务、导入器、导出器

### 模型文件

`apps/backend/app/models` 当前包含：

- `base.py`
- `base_data.py`
- `student.py`
- `teacher.py`
- `exam.py`
- `archive.py`
- `workload.py`
- `evaluation.py`
- `recommendation.py`
- `gaokao_import.py`
- `system.py`

已确认存在的关键模型域：

- 学年学期、年级班级、学科、字典
- 学生、监护人、班级历史、批量调班批次和明细、附件、职业偏好
- 教师、职称历史、任教关系、班主任关系
- 考试、科目、成绩、分析相关表
- 成长档案、成长附件
- 课表、工作量规则、工作量结果
- 评教、班主任量化
- 院校、专业、录取记录、招生计划、推荐、志愿草稿、规则字典、特殊类型规则、就业映射
- 高考来源文档和导入批次
- 系统配置、审计、备份、报表导出

### 服务文件

`apps/backend/app/services` 当前有 46 个服务文件加 `__init__.py`。复杂业务已拆出若干私有 helper：

- 评教：`_evaluation_*`
- 推荐：`_recommendations_*`
- 工作量：`_workload_calculation.py`
- 高考：`gaokao.py`、`gaokao_imports.py`、`gaokao_official_importers.py`、`gaokao_pathways.py`
- 其他主服务：`dashboard.py`、`base_data.py`、`students.py`、`teachers.py`、`exams.py`、`analytics.py`、`archive.py`、`reports.py`、`system.py`、`workload.py`

### 导入器

`apps/backend/app/importers` 当前实际导入器：

- `students.py`
- `teachers.py`
- `scores.py`
- `timetable.py`
- `evaluation.py`
- `admissions.py`
- `enrollment_plans.py`
- `base.py`

高考官方数据导入不在 `importers/`，而是在 `services/gaokao_official_importers.py` 和根目录脚本中维护。

### 导出器

`apps/backend/app/exporters` 当前实际导出器：

- `archive.py`
- `recommendations.py`
- `reports.py`
- `students.py`
- `teachers.py`
- `templates.py`
- `workload.py`

## 7. 当前测试文件

后端测试：

- `apps/backend/tests` 当前有 20 个 `test_*.py` 文件，外加 `conftest.py`
- 覆盖 API、系统和归档、工作台、数据健康、评教量化、考试、gaokao API、导入框架、物化、路径、预估分、成绩分析、推荐导出、推荐工作流、山东冲稳保、学生批量删除、批量调班、学生导入、工作量

前端单测：

- `apps/frontend/tests` 当前有 28 个测试文件
- 覆盖分析 helper、API client、考试科目配置、高考数据报告和证据、导入中心、导入反馈、导航、升学方案、推荐对比/文案/策略/提交/输出保护、报表洞察、山东推荐工作台、学生批量操作、升学画像、用户反馈、志愿工作台

跨端 E2E：

- `tests/e2e/dashboard-smoke.spec.ts`
- 当前 32 条流程集中在一个文件
- fixtures：
  - `admissions-cross-province.xlsx`
  - `admissions-import.xlsx`
  - `enrollment-plans-import.xlsx`
  - `scores-import.xlsx`
  - `scores-invalid.xlsx`

## 8. 质量门禁结果

### `npm run check`

结果：通过。

- 后端全量测试：`101 passed`
- 前端静态检查：通过
- 前端单元测试：`28 files / 157 tests passed`
- 前端生产构建：通过

### `npm run check:all`

结果：通过。

- 后端全量测试：`101 passed`
- 前端静态检查：通过
- 前端单元测试：`28 files / 157 tests passed`
- 前端生产构建：通过
- 跨端 E2E：`32 passed`
- E2E 用时：约 `7.2m`

说明：完整门禁重复执行了常规门禁后再跑 E2E，确认当前主线不是只靠单测通过。

## 9. 已确认已有的功能

从真实文件、路由和测试确认，当前已有：

- 本地启动、停止、开发启动和质量门禁脚本
- 工作台摘要接口和工作台页面
- 基础数据维护
- 学生管理、学生详情、学生导入导出、附件、成长档案、职业偏好
- 学生批量软删除、批量调班、调班审计和调班历史
- 教师管理、教师详情、任教关系、职称历史、教师导入导出
- 考试、科目配置、成绩导入、成绩批次和重算
- 学生、班级、年级、教师分析及全景对比
- 课表导入、未匹配修正、工作量规则、工作量计算、工作量导出和打印
- 评教模板、评教导入、评教汇总、教师评教趋势、班主任量化
- 导入中心批次聚合、模板入口、错误报告和撤销说明
- 报表导出、打印页、导出记录和下载
- 系统文件、备份恢复、审计日志、系统配置、数据修复
- 高考数据总览、数据健康、山东覆盖矩阵、审阅、院校证据和监控
- 升学路径、学生升学画像、路径评估、升学路径报告
- 推荐中心、山东普通类冲稳保、志愿工作台、志愿草稿、版本对比、就业方向和专业就业映射
- 规则字典：省份志愿规则、赋分规则、选科字典、特殊类型规则
- P0 数据健康和 P0 备份恢复验收脚本
- Electron 桌面壳和打包脚本

## 10. 报告提到但代码中未确认或尚未完成的功能

这些内容不能在后续开发中假定已经完成：

- 独立考勤中心、行为预警中心：当前未确认存在独立模型、页面或路由；后续若做，只能基于已有数据做空态或说明，不能直接新增表。
- 无快照的一键导入回滚：当前导入中心有撤销说明，但未实现通用自动回滚；继续保持“先备份、重新导入、业务页修正”边界。
- 非开发用户长期交付所需的桌面端重新打包验证：当前有 Electron 配置和脚本，但本次 M0 未重新执行 `desktop:dist:*`。
- 真实学校成绩数据试跑：当前主库 `score_record=0`，分析链路通过测试但未用真实成绩数据验证教学效果。
- 单招 / 综评完整录取判断：当前数据健康仍提示缺专门录取结果，只能初筛和人工复核。
- 2024 山东招生计划完整性：当前报告仍提示数量偏少，不能视为完整计划库。
- 招生章程限制链自动完成：仍有大量待人工复核，机器预审不能替代人工确认。
- M1 之后的新规划能力，如“今日教务决策台”“真实数据试跑流程”“学生/教师 360° 总览增强”，尚未在本轮实现。

## 11. 当前风险项

1. 真实教学业务数据不足：教师 2 条、考试 1 条、成绩 0 条。
2. 高考数据健康仍为 `warning`：单招 / 综评缺专门录取结果、2024 招生计划偏少、章程限制链待复核。
3. 大文件风险仍集中：
   - `apps/frontend/src/pages/GaokaoDataPage.vue`：2337 行
   - `apps/backend/tests/test_recommendation_workflow.py`：2301 行
   - `apps/backend/app/services/gaokao_pathways.py`：2264 行
   - `apps/backend/app/services/gaokao.py`：2168 行
   - `apps/frontend/src/components/recommendations/RecommendationVolunteerWorkbenchPanel.vue`：2105 行
   - `apps/backend/app/exporters/recommendations.py`：1838 行
   - `apps/backend/app/services/students.py`：1679 行
4. E2E 集中在 `tests/e2e/dashboard-smoke.spec.ts`，当前 32 条通过但单文件约 1458 行，后续失败定位成本会继续上升。
5. 仓库体积大，`data/` 和备份包是主要来源；不能为了瘦身随意删除主库、备份和 handoff。

## 12. M1 前建议

- M1 可以直接从 `DashboardPage.vue`、`apps/backend/app/services/dashboard.py`、`apps/backend/app/api/routes/dashboard.py` 和 `apps/backend/app/schemas/dashboard.py` 入手。
- 工作台需要的数据尽量复用已有服务和现有 API；如果缺最近导入、最近备份、数据健康状态，优先读现有 `system`、`import-center`、`gaokao/data-health` 能力。
- 不新增数据库表；工作台卡片和下一步建议先用现有数据计算。
- 改动后至少运行 `npm run check`；如果触碰导航、工作台主流程或跨页面入口，补跑相关 E2E 或 `npm run check:all`。
