# 第四轮 E6 数据库补齐导入结果

- 日期：2026-04-26
- 执行窗口：E6，数据库补齐导入执行
- 当前分支：`codex/r4-e6-data-completion-imports`
- 主库：`data/app.db`
- 导入前备份：`data/backups/app_before_e6_data_completion_import_20260426_135630.db`
- 本窗口边界：只导入可核验的山东官方公开数据；不伪造 2026 未发布数据，不用第三方整理表覆盖主库，不批量关闭章程待复核。

## 1. 本次完成结论

E6 已按 E5 计划补齐两类可自动导入数据：

1. 2020-2022 山东夏季高考一分一段。
2. 2020-2022 山东夏季高考各类别分数线 / 省控线。

导入后 `backend:data-health` 的 P0 缺口从 6 条降为 4 条：

| 项目 | 导入前 | 导入后 |
| --- | --- | --- |
| 一分一段 `score_rank_segment` | 11266 条，缺 2020-2022 | 22388 条，覆盖 2020-2025 |
| 省控线 / 批次线 `gaokao_score_line` | 41 条，缺 2020-2022 | 74 条，覆盖 2020-2025 |
| P0 缺口数量 | 6 条 | 4 条 |

导入后仍保留的 4 条缺口：

1. 特殊类型已有招生计划但缺专门录取结果：春季高考、艺术类、体育类、单独招生、综合评价招生。
2. 山东招生计划 2024 年数量偏少：592 条，需继续核验完整性。
3. 政策参考数量偏少：4 条，交付前需补山东官方政策和填报规则。
4. 招生章程限制链仍有 1748 条待人工复核。

## 2. 官方来源与导入批次

| 年份 | 数据类型 | source_document_id | import_run_id | 导入结果 | 本地官方文件 |
| --- | --- | ---: | ---: | --- | --- |
| 2020 | 一分一段 | 26 | 10 | 3769 / 3769 成功 | `data/imports/gaokao/official/2020/2020_score_rank_segment_2020年夏季高考文化总成绩一分一段表.xls` |
| 2020 | 分数线 / 省控线 | 29 | 11 | 11 / 11 成功 | `data/imports/gaokao/official/2020/2020_score_line_山东省2020年夏季高考各类别分数线.png` |
| 2021 | 一分一段 | 25 | 12 | 3681 / 3681 成功 | `data/imports/gaokao/official/2021/2021_score_rank_segment_2021年夏季高考文化总成绩一分一段表.xls` |
| 2021 | 分数线 / 省控线 | 28 | 13 | 11 / 11 成功 | `data/imports/gaokao/official/2021/2021_score_line_山东省2021年夏季高考各类别分数线.png` |
| 2022 | 一分一段 | 24 | 14 | 3672 / 3672 成功 | `data/imports/gaokao/official/2022/2022_score_rank_segment_2022年夏季高考文化成绩一分一段表.xls` |
| 2022 | 分数线 / 省控线 | 27 | 15 | 11 / 11 成功 | `data/imports/gaokao/official/2022/2022_score_line_山东省2022年夏季高考各类别分数线.png` |

SHA256 已登记到 `gaokao_source_document.file_sha256`：

| source_document_id | SHA256 |
| ---: | --- |
| 26 | `4cd5362110c5b27b356e0a17dd0d0e3e72a6114270835221d7e808886c4c1abc` |
| 29 | `8ec4633a72359032a00385ed9bfaf7554e942c31ac3029d11bc20bebe0ccbe3e` |
| 25 | `22bcbf5204ce0ab9f16d154c807cd1f583198d42ff089acdde98a34521b2921c` |
| 28 | `7fa7d796f7a1515d161d19c1503e164f6ad09b437211fa99dff369795d5ac758` |
| 24 | `14879e51028593ac2a84589e6e1e7ef6cc2a7e83cb0641d72384fb1db7be0b25` |
| 27 | `22a48309e1b0b1958146967cc7d92eb82c7c107c1b271be069ec2195f9ee0a71` |

## 3. 代码与脚本变化

- `apps/backend/app/services/gaokao_imports.py`
  - 新增 2020-2022 一分一段和分数线官方来源种子。
- `apps/backend/app/services/gaokao_official_importers.py`
  - 新增 2020-2022 官方附件 URL。
  - 新增 2020-2022 分数线结构化校对行。
  - 扩展覆盖报告到 2020-2025。
  - 修复 2020 一分一段 Excel-HTML 表头压缩导致的分组解析问题。
- `scripts/import_shandong_gaokao_core_data.py`
  - `--year` 支持 2020-2025。
  - 修正非 JSON 输出使用的导入结果字段。
- `apps/backend/tests/test_gaokao_import_framework.py`
  - 新增 2020 一分一段压缩表头解析回归。

## 4. 已执行命令

```bash
npm run backend:migrate
npm run backend:data-health -- --json
npm run backend:test -- apps/backend/tests/test_gaokao_import_framework.py -q
npm run backend:gaokao-sources -- --json
npm run backend:gaokao-import-shandong-core -- --year 2020 --year 2021 --year 2022 --source-type score_rank_segment --source-type score_line --no-download --coverage-doc docs/round4-data-completion-result.md --json
npm run backend:data-health -- --json
```

第一次导入尝试使用自动下载时，山东省教育招生考试院附件下载出现 HTTPS 握手超时；已改为使用同一官方 URL 预先下载到允许目录的本地文件，并通过 `--no-download` 完成登记、SHA256 和解析写库。

## 5. 不能补齐项

| 数据项 | 当前处理 | 原因 |
| --- | --- | --- |
| 2023 招生计划完整文件 | 本窗口不导入 | E5 未确认到稳定可复用的官方完整公开附件；不能用第三方汇总替代 |
| 2024 招生计划完整性 | 仍保留偏少警告 | 当前可公开确认的多为补充信息，不等同完整计划 |
| 2025 招生计划完整性 | 只保留后续核验项 | 本窗口只补一分一段和分数线，不覆盖既有招生计划 |
| 2026 普通类正式计划 | 不导入 | 官方未发布，不能用单招 / 综评计划限额替代 |
| 2026 一分一段 / 分数线 | 不导入 | 官方未发布，只能继续显示待发布 |
| 特殊类型专门录取结果 | 不导入 | 当前缺官方专门录取结果，只能保持初筛和风险提示 |
| 招生章程限制链 | 不批量关闭 | 需逐校逐专业人工复核，不能无依据改为已确认 |

## 6. 下一步

1. E7 可把本结果接入数据健康、报表和使用说明，重点解释 P0 缺口已从 6 条降到 4 条。
2. 招生计划线继续等待用户提供官方 `填报志愿指南`、志愿填报辅助系统导出或可核验官方附件。
3. 政策参考可以继续从已登记 2026 官方政策来源推进到本地文件 SHA256 和 `gaokao_policy_reference`，但不能替代普通类正式计划。
4. 章程限制链只能按高校官网或人工核验逐条收口，不应批量标记完成。
