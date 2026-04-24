# 当前开发地图（2026-04-24）

- 执行窗口：窗口 0
- 文档来源：按 `docs/Codex-App-基于仓库的后续开发执行文档-v3.md` 补齐指定 dated 开发地图
- 去重说明：已有窗口 0 已生成 `docs/repo-audit.md`、`docs/mac-dev-setup.md`、`docs/development-roadmap.md`；本文只补 v3 要求的“当前业务模块地图”

## 1. 学生、教师、班级、课程、任教关系现状

### 学生

- 主要后端：`apps/backend/app/api/routes/students.py`、`apps/backend/app/services/students.py`、`apps/backend/app/importers/students.py`
- 主要前端：`apps/frontend/src/pages/StudentsPage.vue`、`apps/frontend/src/pages/StudentDetailPage.vue`
- 当前能力：
  - 学生列表、详情、新增、编辑
  - Excel 导入、导出、模板下载
  - 学生成长档案、附件、职业意向
  - 学生导入已补 `notice_preview`，能提示自动建班、未匹配年级、字典值待核对
  - 学生档案已包含生源地字段，推荐 / 志愿可回退读取
- 后续重点：
  - 继续优化导入前字段映射和字典候选建议
  - 不要用姓名作为唯一身份键；优先学号 / 学籍号

### 教师

- 主要后端：`apps/backend/app/api/routes/teachers.py`、`apps/backend/app/services/teachers.py`
- 主要前端：`apps/frontend/src/pages/TeachersPage.vue`、`apps/frontend/src/pages/TeacherDetailPage.vue`
- 当前能力：
  - 教师列表、详情、新增、编辑、导入导出
  - 职称、任教关系、教师分析相关链路已存在
- 后续重点：
  - 导入错误提示可继续向学生导入的友好反馈对齐
  - 教师身份匹配应优先工号

### 班级、课程、基础字典

- 主要后端：`apps/backend/app/api/routes/base_data.py`、`apps/backend/app/services/base_data.py`
- 主要前端：`apps/frontend/src/pages/BaseDataPage.vue`
- 当前能力：
  - 学年、学期、年级、班级、科目、课程类型、学生类别等基础数据管理
  - 成绩、课表、推荐、工作量等模块依赖这些字典
- 后续重点：
  - 避免为了单个导入器硬编码字典规则
  - 基础数据变更必须兼顾考试、成绩、任教、推荐前置

### 任教关系

- 主要后端：`teachers.py`、`analytics.py`、相关 schema/model
- 主要前端：教师中心、分析中心相关页面
- 当前能力：
  - 任教关系维护和历史分析已接入成绩分析、教师分析、报表
- 后续重点：
  - 回归时要覆盖“教师任教 -> 考试成绩 -> 教师分析 -> 报表”

## 2. 考试、成绩、分析、报表现状

### 考试和成绩

- 主要后端：`apps/backend/app/api/routes/exams.py`、`apps/backend/app/services/exams.py`
- 主要前端：`apps/frontend/src/pages/ExamsPage.vue`
- 当前能力：
  - 考试列表、详情、新增、编辑
  - 考试科目配置
  - 成绩 Excel 导入、错误报告、导入批次
  - E2E 已覆盖考试到分析的核心前置链路
- 后续重点：
  - 继续保持错误成绩模板返回业务级错误，不要退回 500
  - 如果多条 E2E 同时挂，先查 `tests/e2e/dashboard-smoke.spec.ts` 的共享前置 helper

### 分析中心

- 主要后端：`apps/backend/app/api/routes/analytics.py`、`apps/backend/app/services/analytics.py`
- 主要前端：`apps/frontend/src/pages/AnalyticsPage.vue`、`apps/frontend/src/components/analytics`
- 当前能力：
  - 学生、班级、年级、教师分析
  - 年级、班级、教师全景对比
  - 学科攻坚优先级和风险预警类看板
