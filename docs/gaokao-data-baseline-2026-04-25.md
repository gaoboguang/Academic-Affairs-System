# 山东高考志愿数据库基线审计

- 审计日期：2026-04-25
- 执行窗口：A0，数据库基线审计与数据缺口确认
- 当前分支：`codex/r2-a0-gaokao-data-baseline`
- 主库：`data/app.db`
- 当前迁移版本：`20260424_0015`
- 本轮范围：只审计山东生源地高考志愿数据基线，不新增功能，不导入新数据。

## 1. 基线命令结果

| 检查项 | 当前结果 |
| --- | --- |
| `git status --short --branch` | `## main...origin/main`，创建 A0 分支前工作区干净 |
| `git log --oneline -5` | 已包含 `a7c7148 docs: record windows 2-9 main merge` 和 `3b796b3 feat: integrate windows 2-9 final acceptance` |
| `git pull --ff-only` | 未完成；本机 GitHub HTTPS 认证不可交互，报错 `could not read Username for 'https://github.com': Device not configured` |
| `npm run backend:data-health -- --json` | 可运行，健康状态为 `warning`，P0 缺口 6 条 |
| `npm run backend:p0-check -- --json` | 通过，`ok: true` |
| P0 备份包 | `data/backups/p0_delivery_backup_20260425_104947.zip` |

说明：`git pull --ff-only` 因本机 GitHub 认证限制失败，但本地 `main` 已在 A0 开工前显示跟踪 `origin/main`，且最近提交符合 v4 开发文档要求。本次审计未写入 `data/app.db`。

## 2. 当前高考相关表清单

### 2.1 应用侧业务表

| 表 | 当前记录数 | 用途判断 |
| --- | ---: | --- |
| `college` | 3460 | 应用侧院校主档 |
| `major` | 13960 | 应用侧专业主档 |
| `college_major` | 60767 | 院校专业关系，支撑专业粒度推荐 |
| `enrollment_plan` | 6341 | 应用侧招生计划，决定可报方向和计划容量 |
| `admission_record` | 170389 | 应用侧录取结果，普通类推荐主参考 |
| `score_rank_segment` | 7492 | 一分一段，分数到位次映射基础 |
| `province_volunteer_rule` | 162 | 省份志愿规则 |
| `province_score_transform_rule` | 876 | 赋分/成绩转换规则 |
| `subject_requirement_dict` | 584 | 选科要求字典 |
| `special_type_rule` | 62 | 春考、艺体、单招、综评等特殊类型初筛规则 |
| `employment_direction` | 14 | 职业方向库 |
| `major_employment_mapping` | 12975 | 专业就业映射 |

### 2.2 raw 高考事实表与来源表

| 表 | 当前记录数 | 用途判断 |
| --- | ---: | --- |
| `gaokao_college` | 3344 | raw 院校主档 |
| `gaokao_major` | 8790 | raw 专业主档 |
| `gaokao_college_tag` | 9284 | raw 院校标签 |
| `gaokao_admission_plan` | 6895 | raw 招生计划 |
| `gaokao_admission_result` | 178343 | raw 投档/录取结果 |
| `gaokao_score_line` | 26 | raw 省控线/批次线 |
| `gaokao_batch_dict` | 32 | raw 批次词典 |
| `gaokao_policy_reference` | 4 | raw 政策参考，明显偏少 |
| `gaokao_college_chapter_rule` | 2052 | raw 招生章程限制链 |
| `gaokao_pathway_dict` | 7 | raw 升学路径字典 |
| `gaokao_province_rule` | 2 | raw 省份规则 |
| `gaokao_province_rule_version` | 2 | raw 省份规则版本 |
| `gaokao_score_transform_rule` | 48 | raw 赋分规则 |
| `gaokao_subject_requirement` | 180788 | raw 选科要求，覆盖山东 2025-2026 与 2027 起两版 |
| `gaokao_subject_requirement_dict` | 27 | raw 选科要求字典 |
| `gaokao_source_registry` | 14 | 已有官方来源登记表 |
| `data_import_error_log` | 4 | 导入错误日志 |
| `import_job` | 16 | 导入任务聚合记录 |

