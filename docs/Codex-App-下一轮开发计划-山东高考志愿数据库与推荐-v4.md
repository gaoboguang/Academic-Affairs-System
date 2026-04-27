# Codex App 下一轮开发执行文档 v4

项目：`gaoboguang/Academic-Affairs-System` / 本地教务工具  
主题：**山东生源地高考志愿数据库补齐 + 基于学生考试成绩/预估高考成绩的冲稳保推荐**  
开发方式：用户不懂编程，全部交给 Codex App 执行  
主开发环境：Mac 本机  
文档日期：2026-04-25

---

## 0. 给 Codex 的最高优先级说明

你是本项目下一轮开发的执行者。用户本人没有编程基础，不负责判断技术细节。你必须直接读取仓库、修改代码、运行验证、提交分支，并用中文解释结果。

本轮目标不是泛泛新增页面，而是围绕 **数据库补齐、山东高考志愿数据可信度、普通类高考志愿推荐可用性** 做一轮集中开发。

必须遵守：

1. **以当前 `main` 为基线开发。** 当前主线已完成窗口 2-9 第一轮整合，远程 GitHub 已可查到：
   - `3b796b3 feat: integrate windows 2-9 final acceptance`
   - `a7c7148 docs: record windows 2-9 main merge`
2. **不要重开旧的 Windows 主线。** 当前主阵地是 Mac，本轮继续按 Mac 开发、Mac 验收、Mac 交付。
3. **本轮优先数据库，不优先 UI 花活。** UI 可以做，但必须服务于数据补齐、数据质量、推荐解释。
4. **只做山东生源地。** 不要扩到全国省份，不要做跨省推荐。
5. **普通类夏季高考优先。** 特殊类型、艺体、春考、单招、综评本轮可以继续作为数据字典和初筛边界，但不得包装成完整录取概率。
6. **推荐结果必须带数据来源和风险解释。** 不能只给“能上/不能上”。
7. **不得伪造 2026 数据。** 2026 数据只导入已公开、可核验的数据；未公开的普通类招生计划要标记为 `not_published` 或 `pending_official_release`，不能假装完整。
8. **不得绕过登录、验证码、付费墙或版权限制。** 数据源优先使用山东省教育招生考试院、山东省教育厅、高校官网公开发布的数据；如网页无法自动抓取，则实现“人工下载文件后导入”的工具。
9. **所有数据库迁移必须走 Alembic。** 修改真实 `data/app.db` 前必须备份。
10. **每个窗口必须提交自己的分支。** 不要把大量成果堆在未提交工作区。

---

## 1. 当前项目真实基线

### 1.1 已确认技术栈

当前仓库是本地单机教务系统 / 本地教务工具，技术栈为：

- 后端：`FastAPI + SQLAlchemy + SQLite + Alembic`
- 前端：`Vue 3 + TypeScript + Vite + Element Plus`
- 桌面端：`Electron`
- 主数据库：`data/app.db`
- 当前常用命令：
  - `npm run dev`
  - `npm run start:local`
  - `npm run stop:local`
  - `npm run backend:data-health`
  - `npm run backend:p0-check -- --json`
  - `npm run check`
  - `npm run check:all`

### 1.2 当前主线状态

当前远程 `main` 已包含第一轮窗口 2-9 整合成果。

已知主线验收结果：

- 后端测试：`69 passed`
- 前端测试：`128 passed`
- E2E：`31 passed`
- `npm run check:all`：通过
- `npm run backend:p0-check -- --json`：通过，`ok: true`
- `git diff --check`：通过

下一轮开发前，Codex 必须先在本地再次执行：

```bash
git status
git pull --ff-only
npm run backend:data-health -- --json
npm run check
```

如果当前机器运行结果与上述主线记录不一致，以本机实际结果为准，并先修复启动/测试问题。

### 1.3 当前数据库和高考数据基线

根据仓库交接记录，当前项目已经有较多高考相关数据和规则，但仍存在明显缺口。

已知数据基础：

- 应用主库：`data/app.db`
- 已并入或物化过的高考相关数据包括：
  - `gaokao_college`
  - `gaokao_admission_plan`
  - `gaokao_admission_result`
  - `score_rank_segment`
  - `province_score_transform_rule`
  - `subject_requirement_dict`
  - `province_volunteer_rule`
  - `special_type_rule`
- 交接记录中曾确认的业务表规模包括：
  - `college ≈ 3455`
  - `major ≈ 13959`
  - `admission_record ≈ 170385`
  - `enrollment_plan ≈ 6338`
  - `college_major ≈ 60761`
  - `employment_direction ≈ 14`
  - `major_employment_mapping ≈ 12975`

本轮 Codex 开工后必须重新运行：

```bash
npm run backend:data-health -- --json
```

并把真实输出保存或更新到：

```text
docs/gaokao-data-baseline-2026-04-25.md
```

### 1.4 当前已知 P0 数据缺口

第一轮验收后仍保留 6 条 P0 数据缺口，下一轮必须重点处理：

1. 特殊类型已有计划但缺少专门录取结果。
2. 山东 2024 招生计划数量偏少。
3. 一分一段缺 2020-2023。
4. 省控线缺 2020-2023。
5. 政策参考数量偏少。
6. 章程限制链仍有大量待复核记录，交接记录曾显示 `1748` 条待复核。

本轮用户特别强调：**优先补齐最近三年数据。**

因此本轮短期目标不是补 2020-2022，而是优先确保：

```text
2023、2024、2025 山东普通类夏季高考：
- 一分一段表
- 普通类常规批第 1 次志愿投档情况表
- 各类别分数线 / 省控线
- 招生计划或填报志愿指南中能公开导入的计划数据
- 选考科目要求
- 章程限制和专业特殊要求来源记录
```

