# 本地教务工具

本项目用于实现一个面向高中场景的本地单机教务决策台，遵循 `AGENTS.md` 与 [`docs/local_edu_tool_dev_spec.md`](./docs/local_edu_tool_dev_spec.md)。

## 快速导航

- 第一次接手仓库：
  先看 [`AGENTS.md`](./AGENTS.md)、[`docs/local_edu_tool_dev_spec.md`](./docs/local_edu_tool_dev_spec.md)、[`memory-bank/active-context.md`](./memory-bank/active-context.md)、[`memory-bank/handoff.md`](./memory-bank/handoff.md)
- 按 Codex App 多窗口继续开发：
  先看 [`docs/repo-audit.md`](./docs/repo-audit.md)、[`docs/mac-dev-setup.md`](./docs/mac-dev-setup.md)、[`docs/development-roadmap.md`](./docs/development-roadmap.md)
- 想先搞清楚顶层目录和文档入口：
  看 [`docs/README.md`](./docs/README.md)、[`scripts/README.md`](./scripts/README.md)、[`handoffs/README.md`](./handoffs/README.md)
- 只想知道怎么运行和验证：
  直接用 `npm run start:local`、`npm run dev`、`npm run clean:local`、`npm run clean:slim`、`npm run check`、`npm run check:all`
- 只想在 Mac 上双击启动：
  看 [`docs/mac-user-startup-guide.md`](./docs/mac-user-startup-guide.md)，开发窗口看 [`docs/mac-developer-checklist.md`](./docs/mac-developer-checklist.md)
- 只想做 P0 交付验收：
  直接用 `npm run backend:p0-check`，步骤说明见 [`docs/p0_delivery_runbook_2026-04-24.md`](./docs/p0_delivery_runbook_2026-04-24.md)
- 只想看测试布局：
  看 [`tests/README.md`](./tests/README.md)
- 只想知道改完该跑哪些验收：
  看 [`docs/codex-task-acceptance-checklist.md`](./docs/codex-task-acceptance-checklist.md)；测试体系审计见 [`docs/test-quality-audit-2026-04-24.md`](./docs/test-quality-audit-2026-04-24.md)
- 只想看最终整合和能否试用：
  看 [`docs/final-acceptance-report-2026-04-24.md`](./docs/final-acceptance-report-2026-04-24.md)
- 想找项目级规则来源：
  `AGENTS.md` 由 [`rulesync.jsonc`](./rulesync.jsonc) 和项目内 `.rulesync/` 来源维护，不建议手改生成结果

当前进度聚焦里程碑 `M0`、`M1`、`M2`、`M3`、`M4`、`M5` 与 `M6`：

- 已规划并初始化 monorepo 结构
- 后端采用 `FastAPI + SQLAlchemy + SQLite + Alembic`
- 前端采用 `Vue 3 + TypeScript + Vite + Element Plus`
- 当前实现重点为基础数据、学生、教师、任教关系、考试管理、成绩导入与分析、课表与工作量、成长档案、升学推荐、评教量化、报表中心、本地备份恢复
- 已提供演示数据、自动化测试和前端生产构建能力

## 当前主线

