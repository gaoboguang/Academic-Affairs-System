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

## 2026-04-26 23:36

- 当前阶段：阶段 3，2025 艺术 / 体育 / 春考专门录取结果导入。
- 已完成：
  - 新增 `scripts/round5_import_2025_special_admission_results.py`，下载并登记 2025 艺术类本科批 6 个专业类别、体育类常规批、春季高考本科批共 8 个官方 XLS 附件。
  - 写库前备份主库：`data/backups/app_before_round5_special_admission_import_20260426_233322.db`。
  - 新增 8 个附件级 `gaokao_source_document`，新增 8 个 `gaokao_import_run`；复跑脚本时全部复用既有批次，不重复创建。
  - 写入 `gaokao_admission_result` raw 专门录取结果 4136 条：艺术类 3403 条、体育类 393 条、春季高考 340 条。
  - 应用侧 `admission_record` 仅在院校和专业能可靠匹配时同步写入 3594 条；未可靠匹配的 542 条保留在 raw 表，不硬凑院校 / 专业 ID。
  - 修正 `apps/backend/app/utils/data_health.py` 的重复估算口径，把 `art_track` 纳入特殊类型录取结果去重维度，避免不同艺术类别被误判为重复。
  - 重新执行 `npm run backend:data-health -- --json`，当前 P0 缺口仍为 3 条，但特殊类型缺口已收窄为“单独招生、综合评价招生”；艺术、体育、春考从“只能初筛”变为“部分可用，需看缺口”。
- 新增来源：8 个附件级 `gaokao_source_document`。
- 成功导入：raw 专门录取结果 4136 条；应用侧可靠匹配 3594 条。
- 失败原因：
  - 542 条应用侧未写入，原因是院校或专业无法用现有应用侧主档可靠匹配；这些记录已保留在 raw 表和官方附件中，后续可做专业别名 / 院校映射专项。
  - 本阶段只找到并导入 2025 本科 / 常规批相关录取情况；2023/2024 同类录取情况、艺术专科、春考专科仍需继续复核。
- 下一步：继续寻找 2023/2024 艺术、体育、春考录取情况来源；或进入招生计划完整性核验和章程机器预审。
- 当前 commit：待阶段 3 本地提交。

## 2026-04-27 08:47

- 当前阶段：阶段 4，招生计划补充信息附件审计。
- 已完成：
  - 确认另一个窗口已经完成并提交阶段 1/2、政策参考结构化和阶段 3 2025 艺术 / 体育 / 春考专门录取结果导入；当前 HEAD 为 `data: import round 5 special admission results`。
  - 保留并微调 `scripts/round5_register_shandong_admission_round_sources.py` 的幂等复跑导入，复跑时不会再新增重复 `gaokao_import_run`。
  - 新增 `scripts/round5_register_plan_supplement_documents.py`，用于下载、登记和审计 2023-2025 山东省教育招生考试院招生计划补充信息 docx 附件。
  - 新增 `docs/round5-plan-supplement-audit.md`，记录 5 个官方补充信息页面、附件直链、下载失败原因和人工下载后复跑命令。
  - 更新 `docs/round5-data-coverage-matrix.md`、`docs/round5-manual-download-and-review-list.md`、`docs/README.md`，明确补充信息不能替代完整《填报志愿指南》，也不能关闭 2024 招生计划数量偏少缺口。
- 新增来源：0 个 `gaokao_source_document`；本阶段只复用阶段 1 已登记的计划补充信息来源。
- 成功导入：0 条业务计划记录。
- 失败原因：
  - 本机访问 5 个 `sdzk.cn/Floadup` 官方 docx 附件直链时均出现 SSL 握手超时；`curl --http1.1` 复核同样超时。
  - 已把 5 个附件直链写入人工下载清单；人工放入 `data/imports/gaokao/official/{year}/` 后可复跑 `./.venv/bin/python scripts/round5_register_plan_supplement_documents.py --no-download --json`。