2026 数据则按“已公开即导入、未公开即监控”的方式处理。

---

## 2. 本轮产品目标

本轮要把系统从“已有高考志愿功能”推进到：

> **山东生源地普通类高考志愿推荐的数据库可用、推荐逻辑可解释、结果可追溯、普通用户可使用。**

### 2.1 用户希望实现的功能

用户原始需求：

1. 根据学生每一次考试成绩，综合推荐考试院校。
2. 支持自主填写预估高考成绩来推荐学校。
3. 推荐学校分为：冲、稳、保。
4. 重点补齐往年数据，尤其最近三年。
5. 2026 招生已经开始，需要把今年已公开的招生数据纳入系统。
6. 暂时只做山东生源地。

### 2.2 本轮必须落地的业务能力

#### A. 数据库补齐能力

系统要能管理和导入山东高考志愿推荐所需的基础数据：

- 院校基础库
- 专业基础库
- 院校-专业关系
- 2023-2025 普通类投档数据
- 2023-2025 一分一段表
- 2023-2025 分数线 / 省控线
- 招生计划数据
- 2026 已公开招生数据
- 选考科目要求
- 招生章程限制
- 数据来源、发布时间、导入批次、校验状态

#### B. 成绩推算能力

系统要支持两种推荐入口：

1. **学生考试成绩入口**
   - 选择学生。
   - 选择近几次校内考试。
   - 系统综合考试总分、年级位次、班级位次、学科稳定性和趋势，生成一个“预估高考分数 / 预估位次区间”。
   - 如果没有学校历史高考校准数据，必须标记为“校内估算，仅供参考”。

2. **手动预估成绩入口**
   - 用户直接填写预估高考总分。
   - 可选填写预估全省位次。
   - 如果只填分数，则系统根据一分一段表换算位次。
   - 如果 2026 一分一段尚未发布，则允许用 2025 一分一段做临时换算，但必须明确标记“按上一年一分一段估算”。

#### C. 冲稳保推荐能力

系统要按山东普通类平行志愿实际逻辑推荐。

山东普通类常规批不是简单“学校志愿”，而是以：

```text
专业（专业类） + 学校
```

为一个志愿单位。UI 可以展示“推荐院校”，但后端和推荐明细必须保留“专业（专业类）+学校”粒度。

推荐结果至少分为：

- 冲：有机会但风险较高。
- 稳：位次匹配度较好。
- 保：安全边际较高。
- 不推荐 / 仅关注：数据不足、选科不符、章程限制、计划缺失、特殊类型不适用。

每条推荐必须解释：

- 使用了哪几年数据。
- 最近一年最低投档分 / 位次。
- 三年位次波动。
- 计划数变化。
- 当前学生预估位次与历史最低位次差距。
- 是否符合选科要求。
- 是否有章程限制。
- 数据置信度。
- 为什么被归为冲/稳/保。

#### D. 数据质量看板

在 `/gaokao-data` 或推荐中心中增加“山东普通类推荐数据覆盖”视图：

- 2023/2024/2025 数据是否完整。
- 2026 数据当前状态：已导入 / 未公开 / 待导入 / 待核验。
- 投档数据覆盖率。
- 一分一段覆盖率。
- 省控线覆盖率。
- 招生计划覆盖率。
- 选科要求覆盖率。
- 章程限制复核进度。
- 数据源列表。
- 导入批次和错误报告。

---

## 3. 外部数据源基线

Codex 必须优先使用官方来源。以下是本轮应接入或至少登记到 source registry 的数据源。

### 3.1 2023-2025 山东普通类投档数据

优先导入：

- 2025：山东省2025年普通类常规批第1次志愿投档情况表  
  `https://www.sdzk.cn/NewsInfo.aspx?NewsID=6996`
- 2024：山东省2024年普通类常规批第1次志愿投档情况表  
  `https://www.sdzk.cn/NewsInfo.aspx?NewsID=6656`
- 2023：山东省2023年普通类常规批第1次志愿投档情况表  
  `https://www.sdzk.cn/NewsInfo.aspx?NewsID=6279`

这些页面通常提供 `.xls` 附件。Codex 要实现：

- 自动识别附件链接；如失败，则支持用户把 `.xls` 文件放到 `data/imports/gaokao/official/` 后执行导入。
- 解析字段：年份、省份、批次、院校代码、院校名称、专业代码、专业名称、计划数、投档最低分、最低位次、专业备注等。
- 所有行保留 source document id。

### 3.2 2023-2025 一分一段表

优先导入：

- 2025：`https://www.sdzk.cn/NewsInfo.aspx?NewsID=6943`
- 2024：`https://www.sdzk.cn/NewsInfo.aspx?NewsID=6577`
- 2023：`https://www.sdzk.cn/NewsInfo.aspx?NewsID=6212`

用途：

- 手动预估分数 → 换算全省位次。
- 校内考试推算 → 与全省排名做粗略映射。
- 历年分数等效换算。

必须注意：

- 一分一段是按当年试卷和考生群体生成，不能直接跨年用分数比较。
- 推荐算法应优先使用位次，分数只作为展示和换算辅助。

### 3.3 2023-2025 各类别分数线 / 省控线

优先导入：

- 2025：`https://www.sdzk.cn/NewsInfo.aspx?NewsID=6941`
- 2024：`https://www.sdzk.cn/NewsInfo.aspx?NewsID=6579`
- 2023：`https://www.sdzk.cn/NewsInfo.aspx?NewsID=6210`

用途：

