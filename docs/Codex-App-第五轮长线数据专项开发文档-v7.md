# Codex App 第五轮长线开发文档：山东 2023-2025 招生计划、投档/录取数据与章程证据链专项补齐

版本：v7  
适用仓库：`gaoboguang/Academic-Affairs-System`  
主开发环境：Mac / Codex App / 本地仓库  
上传方式：用户通过 GitHub Desktop 手动上传，Codex 不执行 `git push`  
本轮任务类型：长线数据专项，建议使用单个 Codex 长任务窗口连续推进  
目标工作时长：约 8 小时  
核心目标：尽可能一次性补齐山东生源地 2023、2024、2025 年招生计划、投档情况、录取最低分、特殊升学路径结果数据、政策参考和章程限制证据链。

---

## 0. 给 Codex 的最高优先级说明

你是本项目的开发代理。用户不懂编程，也不希望半夜反复介入。你需要尽可能自主完成长线数据补齐任务。

本轮重点不是继续做页面功能，而是：

```text
1. 把 2023-2025 山东生源地招生计划和录取 / 投档数据尽量补全。
2. 优先使用山东省教育招生考试院官网数据。
3. 可以参考高校官网、教育部/阳光高考、山东省教育厅、其他信息站，但必须标注来源等级。
4. 不伪造数据，不把第三方整理数据当官方数据。
5. 对无法自动补齐的数据，必须生成明确的“待人工下载 / 待人工复核 / 官方未发布 / 来源不稳定”清单。
6. 对招生章程限制链，Codex 可以做机器审核，但必须保留证据和置信度，不能无依据批量标记为人工确认。
7. 不执行 git push。用户会用 GitHub Desktop 手动上传。
```

开始前必须阅读：

```text
README.md
AGENTS.md
memory-bank/handoff.md
memory-bank/active-context.md
docs/round4-final-acceptance-report.md
docs/round4-data-completion-result.md
docs/round4-data-completion-plan.md
docs/round3-shandong-pathway-final-report.md
docs/round2-gaokao-recommendation-final-report.md
docs/gaokao-data-coverage-after-round2.md
```

本轮完成后必须生成：

```text
docs/round5-shandong-admission-data-final-report.md
docs/round5-source-discovery-report.md
docs/round5-data-coverage-matrix.md
docs/round5-chapter-review-report.md
docs/round5-manual-download-and-review-list.md
```

并更新：

```text
memory-bank/active-context.md
memory-bank/handoff.md
memory-bank/progress.md
docs/README.md
```

---

## 1. 当前项目状态

第四轮已经完成：

```text
学生批量删除
学生批量调班
调班历史进入学生详情和成长档案
2020-2022 山东一分一段补齐
2020-2022 山东省控线 / 批次线补齐
data-health 从 6 条 P0 数据缺口降为 4 条
```

第四轮数据补齐后的关键状态：

```text
score_rank_segment：22388 条，覆盖 2020-2025
gaokao_score_line：74 条，覆盖 2020-2025
P0 数据缺口：4 条
```

仍然存在的关键缺口：

```text
1. 特殊类型已有招生计划但缺专门录取结果。
2. 2024 山东招生计划数量偏少。
3. 政策参考数量偏少。
4. 招生章程限制链仍有 1748 条待人工复核。
```

本轮要集中处理这些问题，尤其是：

```text
2023-2025 招生计划
2023-2025 投档情况
2023-2025 录取最低分 / 录取情况
特殊类型 / 艺术 / 体育 / 春考 / 单招 / 综评相关可得数据
高校招生章程限制链
```

---

## 2. 用户本轮真实诉求

用户希望：

```text
1. 重点补齐 2023、2024、2025 年招生计划和录取情况。
2. 需要详细且准确的数据。
3. 可以到山东省教育招生考试院官网寻找。
4. 可以参考学校官网等其他可靠来源。
5. 用户之前在山东省教育招生考试院官网找到过往年录取最低分，其中包括多种升学方式和省外院校录取情况。
6. 希望尽量一次性把数据库补齐。
7. 希望 Codex 能连续跑 8 小时左右，第二天用户可以直接查看成果。
```