- 后续重点：
  - 分析口径应继续复用后端服务，不要在前端硬算核心业务规则
  - 继续保持打印页、报表中心和 Excel 导出口径一致

### 报表中心

- 主要后端：`apps/backend/app/api/routes/reports.py`、`apps/backend/app/services/reports.py`、`apps/backend/app/exporters`
- 主要前端：`apps/frontend/src/pages/ReportsPage.vue`、`apps/frontend/src/components/reports`
- 当前能力：
  - 学生、班级、年级、教师、工作量、评教、量化、成长档案、推荐、志愿草稿等报表导出
  - 多类打印预览页已存在
  - 推荐报告和志愿草稿导出前摘要、打印页、Excel 风险说明已逐步统一
- 后续重点：
  - 不要给报表中心另起一套解释文案，应继续复用现有 helper / exporter 口径

## 3. 课表、工作量现状

- 主要后端：`apps/backend/app/api/routes/workload.py`、`apps/backend/app/services/workload.py`、`apps/backend/app/services/_workload_calculation.py`
- 主要前端：`apps/frontend/src/pages/TimetableWorkloadPage.vue`、`apps/frontend/src/components/workload`
- 当前能力：
  - 课表导入
  - 未匹配项修正
  - 工作量规则维护
  - 工作量计算和导出
  - 工作量打印预览
- 当前结构：
  - 页面已拆为组件和组合逻辑，后端计算也有独立 helper
- 后续重点：
  - 如果继续拆分，按“导入 / 规则 / 结果”继续收边界
  - 不要在没有测试保护的情况下重写工作量计算

## 4. 成长档案、评教、量化现状

### 成长档案

- 主要前端：`apps/frontend/src/pages/GrowthArchivePage.vue`、`GrowthSummaryPrintPage.vue`
- 当前能力：
  - 学生成长档案维护
  - 摘要打印预览和报表链路
- 后续重点：
  - 与学生详情、报表中心保持入口一致

### 评教

- 主要后端：`apps/backend/app/api/routes/evaluation.py`、`apps/backend/app/services/evaluation.py`、`_evaluation_*`
- 主要前端：`apps/frontend/src/pages/EvaluationQuantPage.vue`、`apps/frontend/src/components/evaluation`
- 当前能力：
  - 评教模板
  - 评教批次导入 / 汇总
  - 教师趋势
  - 评教汇总打印和报表
- 当前结构：
  - 后端 `evaluation.py` 是 facade，内部已拆模板、批次、统计、班主任量化
  - 前端已拆组件和组合逻辑
- 后续重点：
  - 如继续处理 `useEvaluationQuantPage.ts`，按“模板 / 批次分析 / 量化规则 / 量化记录”继续细分

### 班主任量化

- 主要后端：`_evaluation_adviser_quant.py`
- 主要前端：`EvaluationQuantPage.vue`、`AdviserQuantPrintPage.vue`
- 当前能力：
  - 量化规则、记录、汇总、打印预览
- 后续重点：
  - 规则变更应保持后端为事实来源

## 5. 推荐中心、高考志愿、数据健康现状

### 推荐中心 / 高考志愿

- 主要后端：`apps/backend/app/api/routes/recommendations.py`、`apps/backend/app/services/recommendations.py`、`_recommendations_*`
- 主要前端：`apps/frontend/src/pages/RecommendationsPage.vue`、`apps/frontend/src/components/recommendations`
- 当前能力：
  - 院校库、专业库、录取库、招生计划
  - 普通生 / 特殊类型推荐
  - 省份规则、特殊类型规则、赋分规则、选科字典
  - 学生志愿工作台、草稿保存、草稿打印 / 导出
  - 职业方向、专业就业映射、职业意向、职业匹配解释
  - 推荐历史、策略模板、对比、报告导出
