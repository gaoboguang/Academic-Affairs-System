# 第五轮长线数据专项进度日志

## 2026-04-26 21:10

- 当前阶段：阶段 0，环境和基线检查。
- 已完成：
  - 从 `main` 创建并切换到 `codex/r5-longrun-shandong-admission-data-completion`。
  - 确认开工前工作区无未提交改动。
  - 确认 `data/app.db` 未被 Git 跟踪，且被 Git 忽略。
  - 执行 `npm run backend:data-health -- --json`，当前状态为 `warning`，P0 缺口 4 条。
  - 执行 `npm run backend:p0-check -- --json`，结果 `ok: true`。
  - 生成阶段 0 基线报告 `docs/round5-baseline-before-import.md`。
- 新增来源：0。
- 成功导入：0。
- 失败原因：无；本阶段未下载或导入数据。
- 下一步：进入阶段 1，搜索并登记山东省教育招生考试院 2023-2025 官方投档、录取、政策和计划来源。
- 当前 commit：已提交，提交说明为 `docs: add round 5 baseline report`；准确提交号以 `git log -1 --oneline` 为准。

## 2026-04-26 21:25

- 当前阶段：阶段 1/2，官方来源发现、普通类多轮投档来源追溯补齐。
- 已完成：
  - 新增 `scripts/round5_register_shandong_admission_round_sources.py`，用于下载并登记 2023-2025 普通类常规批第 2/3 次志愿投档官方文件，并挂接既有 raw 投档行。
  - 新增 `scripts/round5_register_discovered_source_documents.py`，用于登记已发现的艺术、体育、春考、政策、百问百答和计划补充信息来源。
  - 运行前备份主库：`data/backups/app_before_round5_admission_round_source_link_20260426_2115.db`。
  - 下载 6 份山东省教育招生考试院普通类第 2/3 次志愿投档 XLS 文件并登记 SHA256。
  - `gaokao_source_document` 从 29 增至 67；`gaokao_import_run` 从 15 增至 21。
  - 2023-2025 普通类常规批第 1/2/3 次 raw 投档行全部补齐 `source_document_id / import_run_id`。
  - 生成 `docs/round5-source-discovery-report.md`、`docs/round5-data-coverage-matrix.md` 和 `docs/round5-manual-download-and-review-list.md`。
- 新增来源：38 个 `gaokao_source_document`。
- 成功导入：未新增业务投档行；完成 34707 条既有 raw 投档行来源追溯挂接。
- 失败原因：
  - 系统 `python3` 缺少项目依赖，首次执行登记脚本失败于 `ModuleNotFoundError: No module named 'sqlalchemy'`，未改数据库；已改用 `./.venv/bin/python` 成功执行。
  - 2023/2024 艺术、体育、春考同名“录取情况表”暂未在官网检索结果中命中，已列入人工复核。
- 下一步：下载并解析已登记的 2025 艺术 / 体育 / 春考录取情况表，评估是否新增 `gaokao_admission_min_score` 辅助表；或先把政策来源结构化写入 `gaokao_policy_reference`。
- 当前 commit：待阶段 1/2 本地提交。

## 2026-04-26 23:15

- 当前阶段：阶段 5 提前收口一项，政策参考结构化写入。
- 已完成：
  - 修正 `scripts/round5_register_shandong_admission_round_sources.py` 的复跑逻辑；同一 `source_document_id + importer_name` 已有成功批次时复用原 `gaokao_import_run`，不再重复创建批次。
  - 清理本窗口复验时临时产生的重复 `gaokao_import_run` 22-27，并把对应 raw 投档行恢复指向原批次 16-21；清理前备份主库，SQLite 完整性检查为 `ok`。
  - 新增 `scripts/round5_import_policy_references.py`，把已登记的 2023-2025 录取工作意见、志愿填报百问百答、招生考试政策百问百答写入 `gaokao_policy_reference`。
  - 写库前备份主库：`data/backups/app_before_round5_policy_reference_import_20260426_231412.db`。
  - `gaokao_policy_reference` 从 4 条增至 13 条；复跑该脚本为更新 9 条、不会重复插入。
  - 重新执行 `npm run backend:data-health -- --json`，当前状态仍为 `warning`，P0 缺口从 4 条降为 3 条。
- 新增来源：0 个 `gaokao_source_document`；本阶段复用阶段 1 已登记政策来源。
- 成功导入：9 条政策参考记录。
- 失败原因：无；本阶段未处理录取情况附件。
- 下一步：继续阶段 3，下载并解析 2025 艺术 / 体育 / 春考录取情况表，先确认附件格式和字段，再决定是否新增辅助表承载专门录取结果。
- 当前 commit：待阶段 1/2 + 政策结构化一并本地提交。