对第 5 点的处理原则：

```text
可以参考。
如果数据来自山东省教育招生考试院官网，应作为优先官方来源。
如果数据来自高校官网，应作为院校官方来源。
如果数据来自其他网站，只能作为发现线索或第三方参考，除非能追溯到山东省教育招生考试院或高校官网原始附件。
```

注意：“省外各省录取情况”要谨慎解释：

```text
如果是“省外高校在山东招生的录取情况”，属于山东生源地数据，可以导入。
如果是“某高校在其他省份的录取情况”，不属于山东生源地推荐主链路，不应混入山东推荐的 admission_record 主表。可以另建辅助证据表或仅登记为 school_external_reference。
```

---

## 3. 本轮数据源优先级

### 3.1 一级来源：山东省教育招生考试院

优先级最高。可导入主库，并应写入：

```text
gaokao_source_document
gaokao_import_run
file_sha256
source_document_id
import_run_id
```

重点数据类型：

```text
普通类常规批第 1/2/3 次志愿投档情况表
春季高考本科 / 专科批投档情况表
艺术类本科 / 专科批投档情况表
体育类常规批投档情况表
艺术 / 体育 / 春季高考录取情况表或录取最低分表
普通类、艺术类、体育类、春考填报注意事项
录取工作意见
志愿填报百问百答
缺额计划 / 补充计划 / 补充说明
```

### 3.2 二级来源：山东省教育厅、教育部、阳光高考

用于政策、报名条件、招生章程入口、单招 / 综评通知、特殊类型政策。

可写入：

```text
gaokao_policy_reference
gaokao_source_document
gaokao_pathway_rule 的 source_document_id
```

### 3.3 三级来源：高校招生官网

用于：

```text
招生章程
专业限制
体检要求
语种限制
单科要求
性别 / 身高 / 色觉 / 视力要求
校区说明
分专业招生计划
高校发布的山东招生计划或山东录取分数
```

如果高校官网数据和山东省教育招生考试院数据冲突，以省考试院数据为主；高校官网作为补充证据。

### 3.4 四级来源：第三方网站

例如教育在线、高考资讯网、学校公众号转发、地方媒体等。

只能作为：

```text
发现线索
页面备份
辅助对照
待核验来源
```

不允许直接把第三方表格作为“官方已确认数据”写入核心表，除非能追溯到官方附件。

---

## 4. 官方来源发现方向

Codex 需要主动搜索并登记来源。以下是当前已确认应该重点寻找的官方数据类型。

### 4.1 普通类常规批投档情况

至少覆盖：

```text
2023 普通类常规批第 1 次志愿投档情况表
2023 普通类常规批第 2 次志愿投档情况表
2023 普通类常规批第 3 次志愿投档情况表

2024 普通类常规批第 1 次志愿投档情况表
2024 普通类常规批第 2 次志愿投档情况表
2024 普通类常规批第 3 次志愿投档情况表

2025 普通类常规批第 1 次志愿投档情况表
2025 普通类常规批第 2 次志愿投档情况表
2025 普通类常规批第 3 次志愿投档情况表
```

字段重点：

```text
year
province = 山东
batch = 普通类常规批
round = 第1次 / 第2次 / 第3次
college_code
college_name
major_code
major_name
plan_count
min_score
min_rank
source_document_id
import_run_id
```

### 4.2 艺术类投档 / 录取情况

至少覆盖：

```text
2023-2025 艺术类本科批第 1 次志愿投档情况表
2023-2025 艺术类本科批第 1 次志愿录取情况表
2023-2025 艺术类专科批第 1 次志愿投档情况表
2023-2025 艺术类专科批录取情况表（如存在）
```

艺术类别包括但不限于：

```text
美术与设计类 / 美术类
书法类
舞蹈类
音乐类
播音与主持类
表(导)演类
文学编导类
戏剧影视表演类
服装表演类
航空服务艺术类
```

字段重点：

```text
art_track
composite_score
culture_score
professional_score
min_score
min_rank 如果有
admission_min_score
录取最低分
source_document_id
```

注意：艺术类多为综合分或专业类别口径，不能混入普通类裸分位次推荐。