- 旧推荐中心已具备院校库、专业库、录取库、普通生/艺体生推荐、策略模板、历史回放、推荐报告导出与定向 E2E
- `/recommendations` 已升级为“高考志愿”工作台形态，当前已落地招生计划库、省份规则、就业方向库、专业就业映射、学生志愿工作台、志愿草稿打印/导出、职业意向输入与职业匹配解释第一轮
- 应用侧 Stage B 规则库已继续补齐：当前 `data/app.db` 已新增 `province_score_transform_rule` 与 `subject_requirement_dict` 两类规则表，后端已补 CRUD / bootstrap 接口，`/api/gaokao/shandong-monitor` 在缺少原始 `gaokao_*` 表时也可回退到这两类应用侧规则表做只读展示
- 2026-04-22 已继续把嵌入主库的原始高考表整理到项目业务表：当前 `data/app.db` 内已物化 `college=3455`、`major=13959`、`admission_record=170385`、`enrollment_plan=6338`、`college_major=60761`；其中招生计划已继续纳入 `春季高考 / 艺术类 / 单独招生 / 综合评价招生 / 体育类`，录取结果仍主要是普通类，因为当前 raw 结果源本身就是普通类口径
- 2026-04-22 已继续把这批类型接进消费链：录取库 / 招生计划库当前都支持按 `student_type` 过滤；推荐候选筛选也已改成“精确类别匹配”，不会再把 `spring_exam / art / sports / independent_recruitment / comprehensive_evaluation` 混成一类
- 2026-04-22 已继续补特殊类型参考链：`spring_exam / independent_recruitment / comprehensive_evaluation` 在缺少专门录取结果时，当前会显式回退参考普通类录取结果，并带风险标记与说明；`art / sports` 仍保持艺体口径，不会和这三类混用
- 2026-04-23 已继续补山东专用规则基线：`province_volunteer_rule` 当前已增至 81 条，山东 2026 年常见普通类批次、春季高考、艺术类、体育类、单独招生、综合评价招生等批次都有专用规则可命中，减少了工作台对通用规则的依赖
- 2026-04-23 已把山东规则补到双年份：当前 `province_volunteer_rule / province_score_transform_rule / subject_requirement_dict` 都已同时覆盖 `2025` 和 `2026`，页面默认切到山东后不再只命中一个未来年份基线
- 2026-04-23 已把职业方向和专业就业映射从空库补到可用：当前 `employment_direction=14`、`major_employment_mapping=12975`，职业匹配、工作台职业意向和推荐解释不再是空白底座
- `volunteer_draft_summary` 的导出前摘要、Excel“边界概览”与志愿草稿打印页已继续统一：草稿详情现在会实时复用现有规则匹配逻辑返回 `rule_alerts + applicable_rules`，未命中明确省份规则的草稿不会再误判成“通用考生规则”，并可继续细分到缺省份/年份/批次/模式等规则缺口；当前报表中心导出前摘要、草稿打印页和 Excel 都已能展示“规则差异摘要”
- Stage B 工作台预览的聚合口径又和草稿链再对齐了一步：当前工作台“边界概览”里的 `missing_rule_*` 和“已回退到通用考生规则”也会按候选数量汇总，不再只停留在泛化提示；页面、草稿打印/报表摘要和 Excel 现在对这类 live 规则缺口的表达更一致
- Stage B 的年份边界解释又补了一层：当前候选池、草稿打印页、报表中心 `volunteer_draft_summary` 导出前摘要和 Excel“边界概览”都会显式提示“参考年份偏旧”，当录取样本最近年份与目标年份相差 2 年及以上时，会提醒排序和解释偏保守
- Stage B 的工作台/草稿聚合解释又补了两类显式摘要：当前工作台“边界概览”、草稿打印页、报表中心 `volunteer_draft_summary` 导出前摘要和 Excel“边界概览”都会继续汇总“类别专用规则口径”和“跨年份参考样本”，不懂数据库的人也能直接看出同省同年不同类别、同省跨年份样本并存时为什么解释会变化
- 同一类“参考年份偏旧”提示已继续扩到推荐报告链：推荐结果页输出前复核、推荐打印页、报表中心 `recommendation_summary` 导出前摘要和 Excel“风险概览”也会在近一年录取样本缺失时给出全局提醒
- 推荐结果页和推荐打印页的单条“理由”说明也已跟上这条口径：当结果快照最近录取样本与目标年份相差 2 年及以上时，会在单条推荐说明里直接补出“排序和解释偏保守”
- 推荐页的单方案对比与批量对照已继续补齐聚合级“参考年份变化”解释：同一院校/专业在不同方案里的最近录取样本年份变化会被单独汇总，且会进一步提示其中有多少条同时伴随冲稳保分组变化，批量对照表也可直接查看“年变伴随分组变”
- 推荐历史对照页又补了一层年份边界解释：当前不仅会汇总“参考样本年份切换”，也会单独识别“最近样本年份没变，但在新目标年份下已变成偏旧样本”的 `stale-only` 场景；单方案对比卡、批量对照表、打印页、报表中心摘要和 Excel“风险概览”都会按同一口径解释
- `/gaokao-data` 已新增高考数据只读驾驶舱第一版：当前可查看数据总览、数据审阅、院校证据页和山东首期监控；后端已补 `/api/gaokao/data-overview`、`/import-batches`、`/review-summary`、`/college-evidence/{college_id}`、`/shandong-monitor`，现在会优先读取独立高考主线库 `data/local_edu_tool/local_edu.sqlite3`，缺失时再回退到 sync board 基线或现有应用模型
- 2026-04-22 已把 handoff 的 `gaokao_*` 原始表、`data_import_error_log`、`score_rank_segment` 并入 `data/app.db`；当前若主库已嵌入这些 raw 表，应用会优先直接走单库，`data/local_edu_tool/local_edu.sqlite3` 则退到同步来源 / fallback 角色
- 2026-04-24 已补 P0 数据健康检查入口和页面看板：`npm run backend:data-health` 与 `/api/gaokao/data-health` 会读取 `data/app.db`，输出核心表数量、山东年份覆盖、考生类型覆盖和缺口摘要；`/gaokao-data` 已新增“山东覆盖”页签，并库、物化、特殊类型规则初始化脚本现在都会输出执行前后的健康摘要，特殊类型规则初始化默认先备份主库
- 2026-04-24 已补阶段一覆盖矩阵和审计摘要：`backend:data-health -- --json` 现在返回山东按年份 / 类别 / 批次的覆盖明细、缺少年份和 `audit_summary`；`/gaokao-data` 的“山东覆盖”页签可展开查看按年矩阵，并显示当前记录数、疑似重复、冲突、待人工复核和特殊类型“仅可做初筛”等缺口
- 2026-04-24 已继续把 P0 特殊类型规则字典接到前端：`/recommendations` 新增“特殊类型规则”页签，可查看山东春考、综评、单招、艺术、体育等规则的细分类别、匹配关键词、核对清单、初筛优先级和来源备注，并可从页面触发山东基线装载
- 2026-04-24 已开始落地阶段二规则核对入口：`/recommendations` 现新增“赋分规则”和“选科字典”页签，能查看 `province_score_transform_rule` 与 `subject_requirement_dict` 的省份、年份、模式、赋分科目、等级表、折算公式、标准化选科和来源备注；三类规则字典均按页签懒加载，避免拖慢推荐主流程
- 系统安全与输出链继续收口：备份恢复路径已纳入允许目录校验；推荐打印页 / 报表中心已统一通过共享 helper 组装推荐解释入参，跨省历史方案差异不会再在打印链路丢失；`grade_summary` 与 `teacher_analysis` Excel 导出也已补齐和打印页一致的摘要结构
- 高复杂模块继续按“小步抽 helper”收口：Stage B 工作台边界/规则摘要已拆到 `apps/frontend/src/components/recommendations/volunteerWorkbenchInsights.ts`，评教批次统计已拆到 `apps/backend/app/services/_evaluation_batch_stats.py`，工作量逐教师计算已拆到 `apps/backend/app/services/_workload_calculation.py`；现有接口、页面入口和导出链保持不变
- 当前开发顺序以 [`gaokao_dev_bundle_v3/gaokao_dev_doc_v3.md`](./gaokao_dev_bundle_v3/gaokao_dev_doc_v3.md) 为准：Stage A 已基本收尾，Stage B 的“全国省份规则基线装载”和“生源地 / 预估分数正式建模”第一轮已落地，批量混合生源地前端跨端回归、“缺少年份规则”解释和 `3+1+2 -> 物理类/历史类` 模式兼容回退也已补齐，下一步优先补更多省份/年份边界和结果解释细化