- 判断是否达到一段线、二段线、特殊类型招生控制线。
- 生成推荐边界提示。
- 为特殊类型 / 艺体 / 春考保留初筛规则。

### 3.4 2025/2026 选考科目要求

山东省教育招生考试院 2025-03-17 公告说明：

- `2024通用版普通高校拟在山东招生专业（类）选考科目要求` 适用于 2025 年和 2026 年参加高考的考生。
- `2027通用版` 适用于 2027 年及以后参加高考的考生。

数据源：

- `https://www.sdzk.cn/NewsInfo.aspx?NewsID=6819`

本轮要确保：

- 推荐时必须检查学生选科是否满足专业要求。
- 不满足选科要求的专业不能进入“冲稳保”，只能进入“不推荐/选科不符”。
- 选科要求必须能在推荐理由中展示。

### 3.5 2026 已公开招生数据

截至本开发文档日期，已经能确认 2026 山东高职（专科）单独招生和综合评价招生政策已经发布，报名时间、考试方式、计划安排原则已经公开。

主要数据源：

- 山东省教育厅《关于做好2026年高职（专科）单独考试招生和综合评价招生工作的通知》  
  `https://edu.shandong.gov.cn/art/2025/12/22/art_107093_10344338.html`

本轮处理原则：

1. 2026 单招 / 综评数据可以建立数据源登记、院校计划限额、院校章程抓取或手动导入能力。
2. 2026 夏季高考普通类正式招生计划如果尚未完整公开，不得伪造。
3. 推荐 2026 普通类时，可以使用：
   - 2023-2025 投档数据；
   - 2025/2026 适用的选科要求；
   - 2026 已公开招生计划，若有；
   - 尚未公开的 2026 普通类计划必须标记为 `pending_official_release`。
4. UI 必须提示：

```text
2026 普通类正式招生计划如未完全公开，当前推荐主要基于 2023-2025 历史投档数据和已公开规则，正式填报前必须以山东省教育招生考试院最终发布的招生计划和高校章程为准。
```

---

## 4. 推荐算法设计要求

本轮可以参考成熟高考志愿项目常见思路，但不得盲目复制第三方代码。核心原则是：

```text
位次优先 + 分数辅助 + 近三年波动 + 招生计划变化 + 选科/章程约束 + 可解释冲稳保
```

### 4.1 推荐粒度

后端推荐候选必须是：

```text
专业（专业类） + 学校 + 年份 + 批次 + 考生类别
```

前端可以聚合成学校卡片，但每张学校卡片必须能展开到专业明细。

### 4.2 输入模型

推荐输入至少包括：

```text
student_id 可选
province = 山东
student_type = general / 普通类
subject_combination = 选科组合
source_mode = manual_score / manual_rank / exam_projection
predicted_score 可选
predicted_rank 可选
selected_exam_ids 可选
risk_preference = conservative / balanced / aggressive
target_year = 2026
batch = 普通类常规批
college_preferences 可选
major_preferences 可选
region_preferences 可选
exclude_private / exclude_high_fee 可选
```

### 4.3 成绩推算模型

#### 4.3.1 手动预估成绩

如果用户输入 `predicted_score`：

1. 优先用目标年份一分一段换算位次。
2. 若目标年份一分一段不存在：
   - 用最近一年一分一段表换算。
   - 标记 `rank_projection_basis = previous_year_score_rank_segment`。
   - 在 UI 中提示“按上一年一分一段估算”。

如果用户输入 `predicted_rank`：

- 直接使用该位次作为主排序依据。
- 分数只作为展示字段。

#### 4.3.2 根据学生考试成绩推算

如果用户选择学生和多次校内考试：

1. 读取该学生历次考试总分、年级名次、班级名次、学科成绩。
2. 计算：
   - 最近一次考试位次；
   - 最近 N 次考试加权平均位次；
   - 位次趋势；
   - 学科短板；
   - 波动区间。
3. 若系统没有“本校历届高考校准数据”，则只能生成：
   - 校内预估分；
   - 校内预估位次；
   - 粗略全省位次区间；
   - 置信度 `low` 或 `medium`。
4. 后续可以新增“本校历史高考校准表”，例如：

```text
school_gaokao_calibration
- year
- grade_rank
- grade_size
- gaokao_score
- gaokao_rank
- subject_combination
```

有该表后，系统才能把校内排名更可靠地映射到山东全省位次。

### 4.4 冲稳保分层建议

Codex 需要把阈值做成可配置，不要硬编码死。

推荐初始配置：

```text
candidate_rank = 学生预估全省位次，数值越小越好
historical_min_rank = 历年该专业+学校最低投档位次，数值越小越好
rank_margin = historical_min_rank - candidate_rank
rank_margin_ratio = rank_margin / historical_min_rank
```

解释：

- `rank_margin > 0`：学生位次优于历史最低位次，有安全边际。
- `rank_margin = 0`：刚好贴近历史最低位次。
- `rank_margin < 0`：学生位次弱于历史最低位次，需要冲。

建议分类：

```text
冲：
- 最近三年中，学生位次接近或略弱于历史最低位次；
- rank_margin_ratio 大约在 -0.12 ~ 0.03；
- 或者某一年命中过，但波动较大。

稳：
- 学生位次优于多数年份历史最低位次；
- rank_margin_ratio 大约在 0.03 ~ 0.18；
- 三年波动不大，计划没有明显缩招。

保：
- 学生位次明显优于历史最低位次；
- rank_margin_ratio 大于 0.18；
- 最近三年稳定，且无明显选科/章程风险。
```

不同风险偏好可以调整：

```text
conservative：少冲，多保
balanced：冲稳保均衡
aggressive：冲的比例增加，但必须保留足够保底项
```