### 4.3 体育类投档 / 录取情况

至少覆盖：

```text
2023-2025 体育类常规批第 1 次志愿投档情况表
2023-2025 体育类常规批第 1 次志愿录取情况表
```

字段重点：

```text
sports_track
composite_score
plan_count
min_score / admission_min_score
source_document_id
```

### 4.4 春季高考投档 / 录取情况

至少覆盖：

```text
2023-2025 春季高考本科批第 1 次志愿投档情况表
2023-2025 春季高考本科批第 1 次志愿录取情况表
2023-2025 春季高考专科批第 1 次志愿投档情况表
2023-2025 春季高考专科批录取情况表（如存在）
```

字段重点：

```text
spring_exam_category
major_category
knowledge_score
skill_score
min_score / admission_min_score
plan_count
source_document_id
```

### 4.5 招生计划

招生计划是本轮最难但最重要的部分。

优先寻找：

```text
2023 山东省普通高校招生填报志愿指南 本科 / 专科
2024 山东省普通高校招生填报志愿指南 本科 / 专科
2025 山东省普通高校招生填报志愿指南 本科 / 专科
山东省教育招生考试院“热点查询 / 招考热点”中的专业招生计划补充信息
普通类、艺术类、体育类、春考各批次缺额计划
高校官网山东招生计划
```

如果官方指南不是公开附件，而需要用户提供纸质书、PDF、导出文件或系统截图，则不要伪造。应生成：

```text
docs/round5-manual-download-and-review-list.md
```

并列出：

```text
需要用户提供的文件名
可能来源
推荐放置目录
导入命令
字段要求
```

---

## 5. 本轮数据表和字段设计

Codex 必须先检查现有模型，能复用就复用，不要重复造表。

### 5.1 已有主链路表

优先复用：

```text
college
major
college_major
enrollment_plan
admission_record
gaokao_admission_plan
gaokao_admission_result
gaokao_source_document
gaokao_import_run
gaokao_policy_reference
gaokao_college_chapter_rule
score_rank_segment
gaokao_score_line
```

### 5.2 可能需要新增的辅助表

如果现有 `admission_record` 无法表达艺术、体育、春考、专科录取最低分等多口径结果，建议新增辅助表，而不是硬塞字段。

可考虑：

```text
gaokao_admission_min_score
gaokao_external_college_admission_reference
gaokao_chapter_review_run
gaokao_chapter_review_item
```

#### gaokao_admission_min_score 建议字段

```text
id
year
province = 山东
student_type
batch
round_no
college_code
college_name
major_code
major_name
category_track
score_type
min_score
min_rank
plan_count
admission_count
source_document_id
import_run_id
source_row_hash
note
created_at
updated_at
is_active
```

用途：保存“录取情况表 / 录取最低分表”类数据，尤其是艺术、体育、春考等不适合直接放普通类 `admission_record` 的数据。

#### gaokao_external_college_admission_reference 建议字段

只在需要保存“高校官网各省录取情况”时使用。

```text
id
college_id
college_name_snapshot
source_province
target_province
year
major_name
score_type
min_score
min_rank
source_url
source_document_id
source_level
note
```

注意：如果 `target_province` 不是山东，不进入山东主推荐，只作为参考证据。

#### gaokao_chapter_review_run / item 建议

用于审核 1748 条章程待复核记录：

```text
gaokao_chapter_review_run
- id
- started_at
- finished_at
- status
- total_count
- reviewed_count
- high_confidence_count
- low_confidence_count
- manual_required_count
- note

gaokao_chapter_review_item
- id
- run_id
- chapter_rule_id
- college_id
- college_name
- major_id
- major_name
- review_status
- confidence_level
- evidence_url
- evidence_title
- evidence_text_excerpt
- extracted_rule_json
- recommendation
- error_message
```

---

## 6. 数据准确性与去重规则

### 6.1 source_document 必须完整

每个导入文件必须有：

```text
province
year
source_type
title
url
official_org
published_at
local_file_path
file_sha256
parser_name
parser_version
status
```

### 6.2 import_run 必须完整

每次导入必须记录：

