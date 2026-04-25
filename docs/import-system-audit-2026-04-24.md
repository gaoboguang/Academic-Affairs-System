# 导入体系审计与统一治理记录

- 日期：2026-04-24
- 执行窗口：窗口 2，统一导入中心与导入体验治理
- 范围：学生、教师、成绩、课表、录取数据、招生计划、评教与班主任量化模板
- 原则：不重写既有导入器，不删除模板，不覆盖导入历史；先统一状态、错误报告、批次摘要和前端反馈。
- 追加状态：同日已补只读“导入中心”，聚合模板、批次、错误报告、审计日志和撤销说明。

## 1. 现有导入入口盘点

| 导入类型 | 后端入口 | 前端入口 | 模板 | 错误报告 | 批次/审计 | 回滚/撤销 |
| --- | --- | --- | --- | --- | --- | --- |
| 学生信息 | `POST /api/students/import` | `StudentsPage.vue` | `students_import_template.xlsx` | `data/logs/student_import_errors*.xlsx` | `import_job` + audit log | 暂无专用回滚，需靠备份恢复 |
| 教师信息 | `POST /api/teachers/import` | `TeachersPage.vue` | `teachers_import_template.xlsx` | `data/logs/teacher_import_errors*.xlsx` | `import_job` + audit log | 暂无专用回滚，需靠备份恢复 |
| 成绩导入 | `POST /api/exams/{exam_id}/scores/import` | `ExamsPage.vue` | `exam_scores_import_template.xlsx` | `data/logs/score_import_errors*.xlsx` | `score_import_batch` + `import_job` + audit log | 暂无专用回滚；可用覆盖/跳过策略再导入 |
| 课表导入 | `POST /api/timetable/import` | `TimetableWorkloadPage.vue` | `timetable_import_template.xlsx` | `data/logs/timetable_import_errors*.xlsx` | `timetable_batch` + `import_job` + audit log | 暂无专用回滚；可停用旧批次并选最新有效批次 |
| 录取数据 | `POST /api/admissions/import` | `RecommendationsPage.vue` 录取库 | `admission_records_import_template.xlsx` | `data/logs/admissions_import_errors*.xlsx` | `import_job` + audit log | 暂无专用回滚，写库前应备份 |
| 招生计划 | `POST /api/enrollment-plans/import` | `RecommendationsPage.vue` 招生计划库 | `enrollment_plans_import_template.xlsx` | `data/logs/enrollment_plans_import_errors*.xlsx` | `import_job` + audit log | 暂无专用回滚，写库前应备份 |
| 评教数据 | `POST /api/evaluation/import` | `EvaluationQuantPage.vue` | `evaluation_import_template.xlsx` | `data/logs/evaluation_import_errors*.xlsx` | `evaluation_batch` + `import_job` + audit log | 暂无专用回滚 |
| 班主任量化 | 当前以模板和批量维护为主 | `EvaluationQuantPage.vue` | `adviser_quant_import_template.xlsx` | 未形成独立统一入口 | 量化记录表 | 暂无专用回滚 |

## 2. 本次统一的导入约定

### 2.1 统一状态

新的规范状态为：

- `pending`：待开始
- `running`：导入中
- `success`：全部成功
- `failed`：没有任何有效行导入
- `partially_failed`：部分成功、部分失败，或课表存在未匹配待修正项
- `rolled_back`：已回滚，当前预留

兼容旧状态：`processing -> running`、`partial_success -> partially_failed`、`completed -> success`、`completed_with_unresolved -> partially_failed`。前端展示通过 `importFeedback.ts` 统一格式化。

### 2.2 统一错误报告结构

错误报告现在统一输出：

```text
行号 / 列名 / 字段名 / 原始值 / 错误原因 / 建议修复 / 原模板字段...
```

这样非程序员用户不用只看“错误原因”，也能知道该改哪一列、原值是什么、建议怎么处理。

### 2.3 统一批次摘要

`ImportResult` 统一包含：

- `status`
- `total_rows`
- `success_rows`
- `failed_rows`
- `skipped_rows`
- `created_rows`
- `updated_rows`
- `error_report_path`
- `error_preview`
- `notice_preview`
- `message`

学生、教师、成绩、课表、录取数据、招生计划和评教入口都能复用这组字段。前端统一显示“总行数 / 成功 / 失败 / 跳过 / 新增 / 更新”。