## 目录结构

```text
local-edu-tool/
  apps/
    backend/
    frontend/
  data/
    local_edu_tool/
    uploads/
    backups/
    templates/
    exports/
    logs/
  docs/
  handoffs/
  scripts/
  tests/
```

## 数据库约定

- 应用主库默认仍是 `data/app.db`
- 2026-04-22 起，若 `data/app.db` 内已经嵌入 `gaokao_*` 原始表、`data_import_batch`、`score_rank_segment` 等 handoff 表，应用会优先直接走单库，不再强依赖独立高考库
- `data/local_edu_tool/local_edu.sqlite3` 现在更适合作为 handoff 同步来源和 fallback 输入，而不是唯一运行库
- 如需改高考库位置，可设置 `LOCAL_EDU_GAOKAO_DB_PATH=/绝对路径/local_edu.sqlite3`
- 当前接管包已整理到 `handoffs/2026-04-21_mac_db_handoff`
- `data/local_edu_tool/local_edu.sqlite3` 当前可以指向 handoff 包内快照；如需把其原始高考表并入主库，执行 `npm run backend:merge-handoff`
- `data/backups/` 是主库备份目录。`backend:merge-handoff`、`backend:materialize-gaokao` 默认会先备份主库；`backend:bootstrap-special-types`、`backend:bootstrap-pathways` 也会在写入规则前备份，除非显式传入 `-- --no-backup`
- 交付前或补数据前先执行 `npm run backend:data-health`；需要机器可读结果时执行 `npm run backend:data-health -- --json`。该 JSON 同时包含阶段一覆盖矩阵和导入审计摘要，可用于补数据前后对照

## 开发环境

- Node.js 20+
- npm 10+
- Python 3.11+

> 当前机器提供 `python3`，如版本高于 3.11 也可运行。项目默认按 `>=3.11` 兼容配置。

## 本地启动

普通使用最省事的方式：

```bash
npm run start:local
```

该命令会后台启动或复用前后端服务，启动成功后可以关闭终端。日志位于 `data/logs/local-services/`。

开发调试时可以使用：

```bash
npm run dev
```

`npm run dev` 是前台开发模式，终端关闭后前端服务会停止。

如果你在 macOS 上更希望直接双击启动，也可以在仓库根目录双击：

[`start-local-edu.command`](./start-local-edu.command)

普通用户步骤见 [`docs/mac-user-startup-guide.md`](./docs/mac-user-startup-guide.md)，开发检查清单见 [`docs/mac-developer-checklist.md`](./docs/mac-developer-checklist.md)。

它会在根目录后台启动或复用前后端服务，默认地址仍是：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`
- API 文档：`http://127.0.0.1:8000/docs`

启动前会先预检 `127.0.0.1:5173` 和 `127.0.0.1:8000`。
如果端口已被占用，或当前上下文无权限监听，脚本会直接报清晰错误并退出，不再先半启动一个服务、再把另一侧连带带停。

如需停止后台服务：

```bash
npm run stop:local
```

### macOS / Linux

```bash
./scripts/dev.sh
```

### Windows PowerShell

```powershell
./scripts/dev.ps1
```

脚本会完成以下工作：

1. 创建或复用根目录 `.venv`
2. 安装后端依赖
3. 执行数据库迁移
4. 初始化模板与示例数据
5. 启动后端服务
6. 安装并启动前端开发服务

默认地址：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`
- API 文档：`http://127.0.0.1:8000/docs`