```text
source_document_id
importer_name
started_at
finished_at
status
total_rows
success_rows
failed_rows
skipped_rows
created_rows
updated_rows
error_report_path
raw_snapshot_path
note
```

### 6.3 去重键建议

普通类投档：

```text
year + province + batch + round_no + college_code + major_code + major_name
```

艺术 / 体育 / 春考：

```text
year + province + student_type + batch + round_no + category_track + college_code + major_code + major_name
```

招生计划：

```text
year + province + batch + student_type + college_code + major_group_code + major_code + major_name + plan_source_type
```

章程限制：

```text
year + college_code + major_code + restriction_type + evidence_url + evidence_hash
```

### 6.4 冲突处理

如果同一 key 出现不同数值：

```text
1. 不直接覆盖。
2. 写入冲突清单。
3. 保留旧值。
4. 在 docs/round5-data-conflicts.md 中记录。
5. 如果新来源是山东省教育招生考试院官方附件，可标记为 recommended_update，但仍要记录差异。
```

---

## 7. 章程限制链 1748 条怎么处理

用户问：Codex 能不能直接审核？

答案：可以让 Codex 做“机器审核”，但不能无依据批量变成“人工已确认”。

本轮允许 Codex 做：

```text
1. 按高校分组读取待复核章程限制。
2. 尝试找到高校招生章程官方页面或 PDF。
3. 提取与专业相关的限制条件。
4. 对比当前 gaokao_college_chapter_rule。
5. 生成证据摘录。
6. 给出置信度：
   high / medium / low / manual_required
7. 将高置信度结果标记为 ai_verified_high_confidence。
8. 将低置信度或无法访问结果保留 manual_required。
```

不允许：

```text
1. 不看证据直接把 1748 条标记完成。
2. 用第三方转载当最终证据。
3. 用 2024 章程代替 2025 / 2026，除非明确标记为历史参考。
4. 学校名相似时混用章程。
5. 把官网打不开的数据标记为已确认。
```

本轮目标：

```text
至少完成 1748 条中的尽可能多条机器预审。
优先审核会影响推荐结果的限制：
- 色盲色弱
- 语种
- 单科成绩
- 身高 / 视力
- 性别
- 体检
- 校区
- 中外合作
- 专业备注
```

---

## 8. 8 小时长线任务设计

本轮建议开一个长线 Codex 窗口，分 8 个阶段。Codex 必须每完成一个阶段就写进度日志并提交本地 commit，避免 8 小时后丢失成果。

### 分支名

```text
codex/r5-longrun-shandong-admission-data-completion
```

### 进度日志

Codex 必须持续更新：

```text
docs/round5-longrun-progress.md
```

格式：

```text
## 时间点
- 当前阶段：
- 已完成：
- 新增来源：
- 成功导入：
- 失败原因：
- 下一步：
- 当前 commit：
```

### 阶段安排

#### 阶段 0：环境和基线，约 30 分钟

```bash
git status
git branch --show-current
npm run backend:data-health -- --json
npm run backend:p0-check -- --json
```

生成或更新：

```text
docs/round5-baseline-before-import.md
```

必须检查：

```bash
git ls-files data/app.db
git status --ignored data/app.db
```

如果 `data/app.db` 没有被 Git 跟踪，必须说明：

```text
代码上传不等于数据库上传。
需要额外提供数据库备份包或确认 data/app.db 是否应该纳入 GitHub Desktop。
```

#### 阶段 1：官方来源发现，约 60-90 分钟

搜索并登记 2023-2025：

```text
普通类常规批第1/2/3次投档情况表
艺术本科 / 专科投档情况表
艺术本科 / 专科录取情况表
体育常规批投档情况表
体育常规批录取情况表
春季高考本科 / 专科投档情况表
春季高考本科 / 专科录取情况表
志愿填报注意事项
录取工作意见
百问百答
缺额计划 / 补充计划
```

生成：

```text
docs/round5-source-discovery-report.md
```

登记来源到数据库：

```text
gaokao_source_document
```

#### 阶段 2：普通类投档数据补齐，约 90 分钟

优先导入：

```text
2023 普通类常规批第2/3次志愿投档情况表
2024 普通类常规批第2/3次志愿投档情况表
2025 普通类常规批第2/3次志愿投档情况表
```

