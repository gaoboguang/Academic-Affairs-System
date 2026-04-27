# 第六轮山东招生数据库补齐阶段报告

- 日期：2026-04-27
- 分支：`codex/r6-local-shandong-db-completion`
- 执行范围：山东 2023-2025 招生计划、投档、录取数据补齐任务的本地自动化入口与当前覆盖复核

## 1. 本轮已完成

1. 阅读并核对第六轮任务文档、第五轮来源发现报告、覆盖矩阵和人工清单。
2. 新增 `data/seed/round6_gaokao_source_documents.json`，固化 15 个已登记的 2023-2025 艺术、体育、春季高考官方投档来源页面。
3. 新增 `scripts/round6_import_special_filing_results.py`：
   - 自动读取 `gaokao_source_document` 中的特殊类型投档来源。
   - 自动抓取官方页面中的 `xls/xlsx` 附件。
   - 下载到 `data/imports/gaokao/official/{year}/`。
   - 解析专业类别、专业、院校、投档计划数、最低综合分或最低位次。
   - 只写 `gaokao_admission_result` raw 表和 `gaokao_import_run`，不写 `admission_record`。
4. 生成第六轮投档附件处理报告：`docs/round6-special-filing-import-result.md`。
5. 生成第六轮覆盖矩阵：`docs/round6-data-coverage-matrix.md`。
6. 生成章程机器预审样本：`docs/round6-chapter-review-sample.md`。

## 2. 当前执行结果

本机当前仍无法稳定访问 `sdzk.cn` / `sdzk.cn/Floadup`，和第五轮记录一致。为避免长时间卡死，本轮使用：

```bash
./.venv/bin/python scripts/round6_import_special_filing_results.py --no-download --no-backup --json
```

结果：

| 项目 | 数量 |
| --- | ---: |
| 已登记投档来源页面 | 15 |
| 本地已存在可解析附件 | 0 |
| 本轮新写 raw 行 | 0 |
| 本轮新写应用侧录取结果 | 0 |
| 待下载 / 待处理来源 | 15 |

## 3. 当前数据库覆盖

| 数据面 | 当前结论 |
| --- | --- |
| 普通类 2023-2025 多轮投档 | 已导入并追溯 |
| 2025 艺术类本科批录取情况 | raw 3403 条，应用侧可靠匹配 2869 条 |
| 2025 体育类常规批录取情况 | raw 393 条，应用侧可靠匹配 385 条 |
| 2025 春季高考本科批录取情况 | raw 340 条，应用侧可靠匹配 340 条 |
| 2023/2024 艺体春考录取情况 | 仍需继续寻找官方录取情况表 |
| 2023-2025 特殊类型投档表 | 来源页面已登记，附件待下载 |
| 完整招生计划指南 / 官方系统导出 | 仍未取得，不能用补充信息替代 |
| 单招 / 综评专门录取结果 | 仍缺，只能初筛 |
| 章程限制链 | 1748 条待人工复核 |

## 4. 验证结果

已执行：

```bash
./.venv/bin/python -m py_compile scripts/round6_import_special_filing_results.py
./.venv/bin/python scripts/round6_import_special_filing_results.py --no-download --no-backup --json
npm run backend:data-health -- --json
```

结果：

- 脚本语法检查通过。
- 第六轮投档脚本试运行通过，生成报告，无数据库写入。
- 数据健康命令通过，状态仍为 `warning`，P0 缺口仍为 3 条。

## 5. 下一步

1. 网络恢复后直接运行 `./.venv/bin/python scripts/round6_import_special_filing_results.py --json`。
2. 若网络仍失败，人工下载官方投档附件到 `data/imports/gaokao/official/{year}/`，再运行 `./.venv/bin/python scripts/round6_import_special_filing_results.py --no-download --json`。
3. 继续寻找 2023/2024 艺术、体育、春考官方录取情况表；未确认前不得写成录取结果。
4. 继续寻找完整《山东省普通高校招生填报志愿指南》或官方系统导出；补充信息不能关闭招生计划完整性缺口。
5. 章程限制链只允许人工确认后更新 `review_status`。

