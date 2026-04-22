# 测试目录约定

- `apps/backend/tests`：后端单元测试、接口测试和工作流回归测试的主入口
- `tests/e2e`：当前已落地 Playwright 跨端流程，默认启动临时演示数据后端和 Vite 前端；`dashboard-smoke.spec.ts` 现有 30 条流程，覆盖工作台导航、学生详情、系统备份、考试到分析、推荐生成/导出、多方案对比、策略模板、历史回放、Stage B 主链路、批量混合生源地、缺少年份规则解释、模式兼容回退、高考志愿主流程、报表与打印预览，以及多条异常提示回归
- `tests/e2e/fixtures`：稳定复用的 Excel 导入样例，当前包含成绩导入、错误成绩模板、录取导入、跨省录取导入 4 份 fixture
- 前端单元测试位于 `apps/frontend/tests`

## 2026-04-16 定向回归

- P0 安全边界：`./.venv/bin/pytest apps/backend/tests/test_archive_and_system.py -q`
- 高考只读驾驶舱：`./.venv/bin/pytest apps/backend/tests/test_archive_and_system.py apps/backend/tests/test_gaokao_api.py -q`
- Stage B 推荐解释入参统一：`npm run test --workspace @local-edu/frontend -- --run tests/report-insight-recommendation.test.ts tests/report-insight-presenter.test.ts tests/recommendation-output-guards.test.ts`
- 分析/导出摘要统一：`./.venv/bin/pytest apps/backend/tests/test_exam_workflow.py apps/backend/tests/test_grade_analytics_and_student_attachments.py -q`
- 高复杂模块小步拆分：
  - `npm run test --workspace @local-edu/frontend -- --run tests/volunteer-workbench.test.ts tests/report-insight-presenter.test.ts`
  - `./.venv/bin/pytest apps/backend/tests/test_evaluation_quant_workflow.py -q`
  - `./.venv/bin/pytest apps/backend/tests/test_workload_workflow.py -q`
  - `npm run build --workspace @local-edu/frontend`
- 推荐历史对照年份边界继续细化：
  - `npm run test --workspace @local-edu/frontend -- --run tests/recommendation-comparison.test.ts`
  - `./.venv/bin/pytest apps/backend/tests/test_recommendation_exporters.py -q`
  - `npm run build --workspace @local-edu/frontend`