第 1 次志愿已有数据也要复核来源、数量和 row_hash。

目标：

```text
普通类常规批 2023-2025 第1/2/3次志愿投档完整覆盖
```

#### 阶段 3：艺术、体育、春考投档 / 录取情况补齐，约 120 分钟

导入或登记：

```text
艺术类本科批第1次投档
艺术类本科批第1次录取
艺术类专科批第1次投档
艺术类专科批录取
体育类常规批第1次投档
体育类常规批第1次录取
春季高考本科批第1次投档
春季高考本科批第1次录取
春季高考专科批第1次投档
春季高考专科批录取
```

如现有 `admission_record` 不适合表达，新增 `gaokao_admission_min_score`。

#### 阶段 4：招生计划补齐，约 120 分钟

优先处理：

```text
2023 招生计划
2024 招生计划完整性
2025 招生计划完整性
普通类 / 艺术 / 体育 / 春考各批次补充计划
缺额计划
高校官网山东招生计划
```

如果无法自动获得官方完整指南文件：

```text
不要伪造。
不要用第三方表直接覆盖。
生成 manual_download 清单。
```

如果能获取高校官网山东招生计划：

```text
写入 source_level = college_official
不覆盖省考试院数据
作为补充计划证据
```

#### 阶段 5：政策参考补齐，约 60 分钟

补齐：

```text
2023-2025 录取工作意见
2023-2025 志愿填报百问百答
2023-2025 各批次填报注意事项
2025/2026 单招综评通知
春考报名办法
艺术/体育/特殊类型政策
```

写入：

```text
gaokao_policy_reference
```

#### 阶段 6：章程限制链机器预审，约 90-120 分钟

处理 `gaokao_college_chapter_rule` 中待复核记录。

优先级：

```text
1. 已有 evidence_url 的记录。
2. 与 2025 / 2026 招生章程相关的记录。
3. 影响普通类推荐的记录。
4. 影响艺术、体育、春考路径的记录。
```

生成：

```text
docs/round5-chapter-review-report.md
docs/round5-chapter-review-errors.md
```

如果来不及全部处理，必须记录已处理数量和未处理原因。

#### 阶段 7：数据健康、验收和最终报告，约 60 分钟

运行：

```bash
npm run backend:migrate
npm run backend:data-health -- --json
npm run backend:p0-check -- --json
npm run backend:test -- apps/backend/tests -q
npm run check
git diff --check
```

如果时间允许再运行：

```bash
npm run check:all
```

生成：

```text
docs/round5-data-coverage-matrix.md
docs/round5-shandong-admission-data-final-report.md
docs/round5-manual-download-and-review-list.md
```

更新：

```text
memory-bank/active-context.md
memory-bank/handoff.md
memory-bank/progress.md
docs/README.md
```

---

## 9. 给 Codex 的长线任务完整提示词

把下面整段直接复制给 Codex App。

