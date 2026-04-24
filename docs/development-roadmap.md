# 开发路线图

- 文档日期：2026-04-24
- 执行窗口：窗口 0，仓库审计与总控规划
- 当前交付焦点：山东生源地考生，全国高校在山东招生数据，本地单机可稳定使用

## 1. 总体原则

1. 先保证启动、迁移、备份、恢复和数据健康检查稳定。
2. 当前高考主线以山东为近期唯一生源地范围。
3. 普通类推荐以位次为主、分数为辅；特殊类型只能做安全初筛和人工复核提示。
4. 不造缺失数据，不静默 fallback，不把计划或省控线包装成录取把握。
5. 多窗口并行时，每个窗口只改自己负责的范围；迁移、主库写入和核心推荐服务必须串行。

## 2. 后续任务清单

| 窗口 | 任务 | 当前状态 | 主要文件或目录 | 是否适合并行 | 验收标准 |
| --- | --- | --- | --- | --- | --- |
| 0 | 仓库审计、Mac 文档、路线图、AGENTS | 本文档已落地 | `docs/repo-audit.md`、`docs/mac-dev-setup.md`、`docs/development-roadmap.md`、`AGENTS.md` | 否 | 四份窗口0文档存在，能说明技术栈、启动状态、下一步 |
| 1 | Mac 环境和启动修复 | 已有基础，需复核从零流程 | `README.md`、`docs/mac-dev-setup.md`、`scripts/dev-local.cjs`、`start-local-edu.command`、`.env.example` | 可与窗口2/3并行 | 新环境能安装依赖、迁移、启动前后端；文档与真实命令一致 |
| 2 | 数据模型、数据库、迁移、约束 | 已较完整，重点是高考数据缺口和规则维护 | `apps/backend/app/models`、`apps/backend/alembic/versions`、`scripts/check_data_health.py`、`scripts/materialize_gaokao_structured_data.py` | 谨慎并行 | 迁移可重复跑，数据健康摘要能反映补数据前后变化，无未备份写库 |
| 3 | 前端基础框架、导航、只读数据页 | 已有导航和页面，重点是规则/数据核对体验 | `apps/frontend/src/layouts`、`apps/frontend/src/pages/GaokaoDataPage.vue`、`apps/frontend/src/pages/RecommendationsPage.vue` | 可与窗口1并行，避开窗口2改同一接口 | 页面可进入主要模块，空态和风险说明清楚，前端构建通过 |
| 4 | 用户、角色、权限 | 当前未实现，且不属于近期 P0 | `apps/backend/app/models/system.py`、前端系统设置页 | 暂缓 | 如要做，先重新确认本地单用户边界，不能影响现有单机启动 |
| 5 | 学生、教师、班级、课程基础信息 | 基本可用 | `students.py`、`teachers.py`、`base_data.py`、对应前端页面 | 可并行做小修 | 导入反馈友好，基础数据不破坏分析和推荐前置 |
| 6 | 课表模块 | 基本可用 | `workload.py`、`_workload_calculation.py`、`TimetableWorkloadPage.vue` | 可并行做局部优化 | 课表导入、修正、规则、计算、导出仍可用 |
| 7 | 考试与成绩模块 | 基本可用 | `exams.py`、`analytics.py`、`ExamsPage.vue`、`AnalyticsPage.vue` | 可并行做局部优化 | 考试建模、成绩导入、分析链路和 E2E 前置不回退 |
| 8 | 批量导入导出 | 多模块已有，仍需补高考数据导入审计 | `importers`、`exporters`、`reports.py`、`scripts` | 可与窗口2串行配合 | 导入后有新增、更新、重复、冲突、待审摘要；导出前有复核摘要 |
| 9 | 测试、验收、文档、清理 | 已有检查入口，需要交付前总验收 | `tests`、`README.md`、`docs`、`scripts/README.md` | 最后集中做 | `npm run check:all` 和 `backend:p0-check` 通过，文档不滞后 |
| 10 | 代码审查、冲突检查、最终交付 | 暂未开始 | 全仓库 | 最后做 | 公共文件冲突处理完，交付说明清晰 |