## 手工初始化

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e './apps/backend[dev]'
cd apps/backend
alembic upgrade head
cd ../..
python scripts/init_data.py --demo
npm install
npm run frontend:dev
```

常用根目录统一入口：

```bash
npm run clean:local
npm run clean:slim
npm run backend:migrate
npm run backend:merge-handoff
npm run backend:materialize-gaokao
npm run backend:bootstrap-special-types -- --year 2025 --year 2026
npm run backend:bootstrap-pathways -- --target-year 2026
npm run backend:data-health
npm run backend:p0-check
npm run backend:init-demo
npm run backend:test
npm run backend:dev
npm run dev
```

## 测试

后端测试：

```bash
npm run backend:test
```

前端静态检查：

```bash
npm run frontend:lint
```

前端单元测试：

```bash
npm run frontend:test
```

前端构建：

```bash
npm run frontend:build
```

跨端 E2E 冒烟：

```bash
npm run e2e:install
npm run e2e
```

统一项目体检：

```bash
npm run check
npm run check:e2e
npm run check:all
```

- `npm run check`：后端全量 pytest + 前端 lint + 前端单测 + 前端构建
- `npm run check:e2e`：执行 `tests/e2e/dashboard-smoke.spec.ts`
- `npm run check:all`：先跑 `check`，再跑 `check:e2e`

测试目录约定：

- 后端单元与接口工作流测试位于 `apps/backend/tests`
- 前端单元测试位于 `apps/frontend/tests`
- 根目录 `tests/e2e` 已落地 Playwright 跨端流程，默认启动临时演示数据后端和 Vite 前端

## 桌面打包

第一版桌面壳已落地，采用 `Electron + FastAPI + SQLite`：

```bash
./.venv/bin/pip install -e './apps/backend[desktop]'
npm install
npm run desktop:prepare
npm run desktop:dist -- --dir
```

可选目标：

```bash
npm run desktop:dist:mac
npm run desktop:dist:win:dir
npm run desktop:dist:win:nsis
```

当前已验证的桌面产物：

- macOS `dir` 目录产物：`dist/desktop/mac/本地教务工具.app`
- Windows `dir` 目录产物：`dist/desktop/win-unpacked/`
- Windows `nsis` 安装包：`dist/desktop/本地教务工具-0.1.0-win-x64.exe`
- 后端独立二进制：`apps/desktop/.dist/backend/local-edu-backend-desktop`
- 开发态桌面入口：`npm run desktop:dev`
- 桌面菜单已支持直接打开数据目录、导出目录和 API 文档

## 已完成内容

- Monorepo 基础骨架
- SQLite 与 Alembic 初始化
- `data/` 本地目录约定
- 导入模板自动生成
- 工作台摘要接口与页面
- 工作台增强：最近考试摘要、快捷入口、数据质量提醒
- 基础数据管理：学年、学期、年级、班级、学科、字典
- 学生管理：列表、详情、创建、更新、模板下载、Excel 导入导出
- 学生详情页：家庭联系人、学籍历史、成绩摘要、成长档案、推荐记录、附件聚合
- 学生附件管理：独立挂接、下载、删除，与成长档案附件引用分开展示
- 教师管理：列表、详情、创建、更新、模板下载、Excel 导入导出
- 教师画像：职称历史维护、任教安排、考试趋势、同学科横向对比
- 任教关系维护与列表
- 考试管理：考试列表、详情、新增、编辑
- 考试科目配置：满分、是否计入总分、优秀线、及格线、排序
- 成绩导入：模板下载、Excel 导入、错误报告、导入批次记录
- 成绩快照：总分、班级名次、年级名次、百分位重建
- 分析中心：学生分析、班级分析、教师任教分析
- 分析中心增强：年级分析、班级横向对比、学科横向对比、分数段与名次段统计
- 分析中心增强：多学年全景对比（年级 / 班级 / 教师视角）
- 分析中心增强：多学年全景对比看板（学年摘要、时间轴、学科趋势、学科攻坚优先级、风险预警）
- 桌面打包第一版：Electron 桌面壳、后端独立二进制、桌面菜单入口、macOS `dir` 目录产物、Windows `dir` / `nsis` 产物
- 桌面体验增强：首次启动提示、桌面内打印预览、数据目录 / 导出目录 / API 文档菜单入口
- 课表管理：模板下载、Excel 导入、批次管理、未匹配项修正
- 工作量规则：默认版本、规则版本化、规则项维护、计算后锁定
- 课时与工作量：周课时、月度课时、学期课时、工作量计算、结果快照、Excel 导出
- 前端页面：新增“课表工作量”入口，覆盖导入、修正、规则、计算、导出闭环
- 成长档案：时间线记录、分类筛选、附件上传、单个学生档案摘要导出
- 推荐中心：院校库、专业库、录取库、普通生推荐、艺体生推荐、方案历史、推荐报告导出
- 推荐中心收尾：策略模板保存/应用/删除、历史方案回放、导出失败回退定向 E2E
- 评教与量化：评教模板、评教导入、教师评教汇总、班主任量化规则版本、量化记录、附件证明、量化汇总
- 报表中心：学生分析、班级分析、年级汇总、教师分析、工作量、成长档案摘要、推荐报告、评教汇总、班主任量化统一导出与记录
- 系统工具：本地文件上传、备份列表、创建备份、恢复备份、审计日志查看
- 系统设置：参数配置、模板管理、数据修复工具
- 系统安全收口：上传分类校验、下载路径边界校验、重复系统模板路由清理
- 高考数据只读驾驶舱：总览、审阅、院校证据页、山东监控页，以及对应只读接口与空态 / 演示态 fallback
- 报表导出摘要统一：`grade_summary` 现已复用 `get_grade_analytics()` 输出 `年级概况 -> 班级汇总 -> 学科汇总`，`teacher_analysis` 导出已补“任教拆分”摘要
- 高复杂模块小步拆分：`volunteerWorkbenchInsights.ts`、`_evaluation_batch_stats.py`、`_workload_calculation.py` 已分别承接 Stage B 工作台 insight、评教批次统计和工作量逐教师计算
- 前端工程化：ESLint、Vitest、Playwright 跨端流程
- 打印预览：报表中心 9 类核心输出均已支持浏览器打印 / 保存为 PDF
- 工作量页页面级逻辑已抽离到 `apps/frontend/src/components/workload/useTimetableWorkloadPage.ts`
- 评教页页面级逻辑已抽离到 `apps/frontend/src/components/evaluation/useEvaluationQuantPage.ts`
- 推荐页组合逻辑已拆到 `apps/frontend/src/components/recommendations/useRecommendationCatalogManager.ts` 与 `useRecommendationWorkflow.ts`
- 推荐页工作流逻辑已继续细分到 `useRecommendationGenerationManager.ts` 与 `useRecommendationHistoryManager.ts`
- 推荐页历史链已继续细分到 `useRecommendationHistoryCollection.ts` 与 `useRecommendationSchemeComparison.ts`
- 推荐页方案对比链已继续细分到 `useRecommendationSingleComparison.ts`、`useRecommendationMultiComparison.ts` 与 `useRecommendationSchemeExport.ts`
- 推荐页生成链已继续细分到 `useRecommendationSubmissionManager.ts` 与 `useRecommendationStrategyManager.ts`
- 推荐页策略链已继续细分到 `useRecommendationStrategySettings.ts` 与 `useRecommendationStrategyPresets.ts`
- 推荐页提交前置校验与 payload 组装已下沉到 `apps/frontend/src/components/recommendations/recommendationSubmission.ts`
- 后端推荐生成链已继续拆分到 `apps/backend/app/services/_recommendations_candidates.py`、`_recommendations_result_builder.py` 与 `_recommendations_history.py`
- 根目录已补 `backend:migrate`、`backend:init-demo`、`backend:test` 与 `backend:dev` 统一入口，后端常用操作不再只依赖手工激活虚拟环境
- `tests/e2e/dashboard-smoke.spec.ts` 已扩到 30 条跨端流程，补齐推荐历史空状态、多方案对比、失败回退、策略模板、历史回放、导出失败回退、高考志愿主线、Stage B 主链路、批量混合生源地链路、缺少年份规则解释、模式兼容回退与多条异常提示回归
- “高考志愿”S1 数据底座已开始落地：新增招生计划库、省份志愿规则配置、页内管理面板与对应 Alembic 迁移
- 后端已新增 `EnrollmentPlan`、`ProvinceVolunteerRule`、招生计划导入器、模板生成与 `/api/enrollment-plans`、`/api/province-volunteer-rules` 接口
- 前端 `/recommendations` 已升级为“高考志愿”工作台形态，现可在同页维护院校库、专业库、招生计划库、录取库、省份规则与推荐中心
- “高考志愿”Stage B 第一段与第二段第一轮已落地：全国省份规则基线装载、学生生源地、目标年份、分数模式、推荐历史快照增强、志愿草稿与打印导出说明已接入主链路
- “高考志愿”S4 第一轮已落地就业方向库、专业就业映射、学生职业意向、职业匹配排序/解释与推荐报告导出增强
- 初始化种子数据与演示数据脚本
- M1/M2/M3/M4/M5/M6 后端测试与前端构建验证
- 工作台 / 学生详情 / 教师详情 / 系统设置增强验证

## 尚未完成内容

- `apps/frontend/src/pages/EvaluationQuantPage.vue` 已降为页面装配层，但 `useEvaluationQuantPage.ts` 后续如继续增长仍可再按模板/批次/量化子域细分
- `apps/frontend/src/pages/TimetableWorkloadPage.vue` 已降为页面装配层，但 `useTimetableWorkloadPage.ts` 后续如继续增长仍可再按导入/规则/结果子域细分
- `apps/frontend/src/pages/RecommendationsPage.vue` 已维持页面装配层，推荐页 facade 已基本稳定；如继续增长，可优先沿 `recommendationSubmission.ts`、`useRecommendationStrategyPresets.ts` 与 `useRecommendationSingleComparison.ts` 再按子域细分
- 打印优化已覆盖报表中心 9 类核心输出；多学年全景对比与复杂分析看板都已有年级 / 班级 / 教师第一轮闭环；桌面打包已有 macOS `dir` 与 Windows `dir` / `nsis` 产物，剩余 P2 重点转到应用图标、签名/安装体验和更广泛的业务域扩展
- `apps/backend/app/services/evaluation.py` 与 `apps/backend/app/services/recommendations.py` 已完成第一轮 service 拆分，但私有子模块中仍有继续细分的空间，尤其是 `_evaluation_batches.py` 与 `_recommendations_result_builder.py`
- 前端整体视觉已做一轮收敛，但部分页面之间的信息密度、操作节奏和局部空状态仍可继续统一
- 前端关键危险操作已补一轮确认与前置校验，但仍可继续系统性梳理其他删除/覆盖类动作
- `gaokao_dev_bundle_v3` 的 Stage A 已基本收尾；Stage B 前两段第一轮已完成，当前剩余重点转到更多省份/年份差异、结果解释与可视化收口

## 下一步建议

1. 按 `gaokao_dev_bundle_v3` 继续收口 Stage B，优先补更多省份/年份边界、结果解释与结果可视化
2. 桌面端继续补应用图标、签名/安装体验和 Windows 安装分发说明
3. 继续拆分 `_evaluation_batches.py`、`_recommendations_result_builder.py` 与较大的页面级 composable，避免复杂度再次集中

## 已验证

以下命令已在当前环境通过：

```bash
npm run backend:migrate
npm run backend:init-demo
npm run backend:test
npm run frontend:build
```

本地启动冒烟检查结果：

- `uvicorn` 成功监听 `127.0.0.1:8000`
- `GET /api/dashboard/summary` 返回演示数据统计：学生 `3`、教师 `2`、年级 `3`、班级 `2`

当前测试覆盖：

- 学生导入校验
- 教师导入与任教关系维护
- 排名算法与百分位
- 建考试 -> 配科目 -> 导入成绩 -> 学生/班级/教师分析流程
- 课表导入 -> 未匹配修正 -> 工作量规则加载 -> 工作量计算 -> 导出报表流程
- 成长档案附件上传 -> 记录维护 -> 摘要导出流程
- 备份创建 -> 数据变更 -> 备份恢复流程
- 录取数据导入 -> 普通生推荐 -> 艺体生推荐 -> 历史方案导出流程
- 评教模板 -> 原始数据导入 -> 教师汇总 -> 班主任量化记录 -> 报表导出流程

本轮额外验证：

- `2026-04-06` 已重新执行 `./.venv/bin/pytest apps/backend/tests`，`21` 个后端测试全部通过
- `2026-04-06` 已重新执行 `npm run frontend:build`，评教量化页拆分后的前端构建通过
- `2026-04-06` 已再次执行 `npm run frontend:build`，工作量页拆分与全局 UI 收敛后的前端构建通过
- `2026-04-06` 已再次执行 `npm run frontend:build`，推荐页数据/动作逻辑抽离后的前端构建通过
- `2026-04-06` 已新增系统安全测试：非法上传分类、非法下载路径、异常数据库文件路径、系统模板路由形态
- `2026-04-06` 已再次执行 `npm run frontend:build`，系统修复确认、学生附件删除确认、策略模板删除确认与报表导出前置校验后的前端构建通过
- `2026-04-06` 已新增 `apps/frontend/eslint.config.js` 与 `npm run frontend:lint`，静态检查通过
- `2026-04-06` 已新增 `apps/frontend/tests` 下 3 个 Vitest 用例文件，`npm run frontend:test` 通过（10 个测试）
- `2026-04-06` 已新增 `playwright.config.ts`、`tests/e2e/dashboard-smoke.spec.ts` 和 `scripts/run_e2e_backend.py`
- `2026-04-06` 已再次执行 `npm run e2e`，当前 3 个 Playwright 跨端流程通过：工作台导航、学生详情链路、系统备份链路
- `2026-04-06` 已新增 `apps/frontend/src/components/workload/useTimetableWorkloadPage.ts`，把工作量页数据加载、watchers 和动作编排从页面主文件中抽离
- `2026-04-06` 已再次执行 `npm run frontend:lint`、`npm run frontend:test`、`npm run frontend:build`、`npm run e2e`，上述工作量页逻辑抽离后的验证通过
- `2026-04-06` 已新增 `apps/frontend/src/components/evaluation/useEvaluationQuantPage.ts`，把评教页数据加载、批次分析、量化规则和量化记录动作从页面主文件中抽离
- `2026-04-06` 已把 `tests/e2e/dashboard-smoke.spec.ts` 扩到第 4 条流程：新建考试 -> 配科目 -> 带到分析中心
- `2026-04-06` 已再次执行 `npm run frontend:lint`、`npm run frontend:test`、`npm run frontend:build`、`npm run e2e`，当前分别通过 `lint`、10 个前端测试、前端构建和 4 个 Playwright 跨端流程
- `2026-04-06` 已新增 `tests/e2e/fixtures/scores-import.xlsx` 与 `tests/e2e/fixtures/admissions-import.xlsx`，用于稳定复用成绩导入与录取导入样例
- `2026-04-06` 已把 `tests/e2e/dashboard-smoke.spec.ts` 扩到第 5、6 条流程：报表中心导出学生分析单、推荐中心导入录取数据并生成/导出推荐报告
- `2026-04-06` 已再次执行 `npm run frontend:lint` 与 `npm run e2e`，当前 6 个 Playwright 跨端流程通过
- `2026-04-06` 已新增 `tests/e2e/fixtures/scores-invalid.xlsx`，用于覆盖考试错误模板导入提示
- `2026-04-06` 已把 `tests/e2e/dashboard-smoke.spec.ts` 再扩到第 7、8、9 条流程：错误成绩模板导入提示、报表缺参提示、推荐缺参提示
- `2026-04-06` 已修正 `apps/backend/app/services/exams.py`，成绩导入模板错误现在返回 `400` 业务错误而不是 `500`
- `2026-04-06` 已执行 `./.venv/bin/pytest apps/backend/tests`，当前 22 个后端测试通过；`npm run e2e` 当前 9 条 Playwright 跨端流程通过
- `2026-04-06` 已新增 `apps/frontend/src/components/recommendations/useRecommendationCatalogManager.ts` 与 `useRecommendationWorkflow.ts`，并把 `useRecommendationsPage.ts` 收成 facade
- `2026-04-06` 已再次执行 `npm run frontend:lint`、`npm run frontend:test`、`npm run frontend:build`、`npm run e2e`，推荐页组合逻辑拆分后的验证通过
- `2026-04-06` 已新增 `apps/frontend/src/components/recommendations/useRecommendationGenerationManager.ts` 与 `useRecommendationHistoryManager.ts`，并把 `useRecommendationWorkflow.ts` 收成 facade
- `2026-04-06` 已再次执行 `npm run frontend:lint`、`npm run frontend:test`、`npm run frontend:build`、`npm run e2e`，推荐页工作流二次细分后的验证通过
- `2026-04-06` 已新增 `apps/frontend/src/components/recommendations/useRecommendationHistoryCollection.ts` 与 `useRecommendationSchemeComparison.ts`，并把 `useRecommendationHistoryManager.ts` 收成 facade
- `2026-04-06` 已再次执行 `npm run frontend:lint`、`npm run frontend:test`、`npm run frontend:build`、`npm run e2e`，推荐页历史链细分后的验证通过
- `2026-04-06` 已新增 `apps/frontend/src/components/recommendations/useRecommendationSingleComparison.ts`、`useRecommendationMultiComparison.ts` 与 `useRecommendationSchemeExport.ts`，并把 `useRecommendationSchemeComparison.ts` 收成 facade
- `2026-04-06` 已再次执行 `npm run frontend:lint`、`npm run frontend:test`、`npm run frontend:build`、`npm run e2e`，推荐页方案对比链细分后的验证通过
- `2026-04-06` 已新增 `apps/frontend/src/components/recommendations/useRecommendationSubmissionManager.ts` 与 `useRecommendationStrategyManager.ts`，并把 `useRecommendationGenerationManager.ts` 收成 facade
- `2026-04-06` 已再次执行 `npm run frontend:lint`、`npm run frontend:test`、`npm run frontend:build`、`npm run e2e`，推荐页生成链细分后的验证通过
- `2026-04-06` 已新增 `apps/frontend/src/components/recommendations/useRecommendationStrategySettings.ts` 与 `useRecommendationStrategyPresets.ts`，并把 `useRecommendationStrategyManager.ts` 收成 facade
- `2026-04-06` 已再次执行 `npm run frontend:lint`、`npm run frontend:test`、`npm run frontend:build`、`npm run e2e`，推荐页策略链细分后的验证通过
- `2026-04-07` 已新增 `apps/frontend/src/pages/RecommendationPrintPage.vue`、`apps/frontend/src/pages/GrowthSummaryPrintPage.vue` 与 `apps/frontend/src/utils/print.ts`
- `2026-04-07` 已在推荐结果页、成长档案页和报表中心补“打印预览”入口，并在路由中新增顶层打印页
- `2026-04-07` 已再次执行 `npm run frontend:lint`、`npm run frontend:build`、`npm run e2e`，打印预览补齐后的验证通过
- `2026-04-07` 已新增 `apps/frontend/src/pages/StudentAnalysisPrintPage.vue`，并把 `student_analysis` 接到报表中心打印预览
- `2026-04-07` 已再次执行 `npm run frontend:lint`、`npm run frontend:build`、`npm run e2e`，学生成绩分析单打印预览补齐后的验证通过
- `2026-04-07` 已新增 `apps/frontend/src/pages/ClassAnalysisPrintPage.vue`、`GradeSummaryPrintPage.vue`、`TeacherAnalysisPrintPage.vue`
- `2026-04-07` 已把 `class_analysis`、`grade_summary`、`teacher_analysis` 接到报表中心打印预览
- `2026-04-07` 已再次执行 `npm run frontend:lint`、`npm run frontend:build`、`npm run e2e`，班级/年级/教师分析打印预览补齐后的验证通过
- `2026-04-07` 已新增 `apps/frontend/src/pages/WorkloadPrintPage.vue`、`EvaluationSummaryPrintPage.vue`、`AdviserQuantPrintPage.vue`
- `2026-04-07` 已把 `teacher_workload`、`evaluation_summary`、`adviser_quant_summary` 接到报表中心打印预览
- `2026-04-07` 已再次执行 `npm run frontend:lint`、`npm run frontend:build`、`npm run e2e`，当前 11 条 Playwright 跨端流程通过，打印优化已覆盖报表中心 9 类核心输出
- `2026-04-09` 已新增 `apps/frontend/src/components/recommendations/recommendationSubmission.ts` 与 `apps/frontend/tests/recommendation-submission.test.ts`，推荐提交前置校验与 payload 规范化已有单测保护
- `2026-04-09` 已新增 `apps/backend/app/services/_recommendations_candidates.py`、`_recommendations_result_builder.py` 与 `_recommendations_history.py`，推荐生成文件已进一步降为工作流编排层
- `2026-04-09` 已把 `tests/e2e/dashboard-smoke.spec.ts` 扩到 15 条流程，新增推荐历史空状态、多方案对比与失败回退回归
- `2026-04-09` 已执行 `./.venv/bin/pytest apps/backend/tests/test_recommendation_workflow.py`，1 个后端推荐工作流测试通过
- `2026-04-09` 已执行 `npm run test --workspace @local-edu/frontend -- --run tests/recommendation-submission.test.ts tests/recommendations-helpers.test.ts`，2 个前端测试文件共 6 个用例通过
- `2026-04-09` 已执行 `npm run frontend:build`，前端生产构建通过
- `2026-04-09` 已执行 `npm run e2e -- tests/e2e/dashboard-smoke.spec.ts`，当前 15 条 Playwright 跨端流程全部通过
- `2026-04-09` 已执行 `npm run test --workspace @local-edu/frontend -- --run tests/recommendations-helpers.test.ts`，当前推荐 helper 单测 4 条通过
- `2026-04-09` 已再次执行 `./.venv/bin/pytest apps/backend/tests/test_recommendation_workflow.py`，新增招生计划导入与省份规则配置回归通过
- `2026-04-09` 已再次执行 `npm run frontend:build`，高考志愿 S1 接线后的前端构建通过
- `2026-04-09` 已执行 `LOCAL_EDU_DB_PATH=/tmp/local_edu_tool_alembic_20260409.db ../../.venv/bin/alembic upgrade head`，新增 `20260409_0008` 迁移可正常升级
- `2026-04-07` 已新增年级视角多学年全景对比接口：`/api/analytics/grades/{grade_id}/panorama`
- `2026-04-07` 已新增 `apps/frontend/src/components/analytics/GradePanoramaPanel.vue`，并在分析中心接入“全景对比”标签页
- `2026-04-07` 已增强 E2E 测试后端种子，覆盖两学年考试趋势；已再次执行 `./.venv/bin/pytest apps/backend/tests/test_grade_analytics_and_student_attachments.py`、`npm run frontend:build`、`npm run e2e`，当前 12 条 Playwright 跨端流程通过
- `2026-04-07` 已新增 `apps/frontend/src/components/analytics/helpers.ts`、`types.ts` 与 `apps/frontend/tests/analytics-panorama-helpers.test.ts`，并把全景对比增强为洞察卡 + 时间轴 + 学科趋势看板
- `2026-04-07` 已继续增强 `GradePanoramaPanel.vue`，新增学科攻坚优先级与风险预警看板；已执行 `npm run frontend:lint`、`npm run frontend:test`、`npm run frontend:build`、`npm run e2e`，当前 16 个前端测试与 12 条 Playwright 流程通过
- `2026-04-07` 已新增班级视角全景对比接口：`/api/analytics/classes/{class_id}/panorama`，新增 `ClassPanoramaPanel.vue`，并在分析中心接入“班级全景”标签页；已执行 `./.venv/bin/pytest apps/backend/tests/test_grade_analytics_and_student_attachments.py`、`npm run frontend:lint`、`npm run frontend:test`、`npm run frontend:build`、`npm run e2e`，当前 16 个前端测试与 12 条 Playwright 流程通过
- `2026-04-07` 已新增教师视角全景对比接口：`/api/analytics/teachers/{teacher_id}/panorama`，新增 `TeacherPanoramaPanel.vue`，并在分析中心接入“教师全景”标签页；已执行 `./.venv/bin/pytest apps/backend/tests/test_grade_analytics_and_student_attachments.py`、`npm run frontend:lint`、`npm run frontend:test`、`npm run frontend:build`、`npm run e2e`，当前 16 个前端测试与 12 条 Playwright 流程通过
- `2026-04-07` 已新增 `apps/desktop` Electron 桌面壳、`apps/backend/app/desktop_entry.py` 桌面后端入口、桌面菜单和桌面打包脚本；已执行 `npm run desktop:prepare` 与 `npm run desktop:dist -- --dir`，当前已生成 `dist/desktop/mac/本地教务工具.app`，并补了 Windows `dir` / `nsis` 目标配置、首次启动提示和桌面内打印预览
