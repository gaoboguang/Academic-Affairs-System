# 测试体系与质量门禁审计

- 文件名日期沿用 Codex App v3 窗口 8 要求：2026-04-24
- 执行分支：`codex/08-quality-gates`
- 审计范围：`package.json`、`scripts/`、`tests/`、`apps/backend/tests/`、`apps/frontend/tests/`、`tests/e2e/dashboard-smoke.spec.ts`

## 1. 统一质量门禁

当前根目录质量入口如下：

| 命令 | 做什么 | 适用场景 |
| --- | --- | --- |
| `npm run check` | 后端全量测试、前端 lint、前端单测、前端构建 | 日常代码改动后的常规门禁 |
| `npm run check:e2e` | 运行 `tests/e2e/dashboard-smoke.spec.ts` | 改跨页面流程、导入、推荐、报表、导航后 |
| `npm run check:all` | 先跑 `check`，再跑 `check:e2e` | 阶段性合并、交付前或公共入口变更后 |
| `npm run backend:p0-check` | 数据健康、SQLite 完整性、备份、临时恢复、恢复后接口检查 | 改数据库、备份恢复、高考数据或交付验收前 |

`check / check:e2e / check:all` 现在由 `scripts/quality-gate.cjs` 分阶段包装。它不降低检查强度，只把失败阶段、命令用途和下一步排查提示说清楚。

## 2. 后端测试覆盖

| 测试文件 | 当前覆盖 |
| --- | --- |
| `test_api_m1.py` | 健康检查、学生创建、基础科目、小语种、教师导入与任教关系 |
| `test_archive_and_system.py` | 成长档案、备份恢复、受控下载、系统模板、导入中心批次聚合 |
| `test_dashboard_profile_and_settings.py` | 工作台画像与系统设置 |
| `test_data_health.py` | P0 数据健康、山东覆盖矩阵、交付判断、特殊类型风险、缺库场景 |
| `test_evaluation_quant_workflow.py` | 评教模板、批次、班主任量化主链路 |
| `test_exam_workflow.py` | 考试成绩导入、分析导出、错误模板、重复行和身份冲突 |
| `test_gaokao_api.py` | 高考只读驾驶舱、山东监控、审阅摘要、院校证据、schema fallback |
| `test_gaokao_materialize.py` | raw 高考表物化到业务表的幂等性 |
| `test_grade_analytics_and_student_attachments.py` | 成绩全景分析、学生附件、年级摘要导出 |
| `test_recommendation_exporters.py` | 推荐报告、志愿草稿 Excel 风险/边界/历史对照摘要 |
| `test_recommendation_workflow.py` | 推荐、规则 bootstrap、特殊类型 fallback、批量推荐、志愿工作台 |
| `test_score_analytics.py` | 排名、百分位等纯计算 |
| `test_student_importer.py` | 学生导入别名、错误报告、自动建班、导入提示 |
| `test_workload_workflow.py` | 课表导入、人工修正、工作量计算与导出 |

结论：后端覆盖以接口和工作流回归为主，核心链路较完整。高风险点主要在真实数据库补齐、公共脚本和桌面打包。

## 3. 前端单测覆盖

| 测试文件 | 当前覆盖 |
| --- | --- |
| `api-client.test.ts` | API 请求、错误 detail、文件上传、安全打开下载 |
| `navigation.test.ts` | 侧栏和路由入口稳定性 |
| `user-feedback.test.ts` | 面向用户的错误原因和下一步提示 |
| `import-feedback.test.ts`、`import-center.test.ts` | 统一导入状态、错误报告、导入中心摘要 |
| `exam-subject-config.test.ts` | 考试科目默认分值和顺序 |
| `analytics-panorama-helpers.test.ts` | 多学年全景看板指标和洞察 |
| `gaokao-overview.test.ts`、`gaokao-evidence.test.ts` | 高考驾驶舱空态解释和院校证据搜索 |
| `recommendations-helpers.test.ts` | 推荐页表单默认值、规则默认值、就业方向分组 |
| `recommendation-submission.test.ts`、`recommendation-strategy.test.ts` | 推荐提交、批量参数、策略快照和脏状态 |
| `recommendation-copy.test.ts`、`recommendation-output-guards.test.ts` | 推荐风险、fallback、输出前复核文案 |
| `recommendation-comparison.test.ts` | 历史方案对比、参考年份变化、过旧样本提示 |
| `volunteer-workbench.test.ts` | 志愿工作台 payload、草稿、规则/边界/风险/职业解释 |
| `report-insights*.test.ts`、`report-type-config.test.ts` | 报表导出前摘要、打印预览路径、中文参数和推荐/志愿摘要 |

结论：前端重点覆盖 helper 和解释逻辑，适合防止页面文案、风险口径和报表摘要漂移。完整页面交互仍主要依赖 E2E。

## 4. E2E 覆盖

`tests/e2e/dashboard-smoke.spec.ts` 当前有 31 条流程，覆盖：

- 工作台导航、学生详情、系统备份。
- 考试创建、成绩导入、分析中心联动。
- 学生/班级/年级/教师分析报表导出和打印预览。
- 工作量、评教、班主任量化打印预览。
- 多学年全景对比。
- 推荐生成、推荐导出、失败回退、空历史、策略模板、历史回放、多方案对比。
- Stage B 生源地回退、批量混合生源地、志愿工作台、草稿版本、就业增强列、就业方向库。
- 志愿草稿报表、推荐/志愿导出前摘要。
- 高考志愿复杂筛选、预估模式、年份边界、模式兼容、志愿上限和草稿名称校验。
- 错误成绩模板、报表缺参、推荐缺参等异常提示。

结论：E2E 主流程覆盖面广，但集中在一个大文件中，失败时常受共享前置数据影响。后续可按“核心教务 / 推荐志愿 / 报表导出 / 异常提示”拆分为多个 spec，降低单次定位成本。

## 5. 当前不足

1. 桌面端打包只有脚本和手工验证记录，缺少自动化冒烟测试。
2. Windows 脚本、Windows 桌面产物和 NSIS 安装包没有当前机器上的自动化验证。
3. `tests/e2e/dashboard-smoke.spec.ts` 过大，公共前置一旦漂移会导致多条流程同时失败。
4. 真实山东公开数据补齐脚本更偏集成性质，适合保留命令验收，不适合在普通单测里联网跑。
5. 导入回滚目前是产品边界内的“备份恢复 / 覆盖修正”，没有 before-image，所以不能补自动删除式回滚测试。
6. 性能、长表格、大数据量导入和视觉回归还没有独立门禁。

## 6. 后续建议

1. 保持 `npm run check` 作为日常质量门禁，不要删减其中任何一段。
2. 改跨页面流程或共享 E2E helper 时，至少跑 `npm run check:e2e`；如果它失败，先修共享前置，再分业务页排查。
3. 改数据库、备份恢复、高考数据或会写库脚本时，额外跑 `npm run backend:p0-check -- --json`。
4. 交付前由最后窗口跑 `npm run check:all` 和 `npm run backend:p0-check -- --json`，并把结果写入交付说明。