```text
你是 Codex。本窗口是第五轮长线数据专项，目标是连续推进约 8 小时，尽可能一次性补齐山东生源地 2023-2025 招生计划、投档情况、录取最低分、特殊升学路径结果数据、政策参考和章程证据链。

重要要求：
1. 不执行 git push。
2. 用户通过 GitHub Desktop 手动上传。
3. 不伪造数据。
4. 不把第三方整理数据当官方数据。
5. 不把 2026 未发布数据写成已导入。
6. 不把特殊类型、艺体、春考、单招、综评包装成录取概率。
7. 不无依据批量关闭 1748 条章程待复核。
8. 每完成一个阶段必须更新 docs/round5-longrun-progress.md 并本地提交 commit。
9. 如果中途失败，不要停在半成品状态；请记录失败原因、已完成内容和下一步。
10. 如果下载失败，请生成 manual_download 清单，不要假装已导入。

请先创建或切换到分支：
codex/r5-longrun-shandong-admission-data-completion

开始前读取：
README.md
AGENTS.md
memory-bank/handoff.md
memory-bank/active-context.md
docs/round4-final-acceptance-report.md
docs/round4-data-completion-result.md
docs/round4-data-completion-plan.md
docs/round3-shandong-pathway-final-report.md
docs/round2-gaokao-recommendation-final-report.md
docs/gaokao-data-coverage-after-round2.md

阶段 0：基线检查
执行：
git status
git branch --show-current
git ls-files data/app.db
git status --ignored data/app.db
npm run backend:data-health -- --json
npm run backend:p0-check -- --json

生成：
docs/round5-baseline-before-import.md
docs/round5-longrun-progress.md

阶段 1：官方来源发现和登记
重点搜索并登记山东省教育招生考试院 2023-2025：
- 普通类常规批第1/2/3次志愿投档情况表
- 艺术类本科/专科投档情况表
- 艺术类本科/专科录取情况表
- 体育类常规批投档情况表
- 体育类常规批录取情况表
- 春季高考本科/专科投档情况表
- 春季高考本科/专科录取情况表
- 录取工作意见
- 志愿填报注意事项
- 志愿填报百问百答
- 缺额计划 / 补充计划

可参考高校官网、山东省教育厅、教育部/阳光高考和其他网站，但 source_level 必须区分：
sdzk_official
education_department
college_official
ministry_or_chsi
third_party_reference

生成：
docs/round5-source-discovery-report.md

阶段 2：补齐普通类投档数据
补齐或复核：
2023-2025 普通类常规批第1/2/3次志愿投档情况表。
目标是 admission_record / gaokao_admission_result 覆盖各年份、各轮次、各专业+学校。
必须保留 source_document_id、import_run_id、row_hash。
如发生冲突，写 docs/round5-data-conflicts.md，不要静默覆盖。

阶段 3：补齐艺术、体育、春考投档和录取情况
处理：
艺术类本科/专科投档与录取情况
体育类常规批投档与录取情况
春季高考本科/专科投档与录取情况

如果现有 admission_record 无法表达综合分、专业类别、春考类别等，新增合理辅助表，例如 gaokao_admission_min_score。
不要把艺术、体育、春考综合分混入普通类位次推荐。

阶段 4：招生计划专项补齐
优先寻找：
2023-2025 山东省普通高校招生填报志愿指南 本科 / 专科
2023-2025 招生计划补充信息
2023-2025 缺额计划
高校官网山东招生计划

如果没有稳定官方文件，不要伪造。
生成：
docs/round5-manual-download-and-review-list.md

阶段 5：政策参考补齐
补齐：
2023-2025 录取工作意见
2023-2025 志愿填报注意事项
2023-2025 百问百答
单招/综评/春考/艺术/体育/特殊类型相关政策
写入 gaokao_policy_reference，并保留来源。

阶段 6：章程限制链机器预审
处理 gaokao_college_chapter_rule 待复核记录。
可以做机器审核，但必须保存证据：
- evidence_url
- evidence_title
- evidence_text_excerpt
- confidence_level
- review_recommendation

高置信度可标记 ai_verified_high_confidence。
不能无依据标记 confirmed_manual_review。
生成：
docs/round5-chapter-review-report.md
docs/round5-chapter-review-errors.md

阶段 7：最终验收
执行：
npm run backend:migrate
npm run backend:data-health -- --json
npm run backend:p0-check -- --json
npm run backend:test -- apps/backend/tests -q
npm run check
git diff --check

如果时间允许：
npm run check:all

生成：
docs/round5-data-coverage-matrix.md
docs/round5-shandong-admission-data-final-report.md

更新：
memory-bank/active-context.md
memory-bank/handoff.md
memory-bank/progress.md
docs/README.md

最后用中文汇报：
1. 本轮实际运行了多长时间。
2. 新增了多少 source_document。
3. 新增了多少 import_run。
4. 各表补齐前后数量。
5. 2023/2024/2025 普通类、艺术、体育、春考覆盖情况。
6. 招生计划补齐了多少，仍缺多少。
7. 章程限制链审核了多少，确认多少，仍需人工多少。
8. 哪些数据无法自动补齐，原因是什么。
9. 测试是否通过。
10. 是否可以合并到 main。
11. 提醒用户不要忘记用 GitHub Desktop 上传。
```

---

## 10. 本轮成功标准

