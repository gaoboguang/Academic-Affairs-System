# Round 2 山东高考志愿推荐最终集成报告

- 日期：2026-04-25
- 执行窗口：C3，最终集成、测试、合并、交接文档
- 集成分支：`codex/r2-final-gaokao-recommendation-integration`
- 基线：`main` 当前本地最新为 `a7c7148 docs: record windows 2-9 main merge`
- 主题：山东生源地普通类高考志愿数据库补齐、数据质量解释、冲稳保推荐、报告导出

## 1. 集成结论

本轮 A0/A1/B1/B2/B3/B4/C1/C2 成果已在 C3 分支汇总。当前实现已经形成“官方来源登记 -> 最近三年核心数据导入 -> 数据健康看板 -> 学生分数/位次预估 -> 山东普通类冲稳保预览 -> 页面展示 -> 打印和 Excel 输出”的闭环。

本轮仍保持以下红线：

- 不伪造 2026 普通类正式招生计划、投档结果、一分一段或省控线。
- 不把校内考试名次直接当作山东全省位次。
- 不把特殊类型、艺体、春考、单招、综评包装成完整录取概率。
- 不新增持久化推荐候选结果表，山东普通类推荐当前仍是本机预览和报告输出。

## 2. 分支整合状态

| 窗口 | 分支 / 来源 | 状态 | 说明 |
| --- | --- | --- | --- |
| A0 | `codex/r2-a0-gaokao-data-baseline` | 已集成 | 数据库基线审计与缺口文档 |
| A1 | `codex/r2-a1-gaokao-source-import-framework` | 已集成 | `gaokao_source_document`、`gaokao_import_run` 和官方文件登记入口 |
| B1 | `codex/r2-b1-shandong-2023-2025-official-data` | 已集成 | 2023-2025 投档表、一分一段、省控线解析与导入 |
| B2 | `codex/r2-b2-2026-gaokao-data-watchlist` | 已集成 | 2026 已公开 / 待发布状态进入健康检查和页面 |
| B3 | `codex/r2-b3-student-gaokao-score-projection` | 已集成 | `student_gaokao_score_projection` 迁移和预估接口 |
| B4 | `codex/r2-b4-shandong-rush-stable-safe-recommendation` | 已集成 | 山东普通类冲稳保推荐预览接口 |
| C1 | 当前 C3 工作区接续 | 已集成 | `/recommendations` 山东普通类推荐工作台和数据质量看板 |
| C2 | 当前 C3 工作区接续 | 已集成 | 山东普通类推荐打印页、Excel 导出和报表记录 |

说明：本机 C1/C2 成果在 C3 开工时处于当前 C2 分支未提交工作区；C3 未回退这些成果，已在最终集成分支中一并收口。

## 3. 本轮新增能力

### 数据与来源

- 新增官方来源登记与导入运行表，核心导入可追溯到 `source_document_id` 和 `import_run_id`。
- `data/imports/gaokao/official/` 与 `data/imports/gaokao/manual/` 成为本地官方文件入场目录；目录内容为本机材料，不纳入代码提交。
- 最近三年山东普通类投档表、一分一段、省控线已完成结构化导入。
- 2026 数据状态已分为已导入、已公开待结构化、待官方发布、当前阶段不适用、需人工核验。

### 推荐链路

- 支持三种山东普通类推荐输入：
  - 选择学生与考试估算；
  - 手动填写预估高考分；
  - 手动填写山东全省位次。
- 推荐结果按“冲 / 稳 / 保 / 仅关注”分组，保留学校 + 专业粒度。
- 选科不符候选不会进入推荐结果。
- 数据不足、计划缺失、计划缩招、校内估算、上一年一分一段估算都会显式提示。
- 页面、打印页和 Excel 均保留 2026 普通类正式计划未完全公开的提示。

### 输出链路

- `/recommendations` 新增“山东普通类推荐”页签。
- 新增 `/print/shandong-recommendation/:storageKey` 打印页。
- 新增 `POST /api/reports/shandong-recommendation/export`，导出 Excel 并写入报表导出记录。
- Excel 包含“汇总页 / 风险说明 / 冲列表 / 稳列表 / 保列表 / 数据不足与风险列表 / 数据来源页”。

## 4. 数据库与数据覆盖结论

- 当前真实主库：`data/app.db`
- C3 已在迁移前备份：`data/backups/app_before_c3_round2_integration_migrate_20260425_1700.db`
- C3 已执行后端迁移，当前 Alembic 版本：`20260425_0017`
- `npm run backend:data-health -- --json` 当前状态：`warning`
- P0 缺口数量：6
- `npm run backend:p0-check -- --json` 当前结果：`ok: true`
- C3 P0 备份包：`data/backups/p0_delivery_backup_20260425_170902.zip`

更详细覆盖矩阵见 `docs/gaokao-data-coverage-after-round2.md`。

## 5. 当前风险

1. 2026 普通类正式招生计划、一分一段、省控线仍待官方发布；当前推荐只能作为预估参考。
2. 2026 普通类投档 / 录取结果当前阶段本来不会产生，不能要求导入。
3. 2023 招生计划缺失，2024 招生计划数量仍偏少，正式填报前需要继续补计划专项。
4. 2020-2022 一分一段和省控线仍缺失，但最近三年 2023-2025 已满足本轮山东普通类推荐最低需要。
5. 政策参考仍只有 4 条，章程限制链仍有 1748 条待人工复核。
6. 校内考试估算缺少本校历史高考校准表，只能作为低 / 中置信预估，不能替代山东全省位次。
7. 特殊类型仍只能初筛，不能给完整录取判断。

## 6. C3 验收记录

| 命令 | 结果 |
| --- | --- |
| `git fetch --all --prune` | 失败；本机 GitHub HTTPS 认证不可交互：`could not read Username for 'https://github.com': Device not configured` |
| `npm run backend:migrate` | 通过；真实主库从 `20260425_0016` 升到 `20260425_0017` |
| `npm run backend:data-health -- --json` | 通过；schema_version=`20260425_0017`，状态 `warning`，P0 缺口 6 条 |
| `npm run backend:p0-check -- --json` | 通过；`ok: true`，备份包 `data/backups/p0_delivery_backup_20260425_170902.zip` |
| `git diff --check` | 通过 |
| `npm run backend:test -- apps/backend/tests/test_recommendation_exporters.py -q` | 通过；`6 passed` |
| `npm run frontend:test -- tests/shandong-recommendation-workbench.test.ts` | 通过；`5 passed` |
| `npm run check` | 通过；后端 `84 passed`、前端单测 `133 passed`、lint 和构建通过 |
| `npm run check:all` | 通过；后端 `84 passed`、前端单测 `133 passed`、E2E `32 passed` |

## 7. 下一轮建议

1. 2026 普通类正式计划发布后，按 A1/B1 导入框架做增量导入，不要手填假数据。
2. 补本校历届高考校准数据，把校内考试估算从“低 / 中置信”提升为更可靠的校准模型。
3. 专项核验 2023 招生计划缺失和 2024 招生计划偏少问题。
4. 继续补山东政策参考和高校章程限制链人工复核。
5. 将当前预览推荐进一步扩展为可保存、可比较、可追踪的山东普通类志愿方案，但需先确认数据模型边界。