### 4.5 三年数据权重

最近三年建议权重：

```text
2025：0.50
2024：0.30
2023：0.20
```

如果 2026 正式招生计划公开：

- 使用 2026 计划数做计划变化校正。
- 但不能使用 2026 投档结果，因为投档发生在录取阶段后。

计划变化校正建议：

```text
plan_change_factor = 2026计划数 / 2025计划数

如果明显扩招：适度降低风险
如果明显缩招：提高风险
如果计划缺失：标记 plan_missing，不降低风险
```

### 4.6 必须展示的风险标签

推荐结果至少支持这些风险标签：

```text
rank_projection_from_previous_year
rank_projection_from_school_exam
historical_data_missing
three_year_data_incomplete
plan_missing
plan_decreased
subject_requirement_mismatch
chapter_pending_review
special_requirement_detected
score_line_only_reference
special_type_reference_only
not_enough_safety_choices
```

---

## 5. 数据库开发重点

Codex 开工后必须先审计现有模型，不要重复建表。优先查找：

```text
apps/backend/app/models*
apps/backend/app/schemas*
apps/backend/app/repositories*
apps/backend/app/services/gaokao.py
apps/backend/app/services/_recommendations_*.py
apps/backend/app/importers/*
apps/backend/alembic/versions/*
```

如果已有表能承接，不要重复创建。

### 5.1 数据源登记表

如果项目尚无完整 source registry，需要新增或补齐：

```text
gaokao_source_document
- id
- province
- year
- source_type
- title
- url
- official_org
- published_at
- fetched_at
- local_file_path
- file_sha256
- parser_name
- parser_version
- status
- note
```

用途：

- 每条导入数据能追溯到官方来源。
- 数据质量看板能显示“数据从哪里来”。
- 后续用户质疑推荐时，可以追溯。

### 5.2 导入批次表

```text
gaokao_import_run
- id
- source_document_id
- importer_name
- started_at
- finished_at
- status
- total_rows
- success_rows
- failed_rows
- skipped_rows
- created_rows
- updated_rows
- error_report_path
- raw_snapshot_path
- note
```

### 5.3 一分一段表

如果现有 `score_rank_segment` 不完整，补齐字段：

```text
score_rank_segment
- id
- province
- year
- category
- score
- same_score_count
- cumulative_count
- rank_min
- rank_max
- source_document_id
```

### 5.4 省控线 / 分数线表

```text
gaokao_score_line
- id
- province
- year
- category
- batch
- line_name
- score
- source_document_id
```

### 5.5 投档 / 录取记录表

现有 `admission_record` 如已能承载，优先扩展：

```text
admission_record
- province
- year
- category
- batch
- college_code
- college_name
- major_code
- major_name
- plan_count
- min_score
- min_rank
- lowest_score_same_rank_count 可选
- subject_requirement_snapshot
- source_document_id
- data_quality_status
```

### 5.6 招生计划表

现有 `enrollment_plan` 如已能承载，优先扩展：

```text
enrollment_plan
- province
- year
- category
- batch
- college_code
- college_name
- major_code
- major_name
- plan_count
- tuition
- duration
- campus
- subject_requirement
- remark
- source_document_id
- data_quality_status
```

### 5.7 推荐运行快照

为了让每次推荐可复查，需要新增或补齐：

```text
gaokao_recommendation_run
- id
- student_id
- target_year
- province
- category
- source_mode
- predicted_score
- predicted_rank
- rank_projection_basis
- selected_exam_ids_json
- risk_preference
- data_version
- created_at
```

```text
gaokao_recommendation_candidate
- id
- run_id
- college_id
- major_id
- college_name_snapshot
- major_name_snapshot
- recommendation_bucket  # rush/stable/safe
- probability_score 可选
- rank_margin
- rank_margin_ratio
- years_used_json
- historical_summary_json
- risk_flags_json
- explanation_text
- source_document_ids_json
```

### 5.8 学生预估成绩快照

```text
student_gaokao_projection
- id
- student_id
- target_year
- source_mode
- predicted_score
- predicted_rank
- rank_range_low
- rank_range_high
- confidence_level
- selected_exam_ids_json
- calculation_detail_json
- created_at
```

---

## 6. 本轮开发阶段安排

不要一次性开太多窗口。推荐分三批。

### 第一批：数据库基线和数据源框架

先开：

```text
窗口 A0：数据库基线审计与数据缺口确认
窗口 A1：数据源登记、导入批次、官方数据导入框架
```

A0、A1 完成并提交后，再开第二批。

### 第二批：最近三年数据补齐和推荐核心

可以并行开：

```text
窗口 B1：2023-2025 山东普通类投档数据 / 一分一段 / 省控线导入
窗口 B2：2026 已公开招生数据监控与导入入口
窗口 B3：学生考试成绩 → 高考预估分 / 位次推算
窗口 B4：冲稳保推荐算法与解释引擎
```

注意：B4 依赖 B1 的数据结构，B4 开工前必须先读取 A1/B1 已提交内容。

### 第三批：前端、报告、验收

```text
窗口 C1：推荐工作台 UI 和数据质量看板
窗口 C2：推荐报告、Excel 导出、打印页一致性
窗口 C3：最终集成、测试、合并、交接文档
```

---

## 7. Codex 窗口提示词

下面每段都可以直接复制给 Codex App。

---

### 窗口 A0：数据库基线审计与数据缺口确认