当前没有独立的 `gaokao_source_document`、`gaokao_import_run` 表。现有 raw 表多数已有 `source_title`、`source_url`、`local_source_path`、`parser_script_name`、`published_at`、`review_status`、`import_batch_id` 等字段；应用侧 `enrollment_plan`、`admission_record` 主要保留 `source_note` / `import_batch_name`，还没有统一 `source_document_id`。

## 3. 2023-2025 山东普通类覆盖

### 3.1 投档/录取记录

| 年份 | 应用侧 `admission_record` 普通类 | raw `gaokao_admission_result` 普通类 | 结论 |
| --- | ---: | ---: | --- |
| 2023 | 29301 | 29760 | 普通类常规批已有，可用于主链路参考 |
| 2024 | 30838 | 31755 | 普通类常规批已有，可用于主链路参考 |
| 2025 | 32963 | 34303 | 普通类常规批已有，可用于主链路参考 |

判断：最近三年普通类投档/录取结果已经是当前数据库最完整的一块。下一步不是重复建表，而是给 A1/B1 补齐来源文档、导入批次、错误报告和去重/冲突审计。

### 3.2 招生计划

| 年份 | 应用侧 `enrollment_plan` 普通类记录 | 应用侧计划数合计 | raw `gaokao_admission_plan` 普通类记录 | raw 计划数合计 | 结论 |
| --- | ---: | ---: | ---: | ---: | --- |
| 2023 | 0 | 0 | 0 | 0 | 缺失 |
| 2024 | 587 | 11038 | 588 | 11117 | 明显偏少，需要核验是否只导入了部分批次/文件 |
| 2025 | 3981 | 98767 | 4369 | 106413 | 已有较多计划，仍需来源和完整性校验 |

判断：最近三年普通类推荐的最大结构性缺口之一是 2023 招生计划缺失、2024 招生计划偏少。计划数据只能说明招生方向和容量，不等同于录取把握。

### 3.3 一分一段

| 年份 | `score_rank_segment` 覆盖 | 明细 |
| --- | ---: | --- |
| 2023 | 0 | 缺失 |
| 2024 | 3751 | 夏季高考全体及选考物理、化学、生物、历史、地理、思想政治分布 |
| 2025 | 3741 | 夏季高考全体及选考物理、化学、生物、历史、地理、思想政治分布 |

判断：2024/2025 已可支撑分数到位次换算；2023 缺失会影响三年位次校验和跨年估算。B1 应优先补 2023 一分一段，同时保持 2024/2025 来源追溯。

### 3.4 省控线/批次线

| 年份 | `gaokao_score_line` 记录数 | 覆盖类型 |
| --- | ---: | --- |
| 2023 | 0 | 缺失 |
| 2024 | 12 | 普通类 6、艺术类 4、体育类 2 |
| 2025 | 14 | 普通类 6、艺术类 4、体育类 4 |

判断：2024/2025 已有省控线/资格线；2023 缺失。艺术/体育可用省控线做资格初筛，但不能替代院校或专业录取结果。

### 3.5 选科要求和章程限制

| 数据域 | 当前状态 | 结论 |
| --- | --- | --- |
| raw 选科要求 | `gaokao_subject_requirement=180788`，其中山东 2025-2026 适用版 90865 条、2027 起新版 89923 条 | 2025/2026 普通类推荐可用，但需要在后续导入框架中保留 source document 追溯 |
| 应用侧选科字典 | 山东 2025 年 9 条、2026 年 9 条；全库 `subject_requirement_dict=584` | 基线规则已具备，后续要校验高频专业口径 |
| 章程限制链 | `gaokao_college_chapter_rule=2052`，其中待人工复核 1748 条 | 能提示章程风险，但交付前仍需人工复核和来源校验 |

## 4. 2026 数据状态

