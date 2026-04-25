# 第四轮 E0 基线审计：学生批量操作、批量调班与数据库补齐

- 日期：2026-04-26
- 执行窗口：E0，第四轮基线审计
- 当前分支：`codex/r4-e0-baseline-audit`
- 基线提交：`169fd5d feat: finalize round 3 pathway integration`
- 范围：只审计现状并生成后续窗口入口，不开发新功能、不修改业务代码、不执行 `git push`

## 1. 审计结论

第四轮可以在第三轮已完成的山东升学方案中心基础上继续推进。当前 main 已包含第三轮 D8 成果，`/gaokao-pathways`、学生详情“升学画像”、路径报告打印/Excel 和高考数据健康检查均存在。

本轮最主要的真实缺口在学生基础管理侧：

1. 学生列表页没有批量选择、批量删除或批量调班入口。
2. 后端学生接口没有单个学生删除接口，也没有批量删除预检/执行接口。
3. 学生模型已有 `is_active` 软删除字段，但学生列表查询当前没有默认排除停用学生。
4. 已有 `student_class_history` 学籍/班级历史表，但只记录学生当前班级变更后的历史段，没有调班批次、逐学生调班结果、来源班级、目标班级、生效日期、原因和备注的完整审计结构。
5. 成长档案当前只读取人工成长记录，不能聚合调班这类系统事件。
6. 数据库补齐仍保留 6 条 P0 数据缺口，必须继续走官方来源登记、导入批次和健康检查，不得伪造 2026 未发布数据。

## 2. 当前真实文件路径

### 学生列表和详情

- `apps/frontend/src/pages/StudentsPage.vue`
  - 当前能力：学生筛选、模板下载、Excel 导出、新增学生、编辑学生、导入学生、进入详情。
  - 当前缺口：`el-table` 没有 `selection` 列；没有选中学生状态；没有“批量操作 / 批量删除 / 批量调班”按钮。
- `apps/frontend/src/pages/StudentDetailPage.vue`
  - 当前能力：基础信息、学籍历史、成绩摘要、成长档案、推荐记录、升学画像、附件。
  - 当前缺口：没有专门调班历史接口数据；成长档案标签只展示人工成长记录摘要。
- `apps/frontend/src/pages/GrowthArchivePage.vue`
  - 当前能力：按学生维护成长记录，支持记录类型筛选、附件、导出摘要、打印预览。
  - 当前缺口：没有“班级调整”系统事件类型；没有把调班历史聚合进时间线。
- `apps/frontend/src/components/students/StudentPathwayProfilePanel.vue`
- `apps/frontend/src/components/students/studentPathwayProfile.ts`
  - 第三轮学生升学画像入口已存在，第四轮不要重写。

### 后端学生、成长档案和审计

- `apps/backend/app/api/routes/students.py`
  - 当前接口：`GET /api/students`、`POST /api/students`、`GET /api/students/{id}`、`PUT /api/students/{id}`、导入、导出、附件、职业意向和学生 profile。
  - 当前缺口：没有 `DELETE /api/students/{id}`，没有 `POST /api/students/bulk-delete/preview`，没有 `POST /api/students/bulk-delete`，没有 `POST /api/students/class-transfer/preview`，没有 `POST /api/students/class-transfer`，没有 `GET /api/students/{id}/class-transfer-history`。
- `apps/backend/app/services/students.py`
  - 当前 `create_student()` / `update_student()` 会写 `audit_log`。
  - `_apply_student_payload()` 会同步 `current_grade_id`、`current_class_id`、`status`、`student_type`、`art_track`、`origin_province` 和 `is_active`。
  - `_update_class_history()` 会在班级变化时关闭当前开放历史并新增一条 `StudentClassHistory`，但原因固定为“系统维护”，生效日期固定为当天，没有批次号和逐学生结果。
- `apps/backend/app/repositories/students.py`
  - 当前列表查询支持学号、姓名、年级、班级、状态、学生类别、艺体方向。
  - 当前缺口：没有默认 `Student.is_active == True` 过滤，也没有批量删除或调班专用查询。
- `apps/backend/app/models/student.py`
  - 已有 `Student`、`StudentGuardian`、`StudentClassHistory`、`StudentAttachment`、`StudentCareerPreference`。
  - `Student` 继承 `ActiveMixin`，具备 `is_active` 字段，可作为软删除底座。
  - `StudentClassHistory` 字段为 `student_id / grade_id / class_id / start_date / end_date / reason`，不足以单独承载第四轮要求的调班批次与调班明细。