```text
你是窗口 A0：数据库基线审计与数据缺口确认。

当前项目是本地教务工具，后端 FastAPI + SQLAlchemy + SQLite + Alembic，前端 Vue 3 + TypeScript + Vite + Element Plus。当前 main 已合并第一轮窗口 2-9 成果，远程最新主线包含提交 a7c7148 和 3b796b3。

本轮重点是山东生源地高考志愿数据库补齐和普通类高考推荐。用户不懂编程，请你全权处理。

任务：

1. 确认当前分支基于 main：
   - git status
   - git pull --ff-only
   - git log --oneline -5

2. 运行数据健康检查：
   - npm run backend:data-health -- --json
   - npm run backend:p0-check -- --json

3. 审计当前数据库和模型：
   - data/app.db 中有哪些高考相关表
   - 每个表当前记录数
   - 2023/2024/2025 山东普通类数据覆盖情况
   - 2026 数据覆盖情况
   - 一分一段表覆盖情况
   - 省控线覆盖情况
   - 投档/录取记录覆盖情况
   - 招生计划覆盖情况
   - 选科要求覆盖情况
   - 章程限制待复核数量

4. 生成文档：
   docs/gaokao-data-baseline-2026-04-25.md

文档必须包括：
- 当前数据表清单
- 当前数据量
- 2023-2025 最近三年缺口
- 2026 已有数据 / 未公开数据 / 待导入数据
- 本轮最优先补齐的数据
- 哪些数据只能初筛，不能用于完整录取推荐

5. 不要新增功能，不要大改代码。最多只补必要的审计脚本或文档。

6. 验证：
   - npm run backend:data-health -- --json
   - git diff --check

完成后请提交分支：
branch: codex/r2-a0-gaokao-data-baseline
commit message: docs: audit gaokao data baseline for round 2

最后用中文汇报：
- 数据库当前真实状态
- 最近三年缺什么
- 2026 数据现在能导入什么
- 下一窗口应该先做什么
```

---

### 窗口 A1：数据源登记与导入框架

```text
你是窗口 A1：山东高考官方数据源登记与导入框架。

请先读取：
- AGENTS.md
- memory-bank/handoff.md
- docs/gaokao-data-baseline-2026-04-25.md（如果存在）
- apps/backend/app/importers/*
- apps/backend/app/services/gaokao.py
- apps/backend/app/models*
- apps/backend/alembic/versions/*

任务目标：
建立或补齐高考官方数据源登记、导入批次、导入错误报告框架，为 2023-2025 山东普通类数据和 2026 已公开数据导入做准备。

必须做：

1. 审计现有 import batch / source document 相关表，避免重复建表。
2. 如果缺少 source registry，请用 Alembic 新增或扩展：
   - gaokao_source_document
   - gaokao_import_run
   - 必要的 source_document_id 外键或引用字段
3. 支持官方来源登记：
   - 山东省教育招生考试院
   - 山东省教育厅
   - 高校官网招生章程
4. 支持本地文件导入目录：
   - data/imports/gaokao/official/
   - data/imports/gaokao/manual/
5. 增加或补齐 CLI 命令，例如：
   - npm run backend:gaokao-sources
   - npm run backend:gaokao-import-official
   如果现有命令体系不适合，请沿 scripts/backend-cli.cjs 扩展。
6. 所有导入必须生成：
   - total_rows
   - success_rows
   - failed_rows
   - skipped_rows
   - error_report_path
   - source_document_id
7. 不要实现复杂抓取，不要绕过限制。网页附件无法自动下载时，必须支持人工下载后导入。

验收：
- 干净库可 alembic upgrade head
- npm run backend:test 相关定向测试通过
- npm run backend:data-health -- --json 仍能运行
- git diff --check 通过

提交：
branch: codex/r2-a1-gaokao-source-import-framework
commit message: feat: add gaokao official source import framework

中文汇报：
- 新增/复用哪些表
- 新增哪些命令
- 如何给后续窗口导入 2023-2025 数据
- 哪些地方仍需后续窗口补实现
```

---

### 窗口 B1：2023-2025 山东普通类核心数据导入

```text
你是窗口 B1：2023-2025 山东普通类核心数据导入。

本窗口目标：补齐最近三年山东普通类推荐必需数据。

官方目标数据源：

普通类常规批第1次志愿投档情况表：
- 2025：https://www.sdzk.cn/NewsInfo.aspx?NewsID=6996
- 2024：https://www.sdzk.cn/NewsInfo.aspx?NewsID=6656
- 2023：https://www.sdzk.cn/NewsInfo.aspx?NewsID=6279

一分一段表：
- 2025：https://www.sdzk.cn/NewsInfo.aspx?NewsID=6943
- 2024：https://www.sdzk.cn/NewsInfo.aspx?NewsID=6577
- 2023：https://www.sdzk.cn/NewsInfo.aspx?NewsID=6212

各类别分数线：
- 2025：https://www.sdzk.cn/NewsInfo.aspx?NewsID=6941
- 2024：https://www.sdzk.cn/NewsInfo.aspx?NewsID=6579
- 2023：https://www.sdzk.cn/NewsInfo.aspx?NewsID=6210

任务：

1. 读取窗口 A1 的数据源登记和导入框架。
2. 为以上三类数据分别实现导入器：
   - 普通类投档表导入器
   - 一分一段表导入器
   - 分数线导入器
3. 如果官方附件无法直接下载，支持人工把 xls/pdf/png 放到：
   data/imports/gaokao/official/{year}/
   然后命令行导入。
4. 投档表解析后要写入或更新 admission_record / 相关表。
5. 一分一段写入 score_rank_segment。
6. 分数线写入 gaokao_score_line 或现有等价表。
7. 所有数据必须关联 source_document_id。
8. 导入后生成覆盖矩阵：
   docs/gaokao-shandong-2023-2025-coverage.md

注意：
- 不要把 2023-2025 数据混成一年。
- 不要只存分数，必须存最低位次。
- 推荐算法以后优先用位次，不是直接比裸分。
- 字段名不一致时要写 parser normalization，不要手工硬改数据。

验收：
- npm run backend:test 相关导入测试通过
- npm run backend:data-health -- --json 能看到 2023-2025 覆盖改善
- git diff --check 通过

提交：
branch: codex/r2-b1-shandong-2023-2025-official-data
commit message: feat: import shandong 2023 2025 gaokao official data

中文汇报：
- 导入了哪些年份
- 每年多少条
- 还缺哪些官方文件
- 是否满足普通类推荐所需最低数据条件
```