## 3. 近期优先路线

### P0：安全底座验收

当前状态：已基本完成。

继续项：

- 窗口 1 复核 Mac 从零环境。
- 窗口 9 交付前再跑 `npm run backend:p0-check -- --json`。
- 交付前确认 `start-local-edu.command` 和 `npm run dev` 都能给非程序员用户稳定启动。

验收：

- `npm run backend:migrate` 可重复执行。
- `npm run backend:data-health -- --json` 有可读摘要。
- `npm run backend:p0-check -- --json` 返回 `ok: true`。

### P1：山东数据底座补齐

当前状态：只读覆盖矩阵和导入审计摘要已经有；真实数据仍缺。

继续项：

- 补山东 2021-2023 招生计划。
- 补一分一段 2020-2023。
- 补省控线/批次线 2020-2023。
- 扩充山东政策参考。
- 继续复核招生章程限制链。
- 特殊类型如果拿不到专门录取结果，必须保持“仅初筛”标记。

验收：

- `/gaokao-data` 能按年份、类别、批次说明覆盖率。
- 补数据前后 `audit_summary` 能显示新增、更新、冲突和待审。
- 不因补数据破坏普通类推荐。

### P2：山东志愿推荐交付版

当前状态：普通类主链路和特殊类型初筛链路已具备，规则核对入口已先落地。

继续项：

- 普通类推荐做一组山东真实样例验收。
- 特殊类型页面、打印、Excel 三端继续保持初筛性质一致。
- 志愿草稿继续检查山东批次上限、重复、保底不足、选科不符、章程待核。
- 规则管理补完整编辑维护，而不是只看列表和 bootstrap。

验收：

- 一个山东普通类学生能完整走完“录入分数/位次 -> 生成候选 -> 保存草稿 -> 打印/导出”。
- 推荐结果必须有来源、年份、样本数、参考口径和风险解释。

### P3：数据工作台和用户手册

当前状态：开发命令和只读看板有了，用户侧补数据和审数据流程仍不完整。

继续项：

- 高考数据工作台从只读展示扩展到低风险维护入口。
- 数据导入复核页展示重复组、同名组、来源差异、字段冲突、待审状态。
- 用户手册覆盖启动、备份、导入、推荐、打印、恢复、常见问题。

验收：

- 使用者不读日志也能判断某一年、某类考生数据是否足够做志愿辅助。
- 重要规则不需要改代码才能调整。

## 4. 公共文件保护清单

以下文件不建议多个窗口同时修改：

- `package.json`
- `README.md`
- `AGENTS.md`
- `.rulesync/rules/overview.md`
- `.env.example`
- `apps/backend/app/models/recommendation.py`
- `apps/backend/app/api/routes/recommendations.py`
- `apps/backend/app/services/_recommendations_generation.py`
- `apps/backend/app/services/_recommendations_workbench.py`
- `apps/backend/app/services/gaokao.py`
- `apps/frontend/src/pages/RecommendationsPage.vue`
- `apps/frontend/src/pages/GaokaoDataPage.vue`
- `tests/e2e/dashboard-smoke.spec.ts`
- `data/app.db`
- `apps/backend/alembic/versions/*`

## 5. 并行窗口建议

- 第二批最多同时开 3 个窗口：窗口 1、窗口 2、窗口 3。
- 如果窗口 2 正在改数据库或迁移，窗口 3 只能做前端纯展示，不要同时改接口 schema。
- 如果窗口 3 正在改推荐页，窗口 8 不要同时改推荐导出和报表摘要。
- 窗口 9 和窗口 10 应在前面窗口完成后再开。

## 6. 每个窗口完成后的中文汇报格式

每个窗口结束时必须说明：

1. 改了哪些文件。
2. 新增或修复了什么。
3. 为什么这样做。
4. 运行了哪些验证，结果是什么。
5. 还剩哪些风险或下一步。
