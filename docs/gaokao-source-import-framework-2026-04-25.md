# 山东高考官方来源登记与导入框架

- 日期：2026-04-25
- 执行窗口：A1，数据源登记、导入批次、官方数据导入框架
- 当前目标：为 B1 导入 2023-2025 山东普通类投档表、一分一段、省控线，以及 B2 登记 2026 已公开数据，先建立可追溯框架。

## 1. 本轮新增表

### `gaokao_source_document`

用途：记录每份官方页面、公告或人工下载文件的来源。

核心字段：

- `province`、`year`、`source_type`
- `title`、`url`、`official_org`
- `source_registry_code`
- `published_at`、`fetched_at`
- `local_file_path`、`file_sha256`
- `parser_name`、`parser_version`
- `status`、`note`

默认已支持来源类型：

- `admission_result`：普通类常规批投档情况表
- `score_rank_segment`：一分一段表
- `score_line`：各类别分数线 / 省控线
- `subject_requirement`：选考科目要求
- `policy`：政策通知

### `gaokao_import_run`

用途：记录某份来源文档的一次导入运行，为后续解析器留下统一批次口径。

核心字段：

- `source_document_id`
- `importer_name`
- `started_at`、`finished_at`
- `status`
- `total_rows`、`success_rows`、`failed_rows`、`skipped_rows`
- `created_rows`、`updated_rows`
- `error_report_path`
- `raw_snapshot_path`
- `note`

当前 A1 只登记“待解析”批次，不把文件解析写入业务表；B1 需要在同一条 `import_run` 上补真实行数、成功/失败行、错误报告和目标表写入。

## 2. 已扩展引用字段

迁移 `20260425_0016` 会给以下表按存在情况补可空引用字段：

- `admission_record`
- `enrollment_plan`
- `score_rank_segment`
- `gaokao_score_line`
- `gaokao_admission_result`
- `gaokao_admission_plan`
- `gaokao_subject_requirement`
- `gaokao_college_chapter_rule`

新增字段：

- `source_document_id`
- `import_run_id`

说明：raw 高考表来自 handoff，并非所有干净库都存在；迁移会先检查表是否存在，再补字段，不影响干净库 `alembic upgrade head`。

## 3. 新增命令

### 登记默认官方来源

```bash
npm run backend:gaokao-sources -- --json
```

该命令会：

- 准备本地导入目录。
- 如 `gaokao_source_registry` 存在，则补/更新山东省教育招生考试院、山东省教育厅、高校官网招生章程三类来源。
- 写入 v4 文档要求的默认 `gaokao_source_document`。

默认导入目录：

```text
data/imports/gaokao/official/
data/imports/gaokao/manual/
data/imports/gaokao/error_reports/
data/imports/gaokao/raw_snapshots/
```

### 登记人工下载文件

```bash
npm run backend:gaokao-import-official -- \
  --source-document-id 6 \
  --file data/imports/gaokao/official/2023/sample.xls \
  --importer-name shandong_score_rank_segment \
  --json
```

该命令会：

- 校验文件必须在 `data/imports/gaokao/official/` 或 `data/imports/gaokao/manual/` 下。
- 写入 `local_file_path` 和 `file_sha256`。
- 创建一条 `gaokao_import_run`，状态为 `pending`。

当前不会解析数据；B1 需要把真实解析器接到该入口。

## 4. A1 已登记的官方来源

普通类常规批第 1 次志愿投档情况表：

- 2025：`https://www.sdzk.cn/NewsInfo.aspx?NewsID=6996`
- 2024：`https://www.sdzk.cn/NewsInfo.aspx?NewsID=6656`
- 2023：`https://www.sdzk.cn/NewsInfo.aspx?NewsID=6279`

一分一段表：

- 2025：`https://www.sdzk.cn/NewsInfo.aspx?NewsID=6943`
- 2024：`https://www.sdzk.cn/NewsInfo.aspx?NewsID=6577`
- 2023：`https://www.sdzk.cn/NewsInfo.aspx?NewsID=6212`

各类别分数线 / 省控线：

- 2025：`https://www.sdzk.cn/NewsInfo.aspx?NewsID=6941`
- 2024：`https://www.sdzk.cn/NewsInfo.aspx?NewsID=6579`
- 2023：`https://www.sdzk.cn/NewsInfo.aspx?NewsID=6210`

选考科目要求：

- 2025/2026：`https://www.sdzk.cn/NewsInfo.aspx?NewsID=6819`

2026 已公开政策：

- 山东省教育厅单招 / 综评通知：`https://edu.shandong.gov.cn/art/2025/12/22/art_107093_10344338.html`
- 2026 年高职（专科）单独招生和综合评价招生院校计划限额：同一教育厅通知附件口径，已登记为 `single_comprehensive_plan_limit`，只用于单招 / 综评计划边界，不得当作普通类正式招生计划。

## 5. 给 B1 的接手说明

B1 不需要再建来源表，应直接：

1. 运行 `npm run backend:migrate`。
2. 运行 `npm run backend:gaokao-sources -- --json`，确认来源文档已登记。
3. 把官方附件或人工下载文件放到 `data/imports/gaokao/official/{year}/`。
4. 用 `backend:gaokao-import-official` 登记文件，拿到 `source_document_id` 和 `import_run_id`。
5. 在投档表、一分一段、省控线解析器里写入：
   - 目标业务表 / raw 表数据
   - `source_document_id`
   - `import_run_id`
   - `total_rows / success_rows / failed_rows / skipped_rows`
   - `created_rows / updated_rows`
   - `error_report_path`

B1 可以补解析器，但不得绕过官网公开来源、验证码、付费墙或版权限制；自动下载失败时继续走人工下载后导入。
