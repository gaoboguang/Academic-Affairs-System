# 第四轮 E5 数据库补齐审计与数据源计划

- 日期：2026-04-26
- 执行窗口：E5，数据库补齐审计与数据源计划
- 当前分支：`codex/r4-e5-data-completion-audit-plan`
- 主库：`data/app.db`
- 本窗口边界：只做审计、计划和来源清单，不大规模导入，不替换 `data/app.db`，不伪造官方数据。

## 1. 当前健康结论

本窗口已执行：

```bash
npm run backend:data-health -- --json
```

当前结果：

| 项目 | 当前值 |
| --- | --- |
| 数据库 | `/Users/gao/local-edu-tool/data/app.db` |
| 生成时间 | `2026-04-26 13:33:41` |
| Alembic 版本 | `20260426_0019` |
| 总结 | 核心表缺失 0 个，空表 0 个，需关注表 2 个，P0 缺口 6 条 |
| P0 交付判断 | 可验收但有数据警告 |

核心表规模：

| 数据域 | 当前记录数 | 判断 |
| --- | ---: | --- |
| 应用侧院校 `college` | 3455 | 可用 |
| 应用侧专业 `major` | 13959 | 可用 |
| 院校专业关联 `college_major` | 60761 | 可用 |
| 应用侧招生计划 `enrollment_plan` | 6338 | 部分可用 |
| 应用侧录取结果 `admission_record` | 170385 | 普通类主链路可用 |
| 一分一段 `score_rank_segment` | 11266 | 2023-2025 已覆盖 |
| raw 招生计划 `gaokao_admission_plan` | 6895 | 部分可用 |
| raw 录取结果 `gaokao_admission_result` | 178343 | 普通类主链路可用 |
| raw 省控线 / 批次线 `gaokao_score_line` | 41 | 2023-2025 已覆盖 |
| raw 政策参考 `gaokao_policy_reference` | 4 | 偏少 |
| raw 招生章程限制链 `gaokao_college_chapter_rule` | 2052 | 可提示风险，仍需复核 |

当前仍保留 6 条 P0 缺口：

1. 特殊类型已有招生计划但缺专门录取结果：春季高考、艺术类、体育类、单独招生、综合评价招生。
2. 山东招生计划 2024 年数量偏少：592 条，需继续核验完整性。
3. 一分一段缺少年份：2020、2021、2022。
4. 省控线 / 批次线缺少年份：2020、2021、2022。
5. 政策参考数量偏少：4 条，交付前需补山东官方政策和填报规则。
6. 招生章程限制链仍有 1748 条待人工复核。

## 2. 补齐原则

本轮数据库补齐只接受以下数据：

- 官方网站页面、附件、公告或用户提供的官方原始文件。
- 可登记到 `gaokao_source_document` 的来源。
- 可记录 `file_sha256` 的本地文件。
- 可写入 `gaokao_import_run` 的导入批次。
- 可用 `backend:data-health` 对比补齐前后变化的数据。

以下内容不能补成“已导入”：

- 2026 普通类正式招生计划在官方未发布前不能导入。
- 2026 投档 / 录取结果在录取阶段前本来不存在，不能伪造。
- 特殊类型录取结果缺官方专门结果时，只能保留初筛、资格线或计划清单口径。
- 招生章程限制链未逐校核验前，不能批量改成已确认。
- 《填报志愿指南》或志愿填报辅助系统中未取得授权或本地官方文件前，不能用第三方整理表替代。

## 3. 逐项补齐计划