### 10.1 最低成功标准

```text
完成官方来源发现报告
普通类常规批 2023-2025 第1/2/3次投档表至少完成登记，能导入的已导入
艺术 / 体育 / 春考至少完成 2025 数据登记，能导入的已导入
招生计划缺口生成清单
章程限制链至少完成一批机器审核
data-health 有前后对比
测试通过
```

### 10.2 理想成功标准

```text
2023-2025 普通类常规批第1/2/3次投档完整导入
2023-2025 艺术类本科/专科投档和录取情况完整导入
2023-2025 体育类投档和录取情况完整导入
2023-2025 春季高考本科/专科投档和录取情况完整导入
2023-2025 招生计划官方文件能导入的全部导入
政策参考数量显著增加
1748 条章程待复核至少完成 500 条以上机器预审
P0 数据缺口进一步下降或全部给出明确不可补原因
```

### 10.3 不合格情况

```text
没有 source_document 追溯
用第三方数据冒充官方数据
把无法下载的数据标记为已导入
静默覆盖旧数据
无测试
无最终报告
无 data-health 前后对比
执行了 git push
```

---

## 11. 关于“山东省教育招生考试院往年录取最低分”的使用方式

用户提到的往年录取最低分非常重要，应该纳入本轮重点。

使用原则：

```text
1. 如果页面来自山东省教育招生考试院，优先导入。
2. 如果是“录取情况表”，不要只当投档表处理，应保留 source_type = admission_min_score 或 admission_result。
3. 如果包含多种升学方式，要按 student_type / batch / category_track 拆分。
4. 如果包含省外高校在山东录取情况，仍属于山东生源地，可用于山东推荐。
5. 如果是某高校在全国各省录取分，不直接进入山东主推荐，但可作为高校官网证据补充。
```

建议将“投档情况”和“录取情况”分开：

```text
投档情况：主要用于投档线、最低位次、投档计划数。
录取情况：主要用于录取最低分、录取结果、综合分、类别录取线。
```

不要把二者混成一张表后丢失语义。

---

## 12. 用户第二天应该看什么

用户第二天打开项目后，应该优先看：

```text
docs/round5-shandong-admission-data-final-report.md
docs/round5-data-coverage-matrix.md
docs/round5-source-discovery-report.md
docs/round5-manual-download-and-review-list.md
docs/round5-chapter-review-report.md
```

页面上优先看：

```text
高考数据
山东覆盖
升学方案
高考志愿
```

命令上优先看：

```bash
npm run backend:data-health -- --json
npm run check
```

---

## 13. 给用户的固定回复模板

如果 Codex 中途问你技术问题，可以复制：

```text
我不懂编程，请你根据当前仓库真实代码、山东省教育招生考试院官方来源和数据工程最佳实践自行判断。原则是：
1. 不执行 git push；
2. 不伪造数据；
3. 不用第三方数据冒充官方数据；
4. 能导入的官方数据尽量导入；
5. 不能导入的生成清单和原因；
6. 每阶段更新 docs/round5-longrun-progress.md 并提交本地 commit；
7. 完成后运行测试并用中文汇报。
```

如果 Codex 想停在“只写计划”，可以复制：

```text
请不要只写计划。本窗口就是长线执行任务。请继续搜索官方来源、登记 source_document、导入可导入数据、更新 data-health，并提交本地 commit。不要执行 git push。
```

如果 Codex 下载失败，可以复制：

```text
如果自动下载失败，请不要停止。请把官方来源登记到 source_document，把需要人工下载的文件写入 docs/round5-manual-download-and-review-list.md，并继续处理其他可下载或可导入数据。
```

---

## 14. 最终提醒

本轮是数据专项，不要被新页面功能分散。

最高优先级：

```text
2023-2025 普通类投档 / 录取
2023-2025 艺术 / 体育 / 春考投档和录取最低分
2023-2025 招生计划完整性
政策参考
章程限制链机器预审
```

低优先级：

```text
新 UI
复杂算法
96 志愿自动编排
跨省公开平台
全国省份扩展
```

如果 8 小时内无法全部完成，以“数据真实、来源可追溯、进度可恢复”为第一原则。