- 下一步：优先进入阶段 6 章程限制链机器预审，或继续寻找单招 / 综评专门录取结果来源；2024 招生计划缺口仍需完整指南或官方系统导出，不能用补充信息替代。
- 当前 commit：待阶段 4 本地提交。

## 2026-04-27 08:52

- 当前阶段：阶段 6，章程限制链机器预审第一批。
- 已完成：
  - 新增 `scripts/round5_chapter_machine_preaudit.py`，对 `gaokao_college_chapter_rule` 中已有高校官网候选链接的待复核记录做机器连通性检查。
  - 写库前备份主库：`data/backups/app_before_round5_chapter_machine_preaudit_20260427_085200.db`。
  - 第一批处理 50 条 `pending_manual_review_with_official_candidate`，写入 `chapter_fallback_verification_status`，并把机器检查摘要追加到 `chapter_fallback_note`。
  - 新增 `docs/round5-chapter-machine-preaudit.md`，记录每条候选链接、HTTP 状态、机器状态和后续人工处理边界。
  - 更新 `docs/round5-data-coverage-matrix.md`、`docs/round5-manual-download-and-review-list.md`、`docs/README.md`。
- 新增来源：0。
- 成功导入：0 条业务数据；机器预审 50 条章程候选链接。
- 机器预审结果：
  - 可访问：2 条。
  - 超时：47 条。
  - 访问异常：1 条。
- 失败原因：
  - 大多数高校官网候选链接在当前网络下超时或 SSL 握手超时；这些结果只说明“本机机器检查未成功”，不能等同于官网不存在。
  - 本阶段没有把任何 `review_status` 改为 `confirmed_*`，因此 `backend:data-health` 中章程待人工复核数量仍保持 1748 条。
- 下一步：对 2 条可访问记录人工打开并确认是否为招生官网 / 章程栏目；或在网络更稳定时扩大机器预审批量。仍不得批量标记为人工确认。
- 当前 commit：待阶段 6 本地提交。

## 2026-04-27 09:15

- 当前阶段：阶段 6 扩大预审 + 阶段 7 验收收口。
- 已完成：
  - 继续运行 `scripts/round5_chapter_machine_preaudit.py --limit 450 --timeout 3 --workers 24 --json`，累计机器预审章程候选链接 500 条。
  - 新增 `docs/round5-chapter-review-report.md`，汇总 500 条机器预审结果和可人工优先核对记录。
  - 新增 `docs/round5-chapter-review-errors.md`，记录访问异常、404、444、502 和超时处理原则。
  - 新增 `docs/round5-shandong-admission-data-final-report.md`，按开发文档阶段 7 汇总本轮数据变化、剩余缺口和验收结果。
  - 更新 `docs/round5-data-coverage-matrix.md`、`docs/round5-manual-download-and-review-list.md`、`docs/README.md`。
- 新增来源：0 个 `gaokao_source_document`；本阶段只写章程机器预审状态。
- 成功导入：0 条业务数据；累计机器预审 500 条章程候选链接。
- 机器预审累计结果：
  - 可访问：18 条。
  - 超时：463 条。
  - 访问异常：13 条。
  - HTTP 404：4 条。
  - HTTP 444：1 条。
  - HTTP 502：1 条。
- 失败原因：
  - 大量高校官网在当前网络下超时或 SSL 握手超时，不能视为官网不存在。
  - 2023 / 2024 艺术、体育、春考“录取情况表”和单招 / 综评专门录取结果未在官网检索中明确命中，继续列入人工复核。
  - 招生计划完整指南或官方系统导出未取得，补充信息不能替代完整计划。
- 下一步：人工下载计划补充附件并复跑计划登记脚本；人工核对 18 条可访问章程链接；如继续自动化，可分批预审剩余 949 条候选链接。
- 当前 commit：待阶段 7 本地提交。