## 3. 本次代码落点

后端：

- `apps/backend/app/importers/base.py`：新增统一状态、状态兼容映射、错误详情推断、错误报告标准列。
- `apps/backend/app/schemas/common.py`：扩展 `ImportResult` 字段。
- `apps/backend/app/importers/students.py`、`teachers.py`、`scores.py`、`timetable.py`：补 `status`、创建/更新计数、结构化错误预览。
- `apps/backend/app/importers/admissions.py`、`enrollment_plans.py`：补统一状态、错误预览和错误报告结构。
- `apps/backend/app/services/students.py`、`teachers.py`、`exams.py`、`workload.py`、`_evaluation_batches.py`、`_recommendations_catalog.py`、`_recommendations_plans.py`：导入任务状态改用统一状态；教师和课表导入补模板错误的 400 业务响应。
- `apps/backend/app/repositories/workload.py`：最新有效课表批次兼容新旧状态。

前端：

- `apps/frontend/src/utils/importFeedback.ts`：统一导入状态、标签、摘要、错误报告下载路径。
- `apps/frontend/src/components/common/ImportFeedbackPanel.vue`：统一导入结果展示。
- `StudentsPage.vue`、`TeachersPage.vue`、`ExamsPage.vue`、`WorkloadTimetablePanel.vue`、`RecommendationAdmissionsPanel.vue`、`RecommendationEnrollmentPlansPanel.vue`：接入统一反馈组件。
- `DashboardPage.vue`：最近导入列表兼容新状态和真实 job type。
- `apps/backend/app/services/system.py`、`apps/backend/app/api/routes/system.py`：新增 `/api/import-center/batches` 与 `/api/import-center/batches/{source_type}/{batch_id}`，聚合 `import_job`、`score_import_batch`、`timetable_batch`、`evaluation_batch`。
- `apps/frontend/src/pages/ImportCenterPage.vue`：新增“导入中心”页面，集中展示模板下载、业务上传入口、批次列表、批次详情、错误报告和撤销说明。
- `apps/frontend/src/router/index.ts`、`apps/frontend/src/layouts/navigation.ts`、`DashboardPage.vue`：接入 `/import-center` 导航与工作台入口。
- `apps/frontend/src/utils/importCenter.ts`：新增导入中心展示 helper。

测试：

- `apps/backend/tests/test_student_importer.py`：覆盖统一状态、创建计数和错误报告标准列。
- `apps/backend/tests/test_exam_workflow.py`：补成绩导入重复行和身份冲突两类错误场景。
- `apps/frontend/tests/import-feedback.test.ts`：覆盖统一状态格式化、摘要和错误报告下载路径。
- `apps/backend/tests/test_archive_and_system.py`：覆盖导入中心批次聚合与详情接口。
- `apps/frontend/tests/import-center.test.ts`：覆盖导入中心摘要、状态、错误报告和审计详情格式化。

## 4. 导入中心落地范围

- 已有 `/import-center` 页面，提供模板下载、进入对应业务页上传、批次列表、批次详情、错误报告下载、撤销说明和关联审计日志。
- 批次聚合当前覆盖 `import_job`、`score_import_batch`、`timetable_batch`、`evaluation_batch`；其中成绩、课表、评教会避免同一次导入在通用任务和专用批次中重复显示。
- 回滚能力明确保持为“提示与恢复路径”，不提供一键自动删除。原因是多数导入没有逐行 before-image 或影响范围快照，直接删批次可能误删后续手工修正和分析快照。
- 学生、教师、成绩、课表已有核心治理；评教已纳入批次中心，高考 raw 数据导入仍优先在 `/gaokao-data` 只读驾驶舱查看。
- “考试 / 考试科目创建”目前是表单维护，不是 Excel 导入；本轮把成绩导入作为考试链路的核心导入治理对象。
- 招生计划和录取数据会创建院校/专业，目前只统计创建数量，尚未细分 `updated_rows`。

## 5. 后续建议

1. 若要继续增强导入中心，优先补“原始上传文件留存与下载”，当前只保留来源文件名和错误报告。
2. 若要做真正批次回滚，先补每类导入的 before-image、影响行主键清单、备份强制校验和恢复后重算策略，再开放按钮。
3. 评教、班主任量化和高考 raw 数据若后续新增独立导入入口，应继续复用当前 `ImportResult` 和导入中心聚合约定。
