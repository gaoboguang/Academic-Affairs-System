# E2E 测试说明

根目录 `tests/e2e` 只放跨端 Playwright 测试，后端单测继续放 `apps/backend/tests`，前端单测继续放 `apps/frontend/tests`。

## 分域文件

- `dashboard.spec.ts`：首页工作台主流程。
- `students.spec.ts`：学生列表、学生详情和附件入口。
- `exams-analytics.spec.ts`：考试、成绩导入、分析中心和成绩异常提示。
- `adviser-dashboard.spec.ts`：成绩、成长档案、规划任务驱动的班主任驾驶舱、学生详情和班主任周报闭环。
- `planning.spec.ts`：学生升学规划目标、路径生成任务、任务完成和规划跟进表闭环。
- `reports.spec.ts`：报表参数、打印预览、导出记录和报表异常提示。
- `recommendations.spec.ts`：推荐生成、历史、模板、对比、失败回退和批量推荐。
- `gaokao-volunteer.spec.ts`：学生志愿工作台、招生计划、省份规则、草稿、就业方向和山东普通类入口。
- `system-backup.spec.ts`：系统设置、备份创建和备份恢复入口。
- `helpers/localEduE2e.ts`：跨域复用的测试前置、下拉选择、导入 fixture 和推荐/志愿工作台 helper。

## 常用命令

```bash
npm run check:e2e
npm run e2e -- tests/e2e/reports.spec.ts
npm run e2e -- tests/e2e/recommendations.spec.ts -g "推荐主流程"
```

`npm run check:all` 会先跑常规质量门禁，再运行整个 `tests/e2e` 目录。若只改某个业务域，可先跑对应 spec 文件，最后按改动风险决定是否跑全量。

## Fixtures

`tests/e2e/fixtures` 下的 Excel 文件用于通过 API 或页面导入稳定测试数据：

- `scores-import.xlsx`：有效成绩导入模板。
- `scores-invalid.xlsx`：错误成绩模板，用于导入失败提示。
- `admissions-import.xlsx`：广东录取库样例。
- `admissions-cross-province.xlsx`：山东 / 河北混合生源地推荐样例。
- `enrollment-plans-import.xlsx`：广东招生计划样例。
这些 fixture 是测试资产，不代表真实学校数据或正式高考数据。