---

### 窗口 B2：2026 已公开招生数据监控与导入入口

```text
你是窗口 B2：2026 已公开招生数据监控与导入入口。

本窗口目标：处理 2026 已经开始的招生数据，但不得伪造未公开的普通类正式招生计划。

已知 2026 官方来源：
山东省教育厅《关于做好2026年高职（专科）单独考试招生和综合评价招生工作的通知》
https://edu.shandong.gov.cn/art/2025/12/22/art_107093_10344338.html

任务：

1. 建立 2026 数据状态模型或扩展现有数据健康结构：
   - published
   - imported
   - pending_official_release
   - not_applicable
   - manual_review_required

2. 登记 2026 单招 / 综评政策来源。

3. 如果能从官方或高校官网公开页面获取单招/综评招生章程和计划，则建立导入入口；如果不能稳定抓取，则支持人工导入。

4. 对 2026 夏季高考普通类：
   - 不要假设正式招生计划已经完整公开。
   - 在数据健康看板中明确显示“普通类正式招生计划：待官方发布/待导入”。
   - 推荐引擎可以用 2023-2025 历史数据和 2025/2026 适用选科要求，但必须显示风险提示。

5. 增加文档：
   docs/gaokao-2026-data-watchlist.md

文档必须说明：
- 2026 哪些数据已公开
- 哪些数据未公开
- 哪些数据需要人工导入
- 系统如何避免把未公开数据当成完整数据

验收：
- npm run backend:data-health -- --json
- npm run frontend:build
- git diff --check

提交：
branch: codex/r2-b2-2026-gaokao-data-watchlist
commit message: feat: track 2026 shandong gaokao data publication status

中文汇报：
- 2026 当前可做什么
- 2026 当前不能做什么
- 推荐页面应该如何提示用户
```

---

### 窗口 B3：学生考试成绩到高考预估分/位次推算

```text
你是窗口 B3：学生考试成绩到高考预估分/位次推算。

本窗口目标：让系统可以根据学生历次考试成绩生成高考预估分数/位次区间，也支持手动填写预估高考分数。

任务：

1. 审计现有考试、成绩、分析接口：
   - Exam
   - ScoreRecord
   - 学生分析
   - 年级排名
   - 历次考试趋势

2. 新增或补齐后端服务：
   - 根据学生和 selected_exam_ids 生成 projection
   - 根据 manual_score + 年份一分一段生成 projected_rank
   - 根据 manual_rank 直接生成 projection

3. 新增 projection snapshot：
   - student_id
   - target_year
   - source_mode
   - predicted_score
   - predicted_rank
   - rank_range_low
   - rank_range_high
   - confidence_level
   - selected_exam_ids_json
   - calculation_detail_json

4. 算法要求：
   - 最近考试权重更高。
   - 同时考虑总分、年级名次、趋势、波动。
   - 如果缺少本校历史高考校准数据，必须标记 confidence_level = low/medium，并显示“校内估算”。
   - 如果使用上一年一分一段换算，必须标记 previous_year_score_rank_segment。

5. 新增 API：
   - 预估成绩计算
   - 预估成绩保存
   - 预估成绩列表/详情

6. 新增测试：
   - 手动分数换位次
   - 手动位次直用
   - 多次考试综合估算
   - 缺少一分一段时给出明确错误或 fallback

验收：
- npm run backend:test 相关测试通过
- npm run frontend:build 如有前端改动
- git diff --check

提交：
branch: codex/r2-b3-student-gaokao-score-projection
commit message: feat: add student gaokao score projection

中文汇报：
- 支持哪些输入方式
- 是否可以根据历次考试估算
- 哪些情况下置信度较低
- 下一窗口推荐算法如何调用
```

---

### 窗口 B4：冲稳保推荐算法与解释引擎

```text
你是窗口 B4：山东普通类冲稳保推荐算法与解释引擎。

本窗口目标：基于 2023-2025 山东普通类历史投档数据、一分一段、选科要求和预估位次，生成冲稳保推荐。

任务：

1. 审计现有推荐相关服务：
   - apps/backend/app/services/_recommendations_*.py
   - apps/backend/app/exporters/recommendations.py
   - 推荐历史和志愿草稿相关模型

2. 实现或扩展山东普通类推荐入口：
   - 输入学生 projection 或 manual score/rank
   - 输入 target_year=2026
   - 输入 subject_combination
   - 输出冲/稳/保候选

3. 推荐粒度必须是：
   专业（专业类） + 学校

4. 算法必须使用：
   - 最近三年最低投档位次
   - 三年位次波动
   - 招生计划变化
   - 选科要求
   - 章程限制状态
   - 数据完整度

5. 初始权重：
   - 2025: 0.50
   - 2024: 0.30
   - 2023: 0.20

6. 推荐结果必须包括：
   - bucket: rush/stable/safe
   - rank_margin
   - rank_margin_ratio
   - score_summary
   - years_used
   - historical_summary
   - risk_flags
   - explanation_text
   - source_document_ids

7. 不满足选科要求的候选不能进入冲稳保。

8. 数据不足候选必须显示为“仅关注 / 数据不足”，不能混入保底。

9. 特殊类型暂时只允许初筛，不得输出完整录取把握。

10. 新增测试：
   - 位次优于历史数据时进入稳/保
   - 位次略弱时进入冲
   - 选科不符时排除
   - 三年数据缺失时降置信度
   - 计划缺失时加风险标签

验收：
- npm run backend:test 相关测试通过
- npm run backend:data-health -- --json
- git diff --check

提交：
branch: codex/r2-b4-shandong-rush-stable-safe-recommendation
commit message: feat: add shandong rush stable safe recommendation engine

中文汇报：
- 推荐算法用了哪些数据
- 冲稳保如何判定
- 有哪些风险标签
- 结果能不能用于普通类推荐
```