- 当前关键边界：
  - 普通类推荐可走位次 / 分数参考
  - 特殊类型当前只能安全初筛，不能包装成录取把握
  - `score_line_reference_only`、`plan_only_reference`、`fallback_priority_*` 都是核看顺序和风险提示，不是录取概率
- 后续重点：
  - 山东普通类真实样例验收
  - 特殊类型三端一致：页面、打印、Excel 都保持初筛说明
  - 规则编辑维护补齐，但不要把规则重新硬编码到前端

### 高考数据驾驶舱

- 主要后端：`apps/backend/app/api/routes/gaokao.py`、`apps/backend/app/services/gaokao.py`、`apps/backend/app/utils/data_health.py`
- 主要前端：`apps/frontend/src/pages/GaokaoDataPage.vue`
- 当前能力：
  - 数据总览
  - 山东覆盖页签
  - 覆盖矩阵
  - 导入审计摘要
  - 数据审阅
  - 院校证据页
  - 山东监控
- 当前真实缺口：
  - 特殊类型专门录取结果缺失
  - 山东招生计划 2021-2023 缺失，2024 数量偏少
  - 一分一段缺 2020-2023
  - 省控线 / 批次线缺 2020-2023
  - 政策参考偏少
  - 章程限制链仍有大量待人工复核
- 后续重点：
  - 优先补真实数据源或导入器，不要重复做同一层看板
  - 页面必须继续解释“缺口”和“初筛”，不能只显示零或静默 fallback

### P0 数据健康与交付验收

- 命令入口：
  - `npm run backend:data-health`
  - `npm run backend:data-health -- --json`
  - `npm run backend:p0-check`
  - `npm run backend:p0-check -- --json`
- 当前能力：
  - 核心表数量
  - 山东年份、类别、批次覆盖
  - P0 缺口摘要
  - SQLite 完整性检查
  - 备份包生成和结构校验
  - 临时恢复和恢复后接口检查
- 后续重点：
  - 交付前窗口必须重新跑 P0 验收

## 6. Mac 启动、测试、打包现状

### Mac 启动

- 统一命令：`npm run dev`
- 双击入口：`start-local-edu.command`
- 后端默认：`http://127.0.0.1:8000`
- 前端默认：`http://127.0.0.1:5173`
- API 文档：`http://127.0.0.1:8000/docs`
- 当前已有文档：`docs/mac-dev-setup.md`
- 后续窗口 1 应继续：
  - 复核从零安装
  - 优化非程序员启动说明
  - 检查端口预检、路径、可执行位、失败提示

### 测试

- 后端：`npm run backend:test`
- 前端 lint：`npm run frontend:lint`
- 前端单测：`npm run frontend:test`
- 前端构建：`npm run frontend:build`
- E2E：`npm run check:e2e`
- 全量检查：`npm run check`、`npm run check:all`

当前测试布局：

- 后端测试：`apps/backend/tests`
- 前端测试：`apps/frontend/tests`
- E2E：`tests/e2e/dashboard-smoke.spec.ts`
- E2E fixture：`tests/e2e/fixtures`

### 打包

- 桌面准备：`npm run desktop:prepare`
- macOS 产物：`npm run desktop:dist:mac`
- Windows 目录产物：`npm run desktop:dist:win:dir`
- Windows NSIS：`npm run desktop:dist:win:nsis`

当前窗口 0 不重新做桌面打包验收。后续交付窗口应在最终代码稳定后再跑桌面包，避免中途反复生成大体积产物。

## 7. 后续并行建议

1. 窗口 1：Mac 启动体验和普通用户文档，可以和只读页面小改并行
2. 窗口 2：数据库 / 数据模型 / 补数据链路，必须避开其它窗口的迁移和主库写入
3. 窗口 3：前端只读核对和数据页体验，若窗口 2 正在改接口 schema，窗口 3 应等待或只做纯展示
4. 窗口 9：最终测试、验收、文档和清理，应在功能窗口之后执行
5. 窗口 10：冲突检查和最终交付建议，最后执行