- `apps/backend/app/schemas/student.py`
  - 已有 `StudentPayload`、`StudentRead`、`StudentClassHistoryRead`、`StudentProfileRead`。
  - 当前缺口：没有批量删除预检/执行 schema，也没有调班预检/执行/历史 schema。
- `apps/backend/app/api/routes/archives.py`
  - 当前接口：`GET /api/archives/students/{student_id}/records`、新增/编辑/删除成长记录、导出成长摘要。
- `apps/backend/app/services/archive.py`
  - 成长记录新增、更新、删除、导出均写入审计日志。
  - 当前缺口：`list_growth_records()` 只返回 `student_growth_record`，没有聚合系统事件。
- `apps/backend/app/models/archive.py`
  - `StudentGrowthRecord` 当前是人工成长记录表，不应把调班记录伪装成人工记录直接混写。
- `apps/backend/app/models/system.py`
  - 已有 `AuditLog`、`ImportJob`、`ReportExportRecord`，批量删除和调班执行应继续复用 `audit_log`。

### 关联数据入口

批量删除预检需要统计的关联数据入口：

- 成绩：`apps/backend/app/models/exam.py`
  - `ScoreRecord`、`ScoreTotalSnapshot`、`ScoreSubjectSnapshot` 均关联 `student_id`。
- 成长档案：`apps/backend/app/models/archive.py`
  - `StudentGrowthRecord.student_id`。
- 附件：`apps/backend/app/models/student.py`
  - `StudentAttachment.student_id`。
- 学籍/班级历史：`apps/backend/app/models/student.py`
  - `StudentClassHistory.student_id`。
- 推荐历史和志愿草稿：`apps/backend/app/models/recommendation.py`
  - `RecommendationResult.student_id`、`VolunteerDraft.student_id`。
- 升学画像和路径评估：`apps/backend/app/models/recommendation.py`
  - `StudentPathwayProfile.student_id`、`StudentPathwayEvaluation.student_id`。

## 3. 已有能力

### 学生中心

- 可分页查询学生列表。
- 可按学号、姓名、年级、班级筛选。
- 可下载学生导入模板。
- 可导入学生，导入策略包括跳过已存在、更新已有记录、仅新增。
- 可导出学生列表。
- 可新增和编辑学生。
- 可进入学生详情。

### 学生详情

- 已展示学生基础信息、家庭联系人、当前班级、学生状态、学生类别、艺体方向、生源地。
- 已展示学籍历史，数据来自 `StudentProfileRead.class_histories`。
- 已展示最近考试趋势、成长档案摘要、推荐记录、升学画像和附件。
- 已接入第三轮 `StudentPathwayProfilePanel`，可维护山东升学画像。

### 成长档案

- 可按学生维护奖励、处分、活动、干部任职、谈话、家校沟通、心理关注、综合素质评价和其他记录。
- 支持附件上传、档案摘要导出和打印预览。
- 人工成长记录删除采用 `is_active=False`，并写审计日志。

### 第三轮升学路径

- 当前 main 最新提交已包含第三轮 D8：山东升学路径字典、学生升学画像、三态规则评估、方案中心、路径报告打印和 Excel 导出。
- 当前数据健康检查显示 `schema_version=20260425_0018`，说明第三轮路径表迁移已经在主库中。
- `/gaokao-pathways` 只做资格初筛、材料缺口和普通类推荐入口，仍保持“不把特殊路径包装成录取概率”的边界。

## 4. 缺失能力

### 学生批量删除

- 前端没有表格多选。
- 前端没有批量删除入口。
- 后端没有单个学生删除接口。
- 后端没有批量删除预检和执行接口。
- 没有“确认删除 X 名学生”这类二次确认机制。
- 没有批量删除结果清单。
- 没有批量删除专用审计结构。
- `Student.is_active` 虽然存在，但当前列表查询没有默认过滤停用学生，E1 需要明确软删除后列表如何隐藏或如何筛选。

### 批量调班和调班历史

- 前端没有批量调班入口和弹窗。
- 后端没有调班预检、执行和历史查询接口。
- 现有 `StudentClassHistory` 只能表示班级历史段，不能表示调班批次和逐学生调班结果。
- 现有更新学生接口会在班级变化时写“系统维护”原因，不满足“调班原因 / 备注 / 来源班级 / 目标班级 / 生效日期 / 操作批次”的要求。
- 成长档案没有调班系统事件聚合。

### 数据库补齐

`npm run backend:data-health -- --json` 当前结论：

- 主库：`data/app.db`
- 生成时间：`2026-04-26 07:37:50`
- schema：`20260425_0018`
- 总结：核心表缺失 0 个，空表 0 个，需关注表 2 个，P0 缺口 6 条。