---

### 窗口 C1：推荐工作台 UI 和数据质量看板

```text
你是窗口 C1：推荐工作台 UI 和数据质量看板。

目标：让非技术用户可以在页面上完成：选择学生/填写预估分 -> 查看冲稳保推荐 -> 查看数据来源和风险。

任务：

1. 审计现有前端页面：
   - /recommendations
   - /gaokao-data
   - 学生分析相关页面

2. 新增或增强“山东普通类推荐”工作台：
   - 入口一：选择学生 + 选择考试记录
   - 入口二：手动填写预估高考分数/位次
   - 选择目标年份，默认 2026
   - 选择选科组合
   - 风险偏好：保守 / 均衡 / 冲刺
   - 生成推荐

3. 推荐结果展示：
   - 冲
   - 稳
   - 保
   - 数据不足 / 仅关注

4. 每条结果必须能展开：
   - 专业（专业类）+学校
   - 历年最低分/位次
   - 位次差距
   - 计划数变化
   - 选科要求
   - 章程限制
   - 风险标签
   - 数据来源
   - 推荐理由

5. 数据质量看板：
   - 2023-2025 覆盖矩阵
   - 2026 发布状态
   - 未公开/待导入/已导入状态
   - P0 缺口

6. 页面文案必须对普通用户友好。
   不要出现只有程序员能看懂的字段名。

验收：
- npm run frontend:lint
- npm run frontend:test
- npm run frontend:build
- 如涉及 E2E，补最小冒烟流程
- git diff --check

提交：
branch: codex/r2-c1-shandong-recommendation-workbench-ui
commit message: feat: add shandong recommendation workbench ui

中文汇报：
- 用户如何操作
- 页面能看到哪些风险
- 数据缺失时页面如何提示
```

---

### 窗口 C2：推荐报告、Excel 导出、打印页一致性

```text
你是窗口 C2：推荐报告、Excel 导出、打印页一致性。

目标：冲稳保推荐结果不仅能在页面看，还能导出为学校内部可用的报告。

任务：

1. 审计现有报表中心和推荐导出：
   - apps/backend/app/exporters/recommendations.py
   - apps/backend/app/exporters/reports.py
   - 推荐打印页
   - 报表中心相关前端组件

2. 增加“山东普通类冲稳保推荐报告”：
   - 学生基本信息
   - 输入来源：考试估算 / 手动预估
   - 预估分数和位次
   - 冲稳保汇总
   - 推荐明细
   - 风险说明
   - 数据来源
   - 2026 数据未公开提示

3. Excel 至少包含：
   - 汇总页
   - 冲列表
   - 稳列表
   - 保列表
   - 数据不足/风险列表
   - 数据来源页

4. 打印页必须适合保存为 PDF。

5. 不要把风险标签原始英文直接展示给用户，要映射成中文。

验收：
- npm run backend:test 相关 exporter 测试通过
- npm run frontend:build
- git diff --check

提交：
branch: codex/r2-c2-shandong-recommendation-report-export
commit message: feat: add shandong recommendation report export

中文汇报：
- 新增了哪些报告
- Excel 有哪些 sheet
- 风险如何展示
```

---

### 窗口 C3：最终集成、测试、合并、交接文档

```text
你是窗口 C3：最终集成、测试、合并、交接文档。

目标：整合本轮 A0/A1/B1/B2/B3/B4/C1/C2 的成果，处理冲突，跑全量验收，合并回 main。

任务：

1. 确认所有分支是否提交并推送/存在于本地。
2. 逐个审查分支差异。
3. 按顺序合并：
   A0 -> A1 -> B1 -> B2 -> B3 -> B4 -> C1 -> C2
4. 处理冲突。
5. 运行：
   - git diff --check
   - npm run backend:data-health -- --json
   - npm run backend:p0-check -- --json
   - npm run check
   - npm run check:all
6. 生成最终文档：
   - docs/round2-gaokao-recommendation-final-report.md
   - docs/gaokao-data-coverage-after-round2.md
   - memory-bank/handoff.md 更新
   - memory-bank/progress.md 更新
7. 提交：
   branch: codex/r2-final-gaokao-recommendation-integration
   commit message: feat: finalize round 2 shandong gaokao recommendation
8. 合并回 main 前，必须确认工作区干净。
9. 合并 main 后再次运行：
   - npm run backend:data-health -- --json
   - npm run check:all
10. 推送到 GitHub。

中文汇报必须包括：
- main 最新 commit hash
- 本轮新增了什么
- 数据库补齐到了什么程度
- 2023-2025 数据是否完整
- 2026 数据当前状态
- 推荐功能是否可用
- 仍有哪些风险
- 下一轮建议做什么
```

---

## 8. 用户给 Codex 的统一限制语

每个窗口开头都可以附加：