| 数据域 | 当前库状态 | A0 判断 |
| --- | --- | --- |
| 普通类正式招生计划 | `enrollment_plan` / `gaokao_admission_plan` 均无 2026 记录 | 未公开或未导入，必须标记为 `pending_official_release` / 待导入，不能伪造 |
| 2026 投档/录取结果 | `admission_record` / `gaokao_admission_result` 均无 2026 记录 | 未发生，不能导入 |
| 2026 一分一段 | 无 2026 记录 | 未发布，若做估算只能使用 2025 并明确提示 |
| 2026 省控线 | 无 2026 记录 | 未发布，不能假装完整 |
| 2026 省份志愿规则 | `province_volunteer_rule` 山东 2026 年 26 条 | 已有规则基线，可用于规则提示 |
| 2026 赋分规则 | `province_score_transform_rule` 山东 2026 年 9 条 | 已有规则基线 |
| 2026 选科字典 | `subject_requirement_dict` 山东 2026 年 9 条；raw 选科要求 2025-2026 适用版 90865 条 | 2025/2026 选科要求已可作为公开依据 |
| 2026 特殊类型规则 | `special_type_rule` 山东 2026 年 31 条 | 春考、艺术、体育、单招、综评初筛规则已有 |

当前能纳入 2026 的只有已公开规则、选科要求、特殊类型政策/初筛规则等。2026 普通类正式招生计划、投档线、一分一段、省控线都不能在 A0 阶段当作已导入数据。

## 5. 当前只能初筛的数据

| 考生类型 | 当前数据 | 可做什么 | 不能做什么 |
| --- | --- | --- | --- |
| 普通类 | 2020-2025 录取结果；2024/2025 招生计划；2024/2025 一分一段和省控线 | 可作为当前推荐主链路参考，重点仍应使用位次 | 2026 正式计划未发布前，不能给出 2026 完整填报结论 |
| 春季高考 | 有招生计划、志愿规则、特殊类型规则；无专门录取结果 | 计划清单初筛、报名/技能类别/章程核对提示 | 不能按完整录取概率或保底结论解释 |
| 艺术类 | 有招生计划、省控线、规则字典；无专门录取结果 | 省控线资格初筛和章程/类别复核 | 不能判断院校或专业录取把握 |
| 体育类 | 有招生计划、省控线、规则字典；无专门录取结果 | 省控线资格初筛和章程/类别复核 | 不能判断院校或专业录取把握 |
| 单独招生 | 有招生计划、规则字典；无专门录取结果 | 计划清单初筛、报名/校测/职业适应测试核对 | 不能包装成普通类录取参考 |
| 综合评价招生 | 有招生计划、规则字典；无专门录取结果 | 计划清单初筛、报名/校测/综合评价规则核对 | 不能包装成普通类录取参考 |

## 6. 本轮最优先补齐的数据

按 A0 审计结果，后续窗口应优先按以下顺序补：

1. **A1 先补来源与导入框架**：复用 `gaokao_source_registry`，新增或补齐 source document / import run / 错误报告 / 本地文件导入目录，避免 B1 直接把数据写进表但无法追溯。
2. **B1 优先补 2023 一分一段和 2023 省控线**：这是最近三年普通类推荐解释中的明确缺口。
3. **B1 校验并补 2023 招生计划、核验 2024 招生计划偏少问题**：2024 当前只有应用侧 587 条普通类计划、raw 588 条普通类计划，需核对官方文件是否只导入部分批次。
4. **B1 给 2023-2025 投档/录取结果补 source document 和导入审计**：记录数已经存在，但仍需追溯来源、批次、去重和冲突。
5. **B2 单独处理 2026 已公开数据状态**：只登记或导入已公开政策、选科要求、单招/综评通知；普通类正式计划未公开时必须保持待发布状态。
6. **后续持续处理章程限制链**：当前 1748 条待人工复核，推荐结果必须继续展示章程待核风险。

## 7. 给下一窗口的交接

下一窗口 A1 不应重做 A0 审计。建议直接读取本文件后做：

- 审计并复用 `gaokao_source_registry`、`import_job`、`data_import_error_log`。
- 判断是否新增 `gaokao_source_document` 和 `gaokao_import_run`，并通过 Alembic 管理。
- 固定官方文件目录：`data/imports/gaokao/official/` 与 `data/imports/gaokao/manual/`。
- 为后续 B1 导入 2023-2025 投档表、一分一段、省控线准备统一字段：`source_document_id`、`total_rows`、`success_rows`、`failed_rows`、`skipped_rows`、`error_report_path`。
- 不要在 A1 抢做 B1 的完整数据导入，也不要伪造 2026 普通类计划。