当前 6 条 P0 缺口：

1. 特殊类型已有招生计划但缺专门录取结果：春季高考、艺术类、体育类、单独招生、综合评价招生。
2. 山东招生计划 2024 年数量偏少：592 条，需继续核验完整性。
3. 一分一段缺少年份：2020、2021、2022。
4. 省控线 / 批次线缺少年份：2020、2021、2022。
5. 政策参考数量偏少：4 条，交付前需补山东官方政策和填报规则。
6. 招生章程限制链仍有 1748 条待人工复核。

## 5. 本轮建议修改范围

### E1 建议范围：学生批量删除后端

- 新增批量删除 schema、service、route 和测试。
- 优先复用 `Student.is_active` 做软删除。
- 预检只统计影响，不修改关联数据。
- 执行只停用学生主档，不删除成绩、成长档案、附件、推荐记录、志愿草稿、升学画像和路径评估。
- 同步明确学生列表默认是否只返回启用学生；如改变默认行为，需要保留 `include_inactive` 或等价查询能力。
- 建议新增批量操作审计表或至少写入结构化 `audit_log.detail_json`。

### E2 建议范围：学生批量删除前端

- 只改 `StudentsPage.vue` 和必要的测试 / helper。
- 增加表格多选、批量操作区、删除预检弹窗和确认文字。
- 删除成功后刷新列表。
- 不碰学生详情、成长档案和升学画像。

### E3 建议范围：批量调班后端

- 复用现有 `StudentClassHistory` 作为学生详情“学籍历史”的展示底座。
- 新增 `student_class_transfer_batch` 和 `student_class_transfer_item` 更适合满足批次审计、逐学生结果、来源班级、目标班级、生效日期、原因和备注。
- 执行调班时同时更新 `Student.current_grade_id/current_class_id`、刷新班级人数、写调班批次和明细、必要时写 `StudentClassHistory`。
- 新增 `GET /api/students/{student_id}/class-transfer-history` 给 E4 展示系统事件。

### E4 建议范围：批量调班前端和成长档案展示

- 学生列表增加批量调班入口。
- 学生详情增加更明确的调班历史展示。
- 成长档案时间线聚合调班系统事件，不直接写入人工 `student_growth_record`。
- E2 和 E4 都会改 `StudentsPage.vue`，不建议并行硬合并；若必须并行，先约定多选状态和批量操作工具条的共享结构。

### E5-E7 建议范围：数据库补齐

- E5 只做补齐审计和官方来源计划，不大规模写库。
- E6 执行可补数据导入，导入前必须备份，导入后必须跑 data-health 和 p0-check。
- E7 把补齐结果做成非程序员可读的页面和文档。

## 6. 不建议修改的模块

- 不建议在 E1-E4 中修改第三轮高考路径核心：
  - `apps/backend/app/services/gaokao_pathways.py`
  - `apps/backend/app/api/routes/gaokao.py`
  - `apps/frontend/src/pages/GaokaoPathwaysPage.vue`
  - `apps/frontend/src/components/gaokao-pathways/pathwayCenter.ts`
  - `apps/frontend/src/components/students/StudentPathwayProfilePanel.vue`
- 不建议在 E1-E4 中修改山东普通类推荐、志愿草稿和报表导出核心：
  - `apps/frontend/src/pages/RecommendationsPage.vue`
  - `apps/backend/app/services/recommendations.py`
  - `apps/backend/app/exporters/recommendations.py`
  - `apps/backend/app/services/reports.py`
- E0 不修改 `data/app.db`，E5 也不应直接替换主库。
- 不建议在 E0-E4 修改 `package.json`、`README.md`、`AGENTS.md` 和 `.rulesync/`，除非最终集成窗口统一整理。

## 7. 后续窗口依赖关系

| 窗口 | 目标 | 依赖 | 高冲突文件 | 建议顺序 |
| --- | --- | --- | --- | --- |
| E1 | 学生批量删除后端 | E0 | `students.py` route/service/schema/model 测试 | 先做 |
| E2 | 学生批量删除前端 | E1 | `apps/frontend/src/pages/StudentsPage.vue` | E1 后做 |
| E3 | 批量调班后端与历史 | E0 | 学生模型、迁移、`students.py` route/service/schema 测试 | 可与 E1 分支级并行，但合并前需处理同模块冲突 |
| E4 | 批量调班前端与成长档案展示 | E3 | `StudentsPage.vue`、`StudentDetailPage.vue`、`GrowthArchivePage.vue` | E3 后做；和 E2 高冲突 |
| E5 | 数据库补齐审计与数据源计划 | E0 | data-health、gaokao import docs/scripts | 可与 E1/E3 并行 |
| E6 | 数据库补齐导入执行 | E5 | `data/app.db`、导入脚本、source/import run | E5 后做 |
| E7 | 数据健康、报表和使用说明 | E6 | `GaokaoDataPage.vue`、docs | E6 后做 |
| E8 | 第四轮最终集成、测试、交接 | E1-E7 | memory-bank、docs/README、最终报告 | 最后做 |