| 数据项 | 当前状态 | 处理方式 | E6 动作 | 验收口径 |
| --- | --- | --- | --- | --- |
| 2020-2022 一分一段 | `score_rank_segment` 缺 2020、2021、2022 | 可自动导入，前提是先登记官方来源和下载文件 | 扩展 2020-2022 `score_rank_segment` 来源种子、下载附件、登记 SHA256，复用或扩展 `shandong_score_rank_segment` 解析器 | `backend:data-health` 不再提示一分一段缺 2020-2022 |
| 2020-2022 省控线 / 批次线 | `gaokao_score_line` 缺 2020、2021、2022 | 可补齐，但需要人工校对官方图片 / 页面中的分数线 | 扩展 2020-2022 `score_line` 来源种子；如果附件是图片，先登记文件和 SHA256，再在解析器中写入人工校对后的结构化行 | `backend:data-health` 不再提示省控线 / 批次线缺 2020-2022，且导入批次记录来源 |
| 2023 招生计划 | 应用侧和 raw 招生计划缺 2023 | 需人工下载或用户提供官方文件 | 优先寻找山东省教育招生考试院官方 `填报志愿指南`、志愿填报辅助系统导出或官方补充信息；没有官方文件时只登记缺口 | 不允许用第三方汇总表直接补主库 |
| 2024 招生计划完整性 | 当前应用侧 592 条，数量偏少 | 需人工核验 | 登记并核对 2024 本科、专科分专业招生计划补充信息；注意补充信息不能等同完整计划 | 如果只补补充信息，状态仍应是部分补齐 |
| 2025 招生计划完整性 | 当前应用侧 5601 条，需复核 | 需人工复核 | 核对 2025 本科、专科补充信息和现有 handoff 计划来源；只补漏项，不覆盖已有可追溯记录 | `enrollment_plan` / `gaokao_admission_plan` 无冲突，来源可追溯 |
| 2026 已公开政策 / 单招综评 / 路径规则 | 多条 2026 政策来源已登记，但不少文件尚无本地 SHA256 | 需人工下载和登记；政策可结构化为参考，不是普通类计划 | 把已登记的 2026 政策来源下载到 `data/imports/gaokao/official/2026/` 或 `manual/2026/`，登记文件；必要时把政策条目写入 `gaokao_policy_reference` | `publication_status` 继续显示普通类正式计划待发布，政策来源有本地文件和 SHA256 |
| 2026 普通类正式计划 | 当前 `pending_official_release` | 官方未发布 | 不导入。E6 只保留待发布登记和页面说明 | 不得出现 2026 普通类正式计划已导入的误判 |
| 政策参考 | 当前 `gaokao_policy_reference=4` | 可补官方政策参考 | 将 D2/D6/D7 已登记的报名、录取意见、艺术、体育、单招、综评、春考等官方政策落入政策参考表或保留导入批次计划 | 政策参考数量增加，来源可追溯，仍不替代招生计划 |
| 招生章程限制链 | 当前 2052 条，其中 1748 条待人工复核 | 需人工复核 | E6 不批量关闭待复核；可按高校官网批量登记候选来源，输出复核队列 | `pending_review` 可减少，但必须有人工核验依据 |
| 特殊类型专门录取结果 | 当前计划和规则有数据，录取结果为 0 | 需官方专门数据，暂无则本轮不适用 | 不使用普通类录取结果伪造特殊类型录取线；保持 `screening_only` | 页面、打印、导出继续显示初筛和 fallback 风险 |

## 4. 当前导入入口

现有入口可继续复用：

```bash
npm run backend:gaokao-sources -- --json
npm run backend:gaokao-sources -- --list --json
npm run backend:gaokao-import-official -- --source-document-id <id> --file <官方文件> --json
npm run backend:gaokao-import-official -- --source-document-id <id> --file <官方文件> --parse --json
npm run backend:gaokao-import-shandong-core -- --json
npm run backend:data-health -- --json
npm run backend:p0-check -- --json
```

E6 如果要补 2020-2022 一分一段和分数线，建议先做最小脚本改造：

1. 在 `apps/backend/app/services/gaokao_imports.py` 中补 2020-2022 `score_rank_segment`、`score_line` 的 `GaokaoSourceDocumentSeed`。
2. 在 `apps/backend/app/services/gaokao_official_importers.py` 中补 2020-2022 官方附件 URL 或文件发现逻辑。
3. 在 `scripts/import_shandong_gaokao_core_data.py` 中允许 `--year 2020 --year 2021 --year 2022`。
4. 对一分一段优先复用现有 xls 解析器；对分数线图片或页面，先人工校对结构化行，再写入 `SCORE_LINE_ROWS` 并保留来源文件 SHA256。
5. 写库前备份 `data/app.db`，写库后执行 `backend:data-health` 和 `backend:p0-check`。

## 5. E6 推荐执行顺序

1. 备份当前主库。
2. 登记或补齐 2020-2022 一分一段和分数线官方来源。
3. 下载官方附件，登记本地文件与 SHA256。
4. 扩展并运行 2020-2022 一分一段导入。
5. 人工校对并导入 2020-2022 分数线。
6. 再处理政策参考，把已有 2026 政策来源从“仅来源登记”推进到“政策参考记录”。
7. 最后处理招生计划完整性，不要把补充信息当成完整计划。
8. 执行：

```bash
npm run backend:data-health -- --json
npm run backend:p0-check -- --json
git diff --check
```

## 6. E6 不应做的事

- 不直接替换 `data/app.db`。
- 不用第三方表格覆盖官方来源。
- 不把 2024 / 2025 分专业招生计划补充信息当成完整招生计划。
- 不把 2026 单招 / 综评计划限额当成普通类夏季高考正式计划。
- 不把普通类录取结果复制成春考、艺体、体育、单招或综评录取结果。
- 不批量关闭招生章程待复核状态，除非每条都有官方章程或人工核验记录。

## 7. 本窗口结论

E5 已确认：当前最适合 E6 自动推进的是 2020-2022 一分一段和 2020-2022 省控线 / 批次线。招生计划、政策参考和章程限制链可以继续推进，但必须保留“部分补齐 / 需人工复核 / 待官方发布”的状态，不能包装成一次性全量完成。
