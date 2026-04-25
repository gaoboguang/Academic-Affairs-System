# 核心教务链路回归审计（2026-04-24）

- 执行窗口：窗口 5，核心教务链路回归与小修复
- 审计范围：学生、教师、班级 / 课程 / 任教、考试、成绩、分析、课表、工作量、报表
- 本轮原则：只做基础教务链路回归，不进入高考推荐、导入中心、Mac 启动或数据库补齐任务
- 当前结论：窗口 5 相关后端、前端单测、前端构建和定向 E2E 均通过；本轮未发现必须立即改代码的小修复项

## 1. 学生信息链路

### 当前链路

- 后端入口：`apps/backend/app/api/routes/students.py`
- 服务与导入：`apps/backend/app/services/students.py`、`apps/backend/app/importers/students.py`
- 前端入口：`apps/frontend/src/pages/StudentsPage.vue`、`apps/frontend/src/pages/StudentDetailPage.vue`
- 测试覆盖：`apps/backend/tests/test_student_importer.py`、`tests/e2e/dashboard-smoke.spec.ts`

### 已确认能力

- 学生列表、筛选、详情页和附件页可正常进入。
- 学生导入已返回成功、失败、跳过、提示预览和错误报告信息。
- 导入反馈组件已能承接学生导入的自动建班、未匹配年级、字典值待核对等提示。
- 学生基础字段已继续服务考试、分析、报表和高考志愿前置链路。

### 本轮判断

- 定向后端测试和 E2E 均通过，未发现学生中心当前有阻断性回归。
- 后续如果继续打磨，更适合补导入前字段映射和字典候选建议，不建议在窗口 5 大改学生模型或导入器。

## 2. 教师信息链路

### 当前链路

- 后端入口：`apps/backend/app/api/routes/teachers.py`
- 服务与导入：`apps/backend/app/services/teachers.py`、`apps/backend/app/importers/teachers.py`
- 前端入口：`apps/frontend/src/pages/TeachersPage.vue`、`apps/frontend/src/pages/TeacherDetailPage.vue`
- 关联链路：任教关系、教师分析、教师分析报表、课表工作量

### 已确认能力

- 教师列表、新增、编辑、导入导出和详情链路仍保留。
- 教师任教关系已被分析中心和报表链路消费。
- 教师分析打印预览已纳入定向 E2E。

### 本轮判断

- 窗口 5 定向验证未暴露教师链路失败。
- 教师导入反馈后续可继续向学生导入的友好提示对齐，但本轮没有发现需要立即修复的错误提示或 API 参数不一致。

## 3. 班级 / 课程 / 任教关系链路

### 当前链路

- 后端入口：`apps/backend/app/api/routes/base_data.py`、`apps/backend/app/api/routes/teachers.py`
- 服务：`apps/backend/app/services/base_data.py`、`apps/backend/app/services/teachers.py`
- 前端入口：`apps/frontend/src/pages/BaseDataPage.vue`、教师中心相关任教关系区域
- 消费方：考试成绩、分析中心、课表工作量、报表中心、推荐前置数据

### 已确认能力

- 学年、学期、年级、班级、科目、课程类型等基础字典仍作为共享事实来源。
- 任教关系继续支撑教师分析和教师报表。
- 考试科目配置依赖的学科字典已由考试主流程 E2E 覆盖。

### 本轮判断

- 不建议在窗口 5 为单一页面硬编码基础字典规则。
- 如果后续出现大面积 E2E 同时挂在考试、报表、推荐或工作量链路，应优先检查共享前置和基础数据种子。

## 4. 考试创建链路

### 当前链路

- 后端入口：`apps/backend/app/api/routes/exams.py`
- 服务与导入：`apps/backend/app/services/exams.py`、`apps/backend/app/importers/scores.py`
- 前端入口：`apps/frontend/src/pages/ExamsPage.vue`
- 前端 helper：`apps/frontend/src/components/exams/examSubjectConfig.ts`
- 测试覆盖：`apps/backend/tests/test_exam_workflow.py`、`apps/frontend/tests/exam-subject-config.test.ts`、`tests/e2e/dashboard-smoke.spec.ts`

### 已确认能力

- 考试新建、科目配置、成绩导入和跳转分析中心的主流程通过定向 E2E。
- 错误成绩模板会给出明确失败原因，不会退回泛化 500。
- 科目配置仍按“勾选学科 + 编辑满分 / 分数线 / 是否计总分”的现有交互工作。

### 本轮判断

- 考试链路当前稳定。
- 后续如果要做学生选科约束，应先正式建模学生选科字段，不应在前端按猜测限制科目。

## 5. 成绩导入与成绩快照链路

### 当前链路

- 后端服务：`apps/backend/app/services/exams.py`
- 成绩导入器：`apps/backend/app/importers/scores.py`
- 分析服务：`apps/backend/app/services/analytics.py`
- E2E fixture：`tests/e2e/fixtures/scores-import.xlsx`、`tests/e2e/fixtures/scores-invalid.xlsx`

### 已确认能力

- 正确成绩模板可导入并带到分析中心。
- 错误成绩模板会在页面给出明确失败提示。
- 成绩导入后的学生、班级、年级和教师分析仍可读取快照数据。

### 本轮判断

- 成绩导入与快照消费链路通过定向后端和 E2E 验证。
- 本轮不改导入器结构；如后续要扩展字段映射，应和导入中心窗口统一处理。

