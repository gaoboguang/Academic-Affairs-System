# Codex 本地第六轮开发文档：山东招生数据库补齐任务

版本：v6-local-codex
执行环境：Codex CLI 本地运行（Mac）
分支建议：codex/r6-local-shandong-db-completion
核心目标：补齐山东省 2023-2025 年招生计划及录取数据，确保数据库完整

---

## 1. 任务背景

1. 上轮第五轮长线任务（r5-longrun-shandong-admission-data-completion）已经完成阶段性成果，但数据库里的招生数据仍不完整。
2. 2023、2024、2025 年普通类、艺术类、体育类及春考招生计划、投档和录取情况未完全补齐。
3. 章程限制链仍有部分待人工复核条目。
4. 当前目标是 **全权交给本地 Codex CLI 自动完成数据库补齐**，尽量减少人工下载或人工干预。

---

## 2. 工作边界

### 允许做

- 全量搜索和抓取山东省教育招生考试院、各高校官网、阳光高考等官方数据
- 下载官方附件（pdf、xls、xlsx、doc、docx）
- 使用已有解析器或新增解析器解析下载的数据
- 自动将解析后的数据导入本地数据库 `data/app.db`
- 生成日志、导入报告、数据覆盖矩阵
- 自动更新 `gaokao_admission_result`、`admission_record`、`gaokao_policy_reference` 等表

### 禁止做

- 伪造未发布或非官方数据
- 修改非数据库相关功能（UI、报表、学生批量操作等）
- 干扰其他分支或 main
- 不验证来源和解析，直接写入数据库
- 不关闭章程待复核条目

---

## 3. 本轮任务阶段

### 阶段 1：数据源确认

- 自动检查 `docs/round5-cloud-source-discovery-report.md` 与 `data/seed/round5_gaokao_source_documents.json`
- 确认 2023-2025 所有官方招生计划、投档和录取数据来源
- 对未下载或超时失败的附件生成下载清单，并尝试重新下载

### 阶段 2：解析器执行与增强

- 使用现有解析器处理下载附件
- 对不能解析的新文件类型，自动生成解析器模板
- 确保每条记录包含：
  - year, province, student_type, batch, round_no, college_code, college_name, major_code, major_name, plan_count, min_score, min_rank, source_document_id, import_run_id, source_row_hash
- 对艺术、体育、春考单独录入，确保 `admission_min_score` 或综合分字段正确

### 阶段 3：数据库导入

- 将解析后的数据批量写入 `data/app.db`
- 按类型分表导入：
  - `gaokao_admission_result`
  - `admission_record`
  - `gaokao_policy_reference`
- 对导入成功和失败记录生成日志
- 更新 `data/coverage-matrix`

### 阶段 4：数据覆盖验证

- 执行：
  ```bash
  npm run backend:data-health -- --json
  npm run backend:p0-check -- --json
  npm run check
  npm run check:all
  git diff --check
  ```
- 确认 P0 数据缺口降到 0 或最小
- 确认数据库与 source_document 对应完整

### 阶段 5：章程限制链辅助预审

- 对剩余 1748 条待复核章程进行自动连通性检查
- 标记可自动校验条目并生成报告，保留人工复核优先级
- 不直接修改 `review_status`

### 阶段 6：最终报告生成

- 生成 `docs/round6-shandong-db-completion-final-report.md`
- 内容包括：
  - 完整数据库覆盖情况
  - 仍需人工干预条目
  - 数据覆盖矩阵
  - 本轮增量统计

---

## 4. 文件路径与产物

- 数据源存放：`data/imports/gaokao/official/<year>/`
- Seed 文件：`data/seed/round6_gaokao_source_documents.json`
- 导入报告：`docs/round6-shandong-db-completion-final-report.md`
- 数据覆盖矩阵：`docs/round6-data-coverage-matrix.md`
- 章程辅助预审报告：`docs/round6-chapter-review-sample.md`

---

## 5. Codex CLI 提示词示例

```text
你是 Codex CLI，本轮任务是全自动补齐山东省 2023-2025 年招生数据库。
1. 自动抓取官方招生计划、投档和录取数据。
2. 下载附件并解析。
3. 将数据写入本地 data/app.db。
4. 生成日志、报告和数据覆盖矩阵。
5. 自动辅助章程限制链预审。
6. 不伪造数据、不修改其他功能、不关闭待人工复核条目。
7. 完成后生成 docs/round6-shandong-db-completion-final-report.md。
```

---

## 6. 建议执行方式

- 新建分支：`codex/r6-local-shandong-db-completion`
- Codex CLI 连续运行任务
- 监控输出日志，确认下载、解析、导入顺利
- 完成后提交分支并生成最终报告