关键冲突提醒：

- E2 和 E4 都会改学生列表页，尽量串行。
- E1 和 E3 都会改后端学生 route/service/schema，尽量以 E1 的批量操作结构作为共享基础，E3 接着扩展调班。
- E5-E7 不应改学生批量操作代码，保持数据补齐线独立。

## 8. 推荐测试命令

### E0 当前验证

```bash
git status
npm run backend:data-health -- --json
git diff --check
```

### E1 / E3 后端窗口

```bash
npm run backend:migrate
npm run backend:test -- apps/backend/tests -q
git diff --check
```

如只跑学生相关定向测试，可先补并执行：

```bash
npm run backend:test -- apps/backend/tests/test_student_importer.py apps/backend/tests/test_grade_analytics_and_student_attachments.py -q
```

### E2 / E4 前端窗口

```bash
npm run frontend:test
npm run frontend:build
git diff --check
```

如果新增学生列表 helper 测试，优先定向跑对应测试文件，再跑全量前端测试。

### E5 / E6 / E7 数据补齐窗口

```bash
npm run backend:data-health -- --json
npm run backend:p0-check -- --json
npm run backend:test -- apps/backend/tests -q
npm run frontend:build
git diff --check
```

E6 写主库前必须先备份，且不能伪造未发布的 2026 普通类正式计划、一分一段、省控线或录取结果。

### E8 最终集成

```bash
git status
npm run backend:migrate
npm run backend:data-health -- --json
npm run backend:p0-check -- --json
npm run check
npm run check:all
git diff --check
```

## 9. E1-E8 真实入口清单

### E1：批量删除后端

- `apps/backend/app/api/routes/students.py`
- `apps/backend/app/services/students.py`
- `apps/backend/app/repositories/students.py`
- `apps/backend/app/models/student.py`
- `apps/backend/app/schemas/student.py`
- `apps/backend/app/models/exam.py`
- `apps/backend/app/models/archive.py`
- `apps/backend/app/models/recommendation.py`
- `apps/backend/app/models/system.py`
- `apps/backend/tests/`

### E2：批量删除前端

- `apps/frontend/src/pages/StudentsPage.vue`
- `apps/frontend/src/api/client.ts`
- `apps/frontend/tests/`

### E3：批量调班后端

- `apps/backend/app/api/routes/students.py`
- `apps/backend/app/services/students.py`
- `apps/backend/app/repositories/students.py`
- `apps/backend/app/models/student.py`
- `apps/backend/app/schemas/student.py`
- `apps/backend/alembic/versions/`
- `apps/backend/tests/`

### E4：批量调班前端和成长档案展示

- `apps/frontend/src/pages/StudentsPage.vue`
- `apps/frontend/src/pages/StudentDetailPage.vue`
- `apps/frontend/src/pages/GrowthArchivePage.vue`
- `apps/frontend/tests/`

### E5-E7：数据库补齐

- `apps/backend/app/utils/data_health.py`
- `apps/backend/app/services/gaokao_imports.py`
- `apps/backend/app/services/gaokao_official_importers.py`
- `scripts/check_data_health.py`
- `scripts/import_gaokao_official.py`
- `scripts/import_shandong_gaokao_core_data.py`
- `scripts/manage_gaokao_sources.py`
- `apps/frontend/src/pages/GaokaoDataPage.vue`
- `docs/round3-shandong-pathway-final-report.md`
- `docs/round2-gaokao-recommendation-final-report.md`
- `docs/gaokao-data-coverage-after-round2.md`

### E8：最终集成

- `docs/round4-final-acceptance-report.md`
- `memory-bank/active-context.md`
- `memory-bank/handoff.md`
- `memory-bank/progress.md`
- `docs/README.md`
- `README.md` 视最终说明需要决定是否更新。

## 10. E0 验证记录

E0 已执行：

```bash
git status
npm run backend:data-health -- --json
git diff --check
```

当前结论：

- `git status`：生成本审计文档后，工作区只出现审计文档和 `memory-bank` 交接记录改动；未修改业务代码。
- `backend:data-health`：通过，`schema_version=20260425_0018`，状态为 `warning`，P0 缺口 6 条。
- `git diff --check`：已通过，无空白或补丁格式问题。