## 6. 分析中心链路

### 当前链路

- 后端入口：`apps/backend/app/api/routes/analytics.py`
- 服务：`apps/backend/app/services/analytics.py`
- 前端入口：`apps/frontend/src/pages/AnalyticsPage.vue`
- 前端组件：`apps/frontend/src/components/analytics`
- 测试覆盖：`apps/backend/tests/test_score_analytics.py`、`apps/backend/tests/test_grade_analytics_and_student_attachments.py`、`apps/frontend/tests/analytics-panorama-helpers.test.ts`

### 已确认能力

- 学生、班级、年级、教师分析链路仍可用。
- 多学年全景对比可展示两学年趋势。
- 班级 / 年级 / 教师分析打印预览可打开。
- 年级汇总导出口径继续复用后端分析服务，不在前端重算核心规则。

### 本轮判断

- 分析中心当前没有窗口 5 范围内的阻断回归。
- 后续应继续保持报表中心、打印页和 Excel 导出口径一致。

## 7. 课表导入、未匹配修正、工作量计算链路

### 当前链路

- 后端入口：`apps/backend/app/api/routes/workload.py`
- 服务：`apps/backend/app/services/workload.py`、`apps/backend/app/services/_workload_calculation.py`
- 导入器：`apps/backend/app/importers/timetable.py`
- 前端入口：`apps/frontend/src/pages/TimetableWorkloadPage.vue`
- 前端组件：`apps/frontend/src/components/workload`
- 测试覆盖：`apps/backend/tests/test_workload_workflow.py`

### 已确认能力

- 课表导入、未匹配项修正、规则版本维护、工作量计算和导出链路仍保留。
- 工作量打印预览已纳入窗口 5 定向 E2E。
- 后端工作量计算已拆到 `_workload_calculation.py`，页面侧已拆到组件和组合逻辑。

### 本轮判断

- 工作量链路通过后端定向测试和打印预览 E2E。
- 后续如果继续整理，应按“导入 / 规则 / 结果”继续收边界，不应重写计算引擎。

## 8. 报表导出链路

### 当前链路

- 后端入口：`apps/backend/app/api/routes/reports.py`
- 服务与导出：`apps/backend/app/services/reports.py`、`apps/backend/app/exporters`
- 前端入口：`apps/frontend/src/pages/ReportsPage.vue`
- 前端 helper：`apps/frontend/src/components/reports`
- 测试覆盖：`apps/frontend/tests/report-type-config.test.ts`、`apps/frontend/tests/report-insights.test.ts`、`apps/frontend/tests/report-insight-loader.test.ts`、`apps/frontend/tests/report-insight-presenter.test.ts`

### 已确认能力

- 学生分析单导出会写入导出记录。
- 班级、年级、教师分析打印预览可打开。
- 工作量、评教、班主任量化打印预览可打开。
- 缺少必填参数时会阻止导出。
- 报表类型配置、摘要 loader 和摘要 presenter 相关前端单测通过。

### 本轮判断

- 报表主链路通过窗口 5 定向验证。
- 本轮不进入窗口 6 的“报表、打印、Excel 导出一致性”专项；如后续要继续统一字段和风险说明，应单独按窗口 6 范围推进。

## 9. 本轮验证

### 已运行

```bash
npm run backend:test -- apps/backend/tests/test_student_importer.py apps/backend/tests/test_exam_workflow.py apps/backend/tests/test_score_analytics.py apps/backend/tests/test_grade_analytics_and_student_attachments.py apps/backend/tests/test_workload_workflow.py apps/backend/tests/test_recommendation_exporters.py -q
```

- 结果：`24 passed`

```bash
npm run frontend:test -- tests/import-feedback.test.ts tests/exam-subject-config.test.ts tests/report-type-config.test.ts tests/report-insights.test.ts tests/report-insight-loader.test.ts tests/report-insight-presenter.test.ts tests/analytics-panorama-helpers.test.ts
```

- 结果：`7 passed` test files，`38 passed` tests

```bash
npm run frontend:build
```

- 结果：通过

```bash
npm run e2e -- --grep "工作台冒烟|学生中心主流程|考试主流程|报表主流程|报表打印扩展|分析中心|考试异常提示|报表异常提示" tests/e2e/dashboard-smoke.spec.ts
```

- 结果：`9 passed`

### 未运行

- 本轮未跑完整 `npm run check:e2e`，因为窗口 4 已记录当前脏工作区整份 E2E 仍有非窗口 5 失败，集中在导入体验、推荐数据准备和默认生源地状态。
- 本轮未跑完整 `npm run check:all`，因为窗口 5 范围已有后端、前端、构建和定向 E2E 验证，且当前仓库存在多个并行窗口改动。

## 10. 后续建议

1. 如果继续基础教务链路，优先补教师导入反馈与学生导入反馈的一致性。
2. 如果多条 E2E 同时失败，先查 `tests/e2e/dashboard-smoke.spec.ts` 的共享 helper 和种子数据，不要直接分散修页面。
3. 工作量链路如继续整理，只拆 helper 和 UI 子域，不重写计算规则。
4. 报表字段和打印 / Excel 一致性应交给窗口 6，不在窗口 5 继续扩大范围。
5. 导入中心、推荐解释和高考数据缺口属于其它窗口，本轮只记录它们可能影响全量 E2E，不顺手修改。