```text
重要限制：

我本人不懂编程，请你直接完成开发，不要让我做技术判断。

你必须读取当前仓库真实代码后再动手，不要凭空假设文件结构。

本轮重点是山东生源地高考志愿数据库补齐和普通类冲稳保推荐。不要扩展到全国，不要重构无关模块。

不要伪造 2026 普通类招生计划或投档数据。未公开的数据必须标记为待官方发布。

不要绕过登录、验证码、付费墙或版权限制。官方附件不能自动下载时，就做人工下载后导入。

每次修改后必须运行相关测试。完成后必须提交当前分支，并用中文说明：改了什么、涉及哪些文件、运行了哪些命令、是否通过、下一步该做什么。
```

---

## 9. 本轮验收标准

### 9.1 数据库验收

至少达到：

- 2023-2025 山东普通类投档数据覆盖状态明确。
- 2023-2025 一分一段覆盖状态明确。
- 2023-2025 省控线覆盖状态明确。
- 每条核心数据能追溯 source document。
- 数据导入有批次、有错误报告、有校验状态。
- 2026 数据状态能区分已公开 / 未公开 / 待导入。

### 9.2 推荐验收

至少达到：

- 支持手动输入预估分数推荐。
- 支持手动输入预估位次推荐。
- 支持选择学生历次考试生成预估推荐。
- 推荐结果分为冲、稳、保。
- 推荐单位保留“专业（专业类）+学校”粒度。
- 推荐理由可解释。
- 选科不符不会进入推荐。
- 数据不足不会被包装成保底。
- 2026 普通类计划未公开时有明确提示。

### 9.3 测试验收

最终必须通过：

```bash
npm run backend:data-health -- --json
npm run backend:p0-check -- --json
npm run check
npm run check:all
git diff --check
```

如果 `check:all` 因浏览器或环境问题失败，Codex 必须说明原因，并至少通过：

```bash
npm run backend:test
npm run frontend:lint
npm run frontend:test
npm run frontend:build
```

---

## 10. 不允许做的事

1. 不允许把特殊类型推荐包装成完整录取概率。
2. 不允许只按分数推荐，不看位次。
3. 不允许只推荐学校，不保留专业粒度。
4. 不允许把 2026 未公开普通类招生计划伪造为已导入。
5. 不允许把用户校内考试名次直接当作山东全省位次。
6. 不允许把数据缺失候选放进“保”。
7. 不允许重构整个推荐中心。
8. 不允许修改 `AGENTS.md` 的生成结果，除非同步维护其规则来源。
9. 不允许在没有备份的情况下直接改 `data/app.db`。
10. 不允许提交未测试的大量代码。

---

## 11. 下一轮之后的潜在方向

本轮完成后，下一轮可以考虑：

1. 本校历史高考校准数据导入。
2. 山东 2026 普通类正式招生计划发布后的增量导入。
3. 志愿表自动排序和 96 个志愿模拟填报。
4. 章程限制自动复核：体检、色弱色盲、语种、单科成绩、性别、校区。
5. 职业方向与专业匹配增强。
6. 普通类本科 / 专科分层推荐。
7. 面向班主任的批量学生志愿推荐。

当前不要提前做这些，除非本轮基础数据和推荐闭环已经稳定。

---

## 12. 给用户的操作建议

你不需要判断技术细节。按下面顺序给 Codex 开窗口即可：

第一批：

```text
窗口 A0
窗口 A1
```

A0/A1 完成后，再开：

```text
窗口 B1
窗口 B2
窗口 B3
```

B1 完成并确认数据结构后，再开：

```text
窗口 B4
窗口 C1
```

最后开：

```text
窗口 C2
窗口 C3
```

不要一开始全部开满，因为本轮涉及数据库迁移和导入器，冲突风险比普通前端开发更高。

---

## 13. 本文档引用的公开数据源

Codex 开发时应优先核验以下官方数据源：

- 山东省教育招生考试院：2025 普通类常规批第 1 次志愿投档情况表  
  https://www.sdzk.cn/NewsInfo.aspx?NewsID=6996
- 山东省教育招生考试院：2024 普通类常规批第 1 次志愿投档情况表  
  https://www.sdzk.cn/NewsInfo.aspx?NewsID=6656
- 山东省教育招生考试院：2023 普通类常规批第 1 次志愿投档情况表  
  https://www.sdzk.cn/NewsInfo.aspx?NewsID=6279
- 山东省教育招生考试院：2025 夏季高考文化成绩一分一段表  
  https://www.sdzk.cn/NewsInfo.aspx?NewsID=6943
- 山东省教育招生考试院：2024 夏季高考文化成绩一分一段表  
  https://www.sdzk.cn/NewsInfo.aspx?NewsID=6577
- 山东省教育招生考试院：2023 夏季高考文化成绩一分一段表  
  https://www.sdzk.cn/NewsInfo.aspx?NewsID=6212
- 山东省教育招生考试院：2025 夏季高考各类别分数线  
  https://www.sdzk.cn/NewsInfo.aspx?NewsID=6941
- 山东省教育招生考试院：2024 夏季高考各类别分数线  
  https://www.sdzk.cn/NewsInfo.aspx?NewsID=6579
- 山东省教育招生考试院：2023 夏季高考各类别分数线  
  https://www.sdzk.cn/NewsInfo.aspx?NewsID=6210
- 山东省教育招生考试院：2025/2026 适用的选考科目要求公告  
  https://www.sdzk.cn/NewsInfo.aspx?NewsID=6819
- 山东省教育厅：2026 高职（专科）单独考试招生和综合评价招生通知  
  https://edu.shandong.gov.cn/art/2025/12/22/art_107093_10344338.html

