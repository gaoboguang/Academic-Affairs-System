# P0 交付验收手册

- 日期：2026-04-24
- 范围：本地启动、迁移、数据健康检查、并库/物化/规则初始化前后摘要、备份恢复演练
- 主库：`data/app.db`
- 备份目录：`data/backups/`

## 1. 一次性验收命令

```bash
npm run backend:p0-check
```

该命令会对真实 `data/app.db` 做以下检查：

1. 读取数据健康检查摘要。
2. 执行 SQLite `PRAGMA integrity_check`。
3. 生成 P0 备份包到 `data/backups/`。
4. 校验备份包内必须包含 `manifest.json` 与 `db/app.db`。
5. 把备份包恢复到临时目录，不覆盖主库。
6. 对恢复出来的数据库再次执行完整性检查和数据健康检查。
7. 用恢复库启动一次 FastAPI `TestClient`，验证 `/api/system/health` 与 `/api/gaokao/data-health`。

输出中 `ok: true` 表示 P0 安全底座验收通过。

机器可读输出：

```bash
npm run backend:p0-check -- --json
```

保留恢复目录便于排查：

```bash
npm run backend:p0-check -- --keep-restore-dir
```

## 2. 数据健康检查

```bash
npm run backend:data-health
npm run backend:data-health -- --json
```

页面入口：

```text
http://127.0.0.1:5173/gaokao-data
```

进入“山东覆盖”页签查看核心表状态、年份覆盖、考生类型覆盖和 P0 缺口。阶段一覆盖能力也在这里：覆盖表可展开查看按年份 / 类别 / 批次的明细矩阵，下方“数据导入审计摘要”会列出当前记录数、疑似重复、冲突、待人工复核和缺口说明。

特殊类型规则入口：

```text
http://127.0.0.1:5173/recommendations
```

进入“特殊类型规则”页签查看山东春考、综评、单招、艺术、体育等规则的细分类别、匹配关键词、核对清单、初筛优先级和来源备注。

阶段二规则核对入口也在同一页面：

- “赋分规则”：查看 `province_score_transform_rule` 的省份、年份、高考模式、赋分科目、等级表、折算公式和来源备注。
- “选科字典”：查看 `subject_requirement_dict` 的省份、年份、高考模式、原始选科代码、标准化科目和来源备注。
- “特殊类型规则 / 赋分规则 / 选科字典”均支持从页面触发基线装载；当前以核对为主，后续再补完整编辑维护。

## 3. 会改库命令

```bash
npm run backend:merge-handoff
npm run backend:materialize-gaokao
npm run backend:bootstrap-special-types -- --year 2025 --year 2026
```

- `backend:merge-handoff`：把 `data/local_edu_tool/local_edu.sqlite3` 中的原始高考表同步进 `data/app.db`。
- `backend:materialize-gaokao`：把 raw 高考表整理到应用业务表。
- `backend:bootstrap-special-types`：写入山东特殊类型规则字典，默认写库前先备份。

以上命令都应输出执行前后的健康摘要；如缺摘要，先停止继续补库。

## 4. 启动检查

```bash
npm run dev
curl -s http://127.0.0.1:8000/api/system/health
curl -s http://127.0.0.1:8000/api/gaokao/data-health
```

macOS 双击入口：

```text
start-local-edu.command
```

默认地址：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`
- API 文档：`http://127.0.0.1:8000/docs`

## 5. 当前已知 P0 数据缺口

截至 2026-04-24，真实主库仍有以下数据缺口。这些缺口不会阻断 P0 安全底座验收，但会阻断后续“数据可用性”阶段：

1. 特殊类型已有招生计划，但缺少专门录取结果。
2. 2024 年山东招生计划数量偏少，当前健康检查标记为需关注。
3. `score_rank_segment` 缺少 2020-2023 年覆盖。
4. `gaokao_score_line` 缺少 2020-2023 年覆盖。
5. 政策参考数量偏少，当前仅 4 条。
6. 章程限制链仍有大量待复核记录，当前为 1748 条。

处理这些缺口时继续遵守三条红线：不造数据、不静默 fallback、不直接覆盖主库。

## 6. 阶段一数据审计口径

`npm run backend:data-health -- --json` 现在同时输出：

- `expected_years`：当前山东阶段一按 `2020-2025` 检查。
- `field_explanations`：解释 JSON 里各大块字段给谁看、怎么看。
- `delivery_assessment`：把结果分为 `pass`、`warning`、`blocked`，方便交付前快速判断。
- `coverage[].missing_years`：各数据域缺少的年份。
- `coverage[].readiness_label` / `coverage[].explanation`：面向非程序员说明该数据域是完整可用、部分可用，还是只能做初筛。
- `coverage[].batch_distribution`：批次或口径分布。
- `coverage[].year_breakdown`：按年展开后的类别与批次明细。
- `special_type_risks`：普通类、春季高考、艺术类、体育类、单独招生、综合评价招生的分类型可用性，明确计划数、录取数、省控线数、规则数和 fallback 模式。
- `audit_summary`：补数据前后对照用的审计摘要，包含当前记录数、疑似重复、冲突、待人工复核和缺口说明。

截至 2026-04-24，阶段一审计仍显示真实数据缺口：招生计划缺 2021-2023，一分一段和省控线缺 2020-2023，特殊类型缺专门录取结果且只能初筛，政策参考偏少，章程限制链仍需人工复核。

## 7. 非程序员怎么看结果

先看 `delivery_assessment`：

- `pass`：P0 健康检查没有发现阻断项或 P0 数据缺口，可继续做启动、推荐、导出和备份恢复验收。
- `warning`：安全底座可以继续验收，但还有数据缺口；可以本机试用，不能把相关结果当作完整交付结论。
- `blocked`：有核心表缺失、空表或疑似冲突，先不要交付日常使用。

再看 `/gaokao-data` 的“山东覆盖”页签：

- “核心表状态”看表是否存在、有无记录、是否有明显缺口。
- “考生类型可用性”看普通类、春考、艺术、体育、单招、综评分别能用到什么程度。
- “山东年份与类型覆盖”展开每个数据域，确认哪些年份、类别和批次有数据。
- “数据导入审计摘要”看重复、冲突和待复核数量，补数据前后用这里对照。

当前交付判断口径：

- 普通类：已有多年录取结果，可作为推荐主链路参考，但招生计划仍需继续核验完整性。
- 艺术类 / 体育类：有招生计划和部分省控线时，只能做资格线初筛；缺少专门录取结果时不能判断院校录取把握。
- 春季高考 / 单独招生 / 综合评价招生：有计划和规则字典时，只能做方向性初筛；如参考普通类结果，页面、打印和导出必须显式标出 fallback 风险。
- 任何特殊类型都不能因为“有招生计划”就被当成“有完整录取结果”。
