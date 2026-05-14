# 数据库字段对照表（v1, 基线日期 2026-05-13）

本文件是 `data/app.db` 的「真值表」。项目里之所以前端经常出错，根因是数据库同时住着**两套 schema**：
**应用层**（ORM + alembic 管）和 **raw 层**（导入脚本、老 handoff db 塞进来的）。本文把两层放在一起对齐，以后写代码先看这份，不要再凭记忆猜字段。

- 基线分支：`main`
- 基线表数：113（ORM 覆盖 91，raw 22，其中 `alembic_version` 不计业务）
- 基线 alembic head：`20260510_0032`
- 基线产出时间：2026-05-13

> 维护规则：
> - 新增表/字段：在对应章节补行；空表变成非空请更新「空表清单」。
> - raw 字段被淘汰：在「raw→应用层 物化通道」章节打勾即可，不要就地删行，保留迁移痕迹。
> - 命名、枚举有新约定：先改「命名与枚举对照」，再改代码。

---

## 目录

1. [总览：两层 schema 共存的现状](#1-总览两层-schema-共存的现状)
2. [表族地图](#2-表族地图)
3. [raw 层 22 张表 — 字段清单](#3-raw-层-22-张表--字段清单)
4. [应用层 vs raw 层 字段对照](#4-应用层-vs-raw-层-字段对照)
5. [命名与枚举对照](#5-命名与枚举对照)
6. [动态探测点（代码里的「字段漂移补丁」）](#6-动态探测点代码里的字段漂移补丁)
7. [raw→应用层 物化通道](#7-raw应用层-物化通道)
8. [空表清单（45 张）](#8-空表清单45-张)
9. [第二 SQLite 句柄（gaokao sidecar）的来龙去脉](#9-第二-sqlite-句柄gaokao-sidecar的来龙去脉)
10. [常见踩坑 FAQ](#10-常见踩坑-faq)
11. [附录 A：前端类型同步流程](#附录-a前端类型同步流程)
12. [附录 B：写新页面 / 新接口的标准流程](#附录-b写新页面--新接口的标准流程)
13. [附录 C：B 计划后的结构变化（2026-05-13）](#附录-cb-计划后的结构变化2026-05-13)

---

## 1. 总览：两层 schema 共存的现状

| 来源 | 谁创建 | 是否走 alembic | 命名风格 | 代表表 |
|---|---|---|---|---|
| 应用层 | `apps/backend/app/models/*.py` + `apps/backend/alembic/versions/*.py` | 是 | 简洁英文：`college.name`、`major.name`、`admission_record.*`、`*_json` 后缀 | `college`、`major`、`admission_record`、`enrollment_plan`、`province_volunteer_rule`、`student`、`exam`、`score_record` |
| raw 层 — 爬虫/脚本直写 | `scripts/import_gaokao_scraper_bundle.py:1752` 起的 `CREATE TABLE IF NOT EXISTS` | 否 | 快照风格：`*_snapshot` 后缀、中文候选类型 | `gaokao_admission_plan`、`gaokao_admission_result` |
| raw 层 — handoff 合并 | `scripts/merge_handoff_gaokao_db.py` → `apps/backend/app/utils/gaokao_sync.py` 的整表 copy | 否 | 老 mac 端 schema | `gaokao_college`、`gaokao_major`、`gaokao_score_line`、`score_rank_segment`、`gaokao_subject_requirement*`、`gaokao_*_dict` 等 |

代码入口：

- 应用层 session：`apps/backend/app/api/deps.py:15` `get_db_session`
- raw 层 sidecar session：`apps/backend/app/api/deps.py:21` `get_gaokao_db_session`（见 §9）
- raw→应用层物化：`apps/backend/app/utils/gaokao_materialize.py:22` `materialize_gaokao_structured_tables`
- 多路 fallback：`apps/backend/app/services/gaokao.py:860` `_build_shandong_section_from_raw_or_model`
- 字段动态探测：`apps/backend/app/services/_recommendations_score_rank.py:128` `PRAGMA table_info(score_rank_segment)`

---

## 2. 表族地图

### 2.1 基础数据（参考表，前端下拉都走这里）

`academic_year`、`semester`、`grade`、`school_class`、`subject`、`dict_type`、`dict_item`、`config_item`

### 2.2 学生域

`student`、`student_guardian`、`student_class_history`、`student_class_transfer_batch`、`student_class_transfer_item`、`student_attachment`、`student_career_preference`、`student_growth_record`、`student_growth_attachment`、`student_planning_goal`、`student_planning_task`、`student_planning_note`、`student_pathway_profile`、`student_pathway_evaluation`、`student_gaokao_score_projection`

### 2.3 教师 / 班级 / 排课 / 工作量

`teacher`、`teacher_title_history`、`teaching_assignment`、`class_adviser_assignment`、`class_honor`、`timetable_batch`、`timetable_entry`、`period_definition`、`workload_rule_version`、`workload_rule_item`、`teacher_workload_result`、`teacher_workload_extra`

### 2.4 考试与成绩

`exam`、`exam_subject`、`score_record`、`score_total_snapshot`、`score_subject_snapshot`、`score_class_mapping`、`score_exam_student_context`、`score_target_line`、`score_import_batch`、`score_import_profile`、`score_question`、`score_question_record`、`score_question_knowledge_point`、`score_question_import_batch`、`score_knowledge_snapshot`、`knowledge_point`、`knowledge_point_alias`、`error_reason_tag`

### 2.5 应用层高考志愿域（ORM）

`college`、`college_alias`、`college_major`、`major`、`major_employment_mapping`、`employment_direction`、`enrollment_plan`、`admission_record`、`province_volunteer_rule`、`province_score_transform_rule`、`subject_requirement_dict`、`special_type_rule`、`gaokao_pathway`、`gaokao_pathway_rule`、`recommendation_scheme`、`recommendation_result`、`volunteer_draft`、`volunteer_draft_item`、`college_profile_detail`、`college_year_summary`、`major_profile_detail`、`college_major_profile`、`gaokao_source_document`、`gaokao_import_run`

### 2.6 raw 层高考志愿域（非 ORM，22 张）

`data_import_batch`、`data_import_error_log`、`score_rank_segment`、
`gaokao_admission_plan`、`gaokao_admission_result`、
`gaokao_college`、`gaokao_college_chapter_rule`、`gaokao_college_tag`、
`gaokao_major`、`gaokao_major_career_mapping`、`gaokao_career_direction`、
`gaokao_score_line`、`gaokao_score_transform_rule`、
`gaokao_subject_requirement`、`gaokao_subject_requirement_dict`、
`gaokao_batch_dict`、`gaokao_pathway_dict`、
`gaokao_province_rule`、`gaokao_province_rule_version`、
`gaokao_policy_reference`、`gaokao_source_registry`

### 2.7 系统 / 审计 / 评价

`audit_log`、`backup_record`、`import_job`、`stored_file`、`report_export_record`、
`evaluation_template`、`evaluation_question`、`evaluation_batch`、`evaluation_response`、`evaluation_summary`、
`adviser_quant_rule_version`、`adviser_quant_rule_item`、`adviser_quant_record`、`adviser_quant_record_attachment`

<!-- CHUNK-BOUNDARY-A -->

## 3. raw 层 22 张表 — 字段清单

所有 raw 表当前都物理上落在 `data/app.db`，ORM 不覆盖；代码要么用 `sqlalchemy.text` 直查，
要么通过 sidecar session 访问。

### 3.1 `data_import_batch` — 0 行

统一导入批次。定义在 `scripts/import_gaokao_official.py` 等脚本里，现在长期空，保留以兼容旧批次号。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | |
| batch_code | VARCHAR(64) | 人工批次号 |
| domain | VARCHAR(64) | 例如 `gaokao` |
| data_type | VARCHAR(64) | 例如 `admission_result` |
| province | VARCHAR(50) | |
| target_year | INTEGER | |
| source_name | VARCHAR(255) | |
| source_title | VARCHAR(255) | |
| version_label | VARCHAR(64) | |
| status | VARCHAR(32) | |
| total_records | INTEGER | |
| started_at, finished_at | DATETIME | |
| created_at, updated_at | DATETIME | |

### 3.2 `data_import_error_log` — 0 行

`data_import_batch` 对应的错误行。含 `batch_id FK -> data_import_batch.id`、`row_number`、`field_name`、`error_code`、`error_message`、`raw_payload`。

### 3.3 `score_rank_segment` — 24,662 行（热）

一分一段。`_recommendations_score_rank.py` 运行时 PRAGMA 决定用哪个 rank 列。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | |
| province | VARCHAR(32) | 原文「山东」，别名见 §5 |
| year | INTEGER | |
| score_type | VARCHAR(64) | 例如 `summer_total`、`art`、`sports`、`spring_exam` |
| subject_group | VARCHAR(128) | 部分年份用科类组合 |
| score | NUMERIC(8,2) | |
| segment_count | INTEGER | 当分段人数 |
| cumulative_count | INTEGER | 累计 |
| rank_value | INTEGER | 与 cumulative_count 二选一（取决于年份） |
| source_level, source_title, source_url, local_source_path, parser_script_name, published_at, review_status, source_record_hash, data_version_label | | raw 通用血缘字段 |
| import_batch_id, source_document_id, import_run_id | INTEGER | 三种批次号并存 |

### 3.4 `gaokao_admission_plan` — 66,739 行（热）

院校专业招生计划。字段命名带 `*_snapshot`（导入时刻冻结的名字）。

核心字段：`province`, `year`, `candidate_type`, `batch_name`, `round_no`, `pathway_code`, `enrollment_type`, `education_level`,
`college_id -> gaokao_college.id`, `college_code_snapshot`, `college_name_snapshot`,
`major_id -> gaokao_major.id`, `major_code_snapshot`, `major_name_snapshot`, `major_group_code`,
`plan_count`, `duration_years`, `tuition`, `campus`,
`subject_requirement_text`, `subject_requirement_code`, `special_plan_tag`,
`major_note`, `authority_scope`, `plan_scope`, `update_type`, `merge_status`,
`parse_confidence`, `original_major_text`, `original_update_text`,
+ raw 血缘字段（`source_*`, `published_at`, `review_status`, `source_record_hash`, `data_version_label`, `import_batch_id`, `source_document_id`, `import_run_id`）。

### 3.5 `gaokao_admission_result` — 282,260 行（最热）

历年实际投档结果。

核心字段：`province`, `year`, `candidate_type`, `batch_name`, `round_no`,
`college_id -> gaokao_college.id`, `college_code_snapshot`, `college_name_snapshot`,
`major_id -> gaokao_major.id`, `major_code_snapshot`, `major_name_snapshot`,
`min_score`, `min_rank`, `avg_score`, `max_score`, `control_line`,
`plan_count`, `actual_filed_count`, `original_min_rank_text`, `remark`,
+ raw 血缘字段同上。

### 3.6 `gaokao_college` — 3,344 行（热）

raw 院校主档。

字段：`standard_id`（UNIQUE）, `college_code`, `college_name`, `alias_names`(JSON), `school_identifier`(UNIQUE),
`province`, `city`, `education_level`, `school_nature`, `affiliation`, `school_type`, `level_tags`(JSON),
`official_site`, `recruit_site`, `chapter_url`, `summary`,
`status`, `is_deleted`, `reference_payload`(JSON), `chapter_fallback_url`, `chapter_fallback_source_type`,
`ranking_national`, `founded_year`, `recommendation_rate`, `admission_phone`, `admission_email`, `mailing_address`,
`national_featured_major_text`, `provincial_featured_major_text`, `featured_major_text`。

### 3.7 `gaokao_college_chapter_rule` — 2,052 行

院校招生章程抽取的硬性限制（身高、视力、政治面貌等）。

核心字段：`province`, `year`, `college_id -> gaokao_college.id`, `college_code_snapshot`, `college_name_snapshot`,
`chapter_url`, `chapter_query_entry_url`, `chapter_source_type`, `retrieval_status`,
`chapter_title`, `language_requirement`, `single_subject_requirement`, `gender_requirement`,
`political_status_requirement`, `height_requirement`, `vision_requirement`, `color_vision_requirement`,
`physical_exam_requirement`, `tuition_note`, `campus_note`, `other_risk_note`,
`parse_confidence`, `status`,
`chapter_fallback_url`, `chapter_fallback_source_type`, `chapter_fallback_note`, `chapter_fallback_verification_status`,
+ raw 血缘字段。UNIQUE `(province, year, college_code_snapshot, college_name_snapshot)`。

### 3.8 `gaokao_college_tag` — 9,226 行

院校标签多对一。字段：`college_id -> gaokao_college.id`, `tag_code`, `tag_name`, `tag_source`；UNIQUE `(college_id, tag_code, tag_name)`。

### 3.9 `gaokao_major` — 8,790 行

raw 专业主档。字段：`standard_id`(UNIQUE), `major_code`, `major_name`, `discipline_category`, `major_category`, `degree_type`,
`is_special_major`, `is_controlled_major`, `duration_years`, `summary`,
`career_direction_tags`(JSON), `employment_tags`(JSON), `status`, `is_deleted`。

### 3.10 `gaokao_major_career_mapping` — 0 行

raw 专业→职业方向映射，字段：`major_id`, `career_direction_id`, `relevance_score`, `note`；UNIQUE `(major_id, career_direction_id)`。

### 3.11 `gaokao_career_direction` — 0 行

raw 职业方向字典。字段：`direction_code`(UNIQUE), `direction_name`, `direction_category`, `summary`, `status`。

### 3.12 `gaokao_score_line` — 74 行

省控线/批次线。字段：`province`, `year`, `candidate_type`, `batch_name`, `line_type`, `score`, `remark` + raw 血缘字段。

### 3.13 `gaokao_score_transform_rule` — 48 行

赋分规则（山东等级赋分等）。字段：`province`, `year`, `exam_mode`, `subject_name`,
`raw_score_min/max`, `transformed_score`, `transformed_score_min/max`, `version_code`,
`rule_expression`, `rule_payload`(JSON), `grade_code`, `grade_name`, `ratio_from`, `ratio_to`,
`status` + raw 血缘字段。

### 3.14 `gaokao_subject_requirement` — 180,788 行（最热）

院校专业选科要求（明细）。字段：`province`, `version_name`, `applies_exam_year_from/to`, `education_level`,
`college_id`, `college_code_snapshot`, `college_name_snapshot`,
`major_id`, `major_code_snapshot`, `major_name_snapshot`,
`requirement_dict_id -> gaokao_subject_requirement_dict.id`, `requirement_code`, `requirement_type`,
`required_subjects`(JSON), `original_requirement_text`, `note`, `page_number` + raw 血缘字段。

### 3.15 `gaokao_subject_requirement_dict` — 27 行

选科要求的字典表（去重后的表达式）。字段：`requirement_code`(UNIQUE), `requirement_name`, `requirement_type`,
`normalized_expression`, `required_subjects`(JSON), `subject_count`, `note`, `status`。

### 3.16 `gaokao_batch_dict` — 32 行

批次字典。字段：`province_scope`, `batch_code`, `batch_name`, `pathway_code`, `year_from`, `year_to`, `sort_order`, `note`, `status`；UNIQUE `(province_scope, batch_code, pathway_code)`。

### 3.17 `gaokao_pathway_dict` — 7 行

升学路径字典。字段：`pathway_code`(UNIQUE), `pathway_name`, `pathway_category`, `sort_order`, `summary`, `status`。

### 3.18 `gaokao_province_rule` — 2 行

省级志愿填报规则（历史快照）。字段：`version_id -> gaokao_province_rule_version.id`, `province`, `year`,
`candidate_type`, `exam_mode`, `total_score`, `score_composition`, `batch_name`, `round_no`,
`volunteer_unit_type`, `max_volunteer_count`, `filing_rule`, `admission_basis`, `cannot_mix_rule`,
`is_support_major_group`, `is_support_collecting`, `score_mode_note`, `notes`, `raw_payload`(JSON)。

### 3.19 `gaokao_province_rule_version` — 2 行

省级规则版本信息。字段：`province`, `year`, `version_code`, `version_name`, `exam_mode`, `is_active`,
`source_title`, `source_url`, `local_source_path`, `published_at`, `note`, `import_batch_id`, `status`；UNIQUE `(province, year, version_code)`。

### 3.20 `gaokao_policy_reference` — 15 行

政策原文索引。字段：`province`, `year`, `policy_type`, `title`, `url`, `local_path`, `summary`,
`source_level`, `version_id -> gaokao_province_rule_version.id`, `import_batch_id`, `published_at`, `status`。

### 3.21 `gaokao_source_registry` — 17 行

抓取源注册表。字段：`source_code`(UNIQUE), `domain`, `source_name`, `province_scope`, `topic`,
`source_level`, `source_type`, `platform`, `trust_level`, `priority`, `entry_url`,
`allow_domains`(JSON), `must_include`(JSON), `exclude_keywords`(JSON), `tags`(JSON), `note`, `status`。

### 3.22 `alembic_version`

只存 `version_num`，业务忽略；当前 `20260510_0032`。


## 4. 应用层 vs raw 层 字段对照

> 所有「前端可见」的字段都来自应用层。raw 层由后端服务吸收、映射后再暴露。前端不要直接拿 raw 字段名。

### 4.1 院校

| 概念 | 应用层 `college` | raw `gaokao_college` |
|---|---|---|
| 主键 | id | id |
| 学校名 | `name` | `college_name` |
| 学校代码 | `college_code` | `college_code` |
| 别名 | 关联表 `college_alias.alias_name` | `alias_names` (JSON 数组) |
| 省份 | `province` | `province` |
| 城市 | `city` | `city` |
| 学校类型 | `school_type` | `school_type` |
| 层次标签 | `school_level_tags_json` (JSON 数组) | `level_tags` (JSON 数组) |
| 官网 | `website` | `official_site` |
| 简介 | `intro` | `summary` |
| 招生站 | 未暴露 | `recruit_site` |
| 章程地址 | 未暴露（见 `gaokao_college_chapter_rule.chapter_url`） | `chapter_url` |
| 支持艺术类 | `supports_art` (bool) | 无（由 `school_type` + 录取记录推断） |
| 教育层次 | 无 | `education_level` |
| 办学性质 | 无 | `school_nature` |
| 主管部门 | 无（应用层在 `college_profile_detail.authority_department`） | `affiliation` |
| 软科全国排名 | `college_profile_detail.ruanke_rank` | `ranking_national` |
| 建校年份 | 无 | `founded_year` |
| 招生电话 | `college_profile_detail.phone` | `admission_phone` |
| 招生邮箱 | `college_profile_detail.email` | `admission_email` |
| 通讯地址 | `college_profile_detail.address` | `mailing_address` |
| 特色专业文本 | 无 | `featured_major_text` 等三列 |
| 备注 | `note` | 无 |
| 软删除 | `is_active` (bool) | `is_deleted` (bool) + `status` |

### 4.2 专业

| 概念 | 应用层 `major` | raw `gaokao_major` |
|---|---|---|
| 主键 | id | id |
| 专业名 | `name` | `major_name` |
| 专业代码 | `major_code` | `major_code` |
| 学科门类 | `category` | `discipline_category` |
| 专业大类 | 无（就用 category） | `major_category` |
| 学位类型 | 无 | `degree_type` |
| 修业年限 | `major_profile_detail.schooling_years` | `duration_years` |
| 简介 | 无（ `major_profile_detail.summary`） | `summary` |
| 方向 | `direction` / `major_profile_detail.direction` | 无 |
| 就业路径 | `career_path` | `career_direction_tags` / `employment_tags`(JSON) |
| 是否艺术类 | `is_art_related` | 无 |
| 软删除 | `is_active` | `is_deleted` + `status` |

### 4.3 录取结果

| 概念 | 应用层 `admission_record` | raw `gaokao_admission_result` |
|---|---|---|
| 粒度 | `(year, province, batch, college_id, major_id, student_type, art_track)` UNIQUE | `(province, year, candidate_type, batch_name, round_no, college_name_snapshot, major_name_snapshot, ...)` 非 UNIQUE |
| 院校关联 | `college_id` (NOT NULL) | `college_id`（nullable）+ `college_code_snapshot` + `college_name_snapshot` |
| 专业关联 | `major_id`（nullable） | `major_id`（nullable）+ `major_code_snapshot` + `major_name_snapshot` |
| 批次 | `batch` | `batch_name` + `round_no`（征集志愿等） |
| 学生类型 | `student_type` 英文枚举：`general/art/sports/spring_exam/independent_recruitment/comprehensive_evaluation` | `candidate_type` 中文「普通类/艺术类/...」或英文别名，对照见 §5 |
| 艺术轨道 | `art_track` | 无（并入 candidate_type） |
| 选科要求 | `subject_requirement`（文本） | 无（从 `gaokao_subject_requirement` 关联） |
| 最低分/位次 | `min_score` `min_rank` | `min_score` `min_rank` |
| 均分/最高分 | `avg_score` `max_score` | `avg_score` `max_score` |
| 控制线 | 无 | `control_line` |
| 计划数 | `plan_count` | `plan_count` |
| 实际投档数 | 无 | `actual_filed_count` |
| 位次原文 | 无 | `original_min_rank_text` |
| 备注 | `source_note` | `remark` |
| 数据血缘 | `source_document_id` + `import_run_id` | 同左 + `import_batch_id` + `source_*` 一整组 |

### 4.4 招生计划

| 概念 | 应用层 `enrollment_plan` | raw `gaokao_admission_plan` |
|---|---|---|
| 粒度 | `(year, province, batch, exam_mode, college_id, major_group_code, major_name_snapshot, student_type)` UNIQUE | `(province, year, candidate_type, batch_name, round_no, college_*, major_*, major_group_code)` |
| 考试模式 | `exam_mode` | 未显式列，走 `pathway_code` + `candidate_type` 推断 |
| 批次 | `batch` | `batch_name` |
| 院校 | `college_id` + `college_code_snapshot` | `college_id` + `college_code_snapshot` + `college_name_snapshot` |
| 专业 | `major_id`（nullable）+ `major_name_snapshot` + `major_code_snapshot` + `major_group_code` | `major_id` + `major_name_snapshot` + `major_code_snapshot` + `major_group_code` |
| 学生类型 | `student_type` 英文枚举 | `candidate_type` 中文 |
| 计划数 | `plan_count` | `plan_count` |
| 选科要求 | `subject_requirement`（文本） | `subject_requirement_text` + `subject_requirement_code` |
| 学费 | `tuition_fee` | `tuition` |
| 学制 | `schooling_years` | `duration_years` |
| 校区 | `training_location` | `campus` |
| 专项标签 | 无 | `special_plan_tag` |
| 专业注释 | 无 | `major_note` |
| 更新类型 | 无 | `update_type` / `merge_status` / `original_update_text` |
| 解析置信度 | 无 | `parse_confidence` |
| 数据血缘 | `source_document_id` + `import_run_id` + `import_batch_name` | 同左 + `import_batch_id` + `source_*` 一整组 |

### 4.5 一分一段

| 概念 | 应用层 | raw `score_rank_segment` |
|---|---|---|
| 落地 | 没有独立应用层表，直接读 raw；后端 `select_score_rank_year` 优先目标年份，否则回退近年 | `province`, `year`, `score_type`, `subject_group`, `score`, `segment_count`, `cumulative_count`, `rank_value` |
| 位次列 | `cumulative_count` 或 `rank_value` 取决于年份 | 二选一，运行时 PRAGMA 探测 |

### 4.6 选科要求

| 概念 | 应用层 `subject_requirement_dict` | raw `gaokao_subject_requirement` + `gaokao_subject_requirement_dict` |
|---|---|---|
| 粒度 | `(province, year, exam_mode, requirement_code)` UNIQUE，仅字典 | 字典 + 明细两张表 |
| 字段 | `requirement_code`, `requirement_text`, `match_mode`, `normalized_subjects_json`, `sort_order` | 见 §3.14、§3.15 |

### 4.7 批次线

| 概念 | 应用层 | raw `gaokao_score_line` |
|---|---|---|
| 落地 | 应用层未建，由前端直接调用后端服务聚合 | `province`, `year`, `candidate_type`, `batch_name`, `line_type`, `score`, `remark` |

### 4.8 批次字典

| 概念 | 应用层 | raw `gaokao_batch_dict` |
|---|---|---|
| 落地 | `dict_item`（类型 `batch`）兜底 | `province_scope`, `batch_code`, `batch_name`, `pathway_code`, `year_from/year_to` |

### 4.9 升学路径

| 概念 | 应用层 `gaokao_pathway` | raw `gaokao_pathway_dict` |
|---|---|---|
| 定位 | 正式业务表，绑定 `gaokao_source_document` 和学生评估 | 只是字典 |
| 字段 | `province`, `pathway_code`, `pathway_name`, `pathway_group`, `student_type`, `exam_type`, `batch_name`, `volunteer_mode`, `max_volunteer_count`, `recommendation_depth`, `status`, `source_document_id`, `summary`, `risk_level`, `notes_json` | `pathway_code`, `pathway_name`, `pathway_category`, `sort_order`, `summary`, `status` |

### 4.10 省级规则

| 概念 | 应用层 `province_volunteer_rule` | raw `gaokao_province_rule` + `gaokao_province_rule_version` |
|---|---|---|
| 粒度 | `(province, year, exam_mode, batch, candidate_type)` UNIQUE | 版本 + 规则两张 |
| 志愿数量上限 | `volunteer_limit` | `max_volunteer_count` |
| 志愿单位 | `volunteer_unit_type` | `volunteer_unit_type` |
| 选科模式 | `subject_requirement_mode` + `required_subjects_json` | `score_composition` + `raw_payload` |

### 4.11 赋分规则

| 概念 | 应用层 `province_score_transform_rule` | raw `gaokao_score_transform_rule` |
|---|---|---|
| 粒度 | `(province, year, exam_mode, subject_name)` UNIQUE | 非 UNIQUE，按原始等级表存多行 |
| 表达方式 | `score_mode` + `grade_table_json` / `formula_json` | `raw_score_min/max`, `transformed_score`, `transformed_score_min/max`, `grade_code`, `grade_name`, `ratio_from/to`, `rule_payload` |

### 4.12 政策参考

| 概念 | 应用层 `gaokao_source_document` | raw `gaokao_policy_reference` |
|---|---|---|
| 定位 | 官方文件登记（含原始 URL、hash、解析器） | 老旧的政策索引 |
| 字段 | `province`, `year`, `source_type`, `title`, `url`, `official_org`, `published_at`, `fetched_at`, `local_file_path`, `file_sha256`, `parser_name`, `parser_version`, `status` | `province`, `year`, `policy_type`, `title`, `url`, `local_path`, `summary`, `source_level`, `version_id`, `published_at`, `status` |

### 4.13 职业方向 / 就业映射

| 概念 | 应用层 `employment_direction` / `major_employment_mapping` | raw `gaokao_career_direction` / `gaokao_major_career_mapping` |
|---|---|---|
| 定位 | 正在使用 | 0 行，留作未来扩展 |

### 4.14 进行中的推荐 / 志愿草稿

| 概念 | 应用层 | raw |
|---|---|---|
| 推荐方案 | `recommendation_scheme`, `recommendation_result` | 无（原 handoff 中的 `recommendation_candidate/explanation/record` 未迁入） |
| 志愿草稿 | `volunteer_draft`, `volunteer_draft_item` | 无 |


## 5. 命名与枚举对照

### 5.1 学生类型 (`student_type` / `candidate_type`)

| 应用层枚举值（英文） | raw 枚举值（中文/英文别名） | 含义 |
|---|---|---|
| `general` | `普通类` / `general` | 普通类 |
| `art` | `艺术类` / `art` | 艺术类 |
| `sports` | `体育类` / `sports` | 体育类 |
| `spring_exam` | `春季高考` / `spring_exam` | 春季高考 |
| `independent_recruitment` | `单独招生` / `independent_recruitment` | 单独招生 |
| `comprehensive_evaluation` | `综合评价招生` / `comprehensive_evaluation` | 综合评价招生 |

数据健康报告里另有以下「检查中」状态码（不要写进业务数据，只用于报表）：
`summer_total`、`province_rule`、`pending_manual_review*`、`confirmed_manual_*`、`partially_filled`。
来源：`apps/backend/app/utils/data_health.py:STUDENT_TYPE_LABELS`。

代码入口：
- 中文 → 英文：`apps/backend/app/utils/data_health.py:RAW_STUDENT_TYPE_ALIASES`
- 英文 → 中文展示：`apps/backend/app/utils/data_health.py:STUDENT_TYPE_LABELS`

### 5.2 省份 (`province`)

| 应用层默认值 | raw 中可能形态 |
|---|---|
| `山东` | `山东` / `山东省` / `sd` / `shandong` |

代码：`apps/backend/app/utils/data_health.py:SHANDONG_ALIASES`。如果给前端提供新的省份字段，必须先经
`_normalize_province`（`apps/backend/app/utils/gaokao_materialize.py`）归一化。

### 5.3 软删除标记

| 层 | 字段 | 真值含义 |
|---|---|---|
| 应用层 | `is_active`（bool） | True = 启用 |
| raw 层 | `is_deleted`（bool） + `status`（VARCHAR） | `is_deleted=False` 且 `status != 'deleted'` 才视为有效 |

参考：`apps/backend/app/utils/gaokao_materialize.py:_upsert_colleges` 的 WHERE 条件。

### 5.4 JSON 列命名规则

- 应用层一律 `_json` 后缀（`school_level_tags_json`, `required_subjects_json`, `notes_json` 等）。
- raw 层 **没有** `_json` 后缀（`alias_names`, `level_tags`, `required_subjects`, `rule_payload`, `raw_payload` 等）。
- 前端要消费 JSON 列时，对应类型一律来自 OpenAPI（不要自己 `JSON.parse` raw 字段）。

### 5.5 时间戳

- 应用层：`created_at` / `updated_at`，default `CURRENT_TIMESTAMP`，存本地 naive 时间。
- raw 层：同名字段但「无 default」，由导入脚本写入；个别 raw 表还多了 `published_at`、`fetched_at`、`source_record_hash`。

### 5.6 「snapshot」字段惯例

raw 层凡是带 `*_snapshot`（`college_name_snapshot`, `major_code_snapshot` 等）的字段都是「导入时刻冻结的字符串」，
不会跟 `gaokao_college` / `gaokao_major` 同步更新。**不要拿 `*_snapshot` 当主键去 JOIN**，请走 `college_id` / `major_id`。


## 6. 动态探测点（代码里的「字段漂移补丁」）

凡是有 `PRAGMA table_info(...)` 或 `snapshot.has_table/pick_column` 的地方，都说明那张表的 schema 不稳定。
以后迁移 raw 表时需要把这些补丁一起下线。

| 位置 | 目标表 | 行为 |
|---|---|---|
| `apps/backend/app/services/_recommendations_score_rank.py:128` | `score_rank_segment` | 运行时判断用 `rank_value` 还是 `cumulative_count` |
| `apps/backend/app/services/_recommendations_score_rank.py:_province_filter/_subject_group_filter/_score_type_filter` | `score_rank_segment` | 判断列是否存在再拼 WHERE |
| `apps/backend/app/services/gaokao.py:860` `_build_shandong_section_from_raw_or_model` | `gaokao_admission_result` → `gaokao_admission_plan` → ORM | 三级 fallback |
| `apps/backend/app/services/gaokao.py:_SchemaSnapshot` | 所有 raw 表 | 启动时快照 `sqlite_master`，供多路判断 |
| `apps/backend/app/utils/gaokao_sync.py:app_db_has_embedded_gaokao_tables` | `gaokao_college` / `gaokao_admission_plan` / `gaokao_subject_requirement_dict` | 决定是否启用 sidecar |
| `apps/backend/app/utils/gaokao_materialize.py:_upsert_colleges` | `gaokao_college` | 用 `_table_columns` 容忍新老 schema |
| `scripts/import_gaokao_scraper_bundle.py:1752/1794` | `gaokao_admission_result` / `gaokao_admission_plan` | 原生 `CREATE TABLE IF NOT EXISTS`，唯一可写入源 |
| `apps/backend/alembic/versions/20260508_0031_gaokao_legacy_fk_safety.py` | `gaokao_college_tag` | 仅在 raw 表存在时才加 FK |

## 7. raw→应用层 物化通道

入口：`scripts/materialize_gaokao_structured_data.py`，底层调 `apps/backend/app/utils/gaokao_materialize.py:22 materialize_gaokao_structured_tables`。

物化顺序与产出：

| 步骤 | raw 源 | 目标 | 影响字段 |
|---|---|---|---|
| 1 | `gaokao_college` | `college` + `college_alias` | 见 §4.1 |
| 2 | `gaokao_major` | `major` | 见 §4.2 |
| 3 | `gaokao_admission_result` | `admission_record` | 见 §4.3 |
| 4 | `gaokao_admission_plan` | `enrollment_plan` | 见 §4.4 |
| 5 | `college` ∩ `major` | `college_major` | 多对多关联 |

**还没物化到应用层的 raw 表（前端暂时拿不到）**：`gaokao_college_chapter_rule`、`gaokao_college_tag`、`gaokao_subject_requirement`、`gaokao_subject_requirement_dict`、`gaokao_score_line`、`gaokao_score_transform_rule`、`gaokao_batch_dict`、`gaokao_pathway_dict`、`gaokao_province_rule*`、`gaokao_policy_reference`、`gaokao_source_registry`、`gaokao_career_direction`、`gaokao_major_career_mapping`、`score_rank_segment`、`data_import_batch`、`data_import_error_log`。

## 8. 空表清单（45 张）

按模块分组，括号内为「当前 113 张总表中的编号意义」仅作提示。动手清理前必须跑一遍 `grep` 看是否还在代码里被引用。

**评价/量化（未启用）**
`evaluation_batch`, `evaluation_response`, `evaluation_summary`,
`adviser_quant_record`, `adviser_quant_record_attachment`

**知识点 & 题库（功能在建）**
`knowledge_point`, `knowledge_point_alias`,
`score_question`, `score_question_record`, `score_question_knowledge_point`, `score_question_import_batch`,
`score_knowledge_snapshot`, `score_target_line`, `score_import_profile`

**学生扩展（按需使用）**
`student_guardian`, `student_attachment`, `student_career_preference`,
`student_class_history`, `student_class_transfer_batch`, `student_class_transfer_item`,
`student_gaokao_score_projection`, `student_growth_attachment`, `student_growth_record`,
`student_pathway_evaluation`, `student_planning_goal`, `student_planning_note`

**班级/教师/工作量**
`class_adviser_assignment`, `class_honor`,
`teacher_title_history`, `teacher_workload_extra`, `teacher_workload_result`,
`period_definition`, `timetable_batch`, `timetable_entry`

**推荐/志愿（功能在建）**
`recommendation_result`, `recommendation_scheme`,
`volunteer_draft`, `volunteer_draft_item`

**系统**
`backup_record`, `report_export_record`, `stored_file`

**raw 层（未启用）**
`data_import_batch`, `data_import_error_log`,
`gaokao_career_direction`, `gaokao_major_career_mapping`

> 原则：空表 **不代表可删**。很多是「功能还没启用」，前端已经写好但走的是空查询。删除前至少确认：
> - `apps/backend/app/models/` 里没有 model 还 import 它
> - `apps/backend/app/api/routes/` 里没有路由还在查它
> - `apps/frontend/src/` 里没有 `/api/` 调用链会读到它

## 9. 第二 SQLite 句柄（gaokao sidecar）的来龙去脉

代码位置：`apps/backend/app/main.py:16 _build_optional_gaokao_db_manager`。

决策流程：

1. 如果 `app.db` 里已经有 raw 表（`gaokao_college` / `gaokao_admission_plan` / `gaokao_subject_requirement_dict` 任一存在），就 **不** 启用 sidecar，全部走 `app.db`。
2. 否则如果 `data/local_edu_tool/local_edu.sqlite3` 存在，就把它作为 sidecar 挂上去，以 `request.app.state.gaokao_db` 暴露。
3. `get_gaokao_db_session` 在 sidecar 不存在时返回 `None`，服务层要自己判 `None`。

对开发的含义：

- 当前仓库 `data/app.db` 里 raw 表齐全，**sidecar 是关闭的**，`get_gaokao_db_session` 全程返回 `None`。
- `apps/backend/app/services/gaokao.py` 里凡是 `if gaokao_session is None` 的分支，会直接落到 `session`（= app.db）上查 raw 表。
- 未来做 B 方案（把 raw 物理迁出 `app.db`）时，这套 sidecar 能直接接起来。

## 10. 常见踩坑 FAQ

**Q1. 前端报「`current_class_name` 是 undefined」。**
`student` ORM 没有这个列，它是服务层用 relationship 补的字段（见 `apps/backend/app/services/students.py`）。检查后端 `StudentRead` 是否包含同名字段，及服务层是否 join 了 `SchoolClass`。

**Q2. 前端做筛选传英文 `candidate_type=art`，后端报「省份无数据」。**
后端在查询 raw 表时会按 `candidate_type` 原文匹配，raw 表里可能是中文「艺术类」。一定要走 `RAW_STUDENT_TYPE_ALIASES` 归一化后再 WHERE。

**Q3. 前端显示的「位次」跟数据库对不上。**
一分一段表 `score_rank_segment` 在不同年份同时出现 `rank_value` 和 `cumulative_count`，看后端 `select_score_rank_year` 选了哪一年。前端不要自己再 JOIN，直接拿 `score_basis`（`target_year_score_rank_segment` 等）区分解释即可。

**Q4. 院校别名下拉不全。**
应用层的 `college_alias` 是由 `materialize_gaokao_structured_tables` 物化来的，如果 raw 里新加了别名但没跑 materialize，应用层看不到。解决：重跑 `scripts/materialize_gaokao_structured_data.py`。

**Q5. 同一院校 `college_id` 在 `admission_record` 和 `enrollment_plan` 里对应不上。**
两边都 FK 到 `college.id`，但 raw 表里一些校名在物化时才会新建占位院校（见 `gaokao_materialize.py` 里的 `占位院校` 注释）。如果前端联查两表，请以 `college_id + year + batch` 为主，不要再叠 `college_name_snapshot`。

**Q6. `gaokao_subject_requirement` 有 18 万行，前端展示慢。**
明细表不要直连前端，用 `apps/backend/app/services/gaokao.py` 里的聚合接口，或者走 `subject_requirement_dict`（27 行）查字典。

**Q7. 新增一张业务表后前端拿不到。**
顺序：
1. `apps/backend/app/models/*.py` 加 model；
2. `apps/backend/alembic/versions/` 写迁移；
3. `apps/backend/app/schemas/*.py` 写 Pydantic；
4. `apps/backend/app/api/routes/*.py` 挂路由；
5. 重新跑 OpenAPI 导出 + `npm run gen:api`（见附录 A），再在前端消费。


---

## 附录 A：前端类型同步流程

前端 `src/types/api.generated.ts` 由后端 OpenAPI 自动生成，以下流程必须在每次后端 schema 变更后手动跑一次。

```bash
# 1. 在 frontend 工作目录执行
cd apps/frontend
# 2. 重新拉取 OpenAPI 并生成 TS 类型
npm run gen:api
# 3. 跑构建确认前端契约（gaokaoDataTypes.ts 等）仍然兼容
npm run build
```

`npm run gen:api` 内部依次做了两件事：

1. `../../.venv/bin/python ../../scripts/dump_openapi.py --output ./openapi.json`
   — 直接 `import` 后端 `app.main.create_app()` 拿到 OpenAPI schema，落到 `apps/frontend/openapi.json`。**不用** 起 HTTP 服务。
2. `openapi-typescript ./openapi.json -o ./src/types/api.generated.ts`
   — 生成 21k 行的 `components["schemas"]` 类型表。

「前端契约」类型（`apps/frontend/src/components/gaokao-data/gaokaoDataTypes.ts` 等）会在文件末尾通过条件类型 `IsAssignable` 验证：手写类型必须是 OpenAPI 生成类型的子集。如果后端 schema 收紧了某字段，跑完 `gen:api` 后 `npm run build` 会在该处报错。改完手写类型再继续，不要让错误扩散到 Vue 组件。


---

## 附录 B：写新页面 / 新接口的标准流程

> 给后续协作者（人或 AI）的 checklist。任何一处略掉，都很可能让前端再次「字段对不上」。

### B.1 加新字段 / 改字段名

1. 改 ORM：`apps/backend/app/models/<domain>.py`。
2. 写 alembic：`apps/backend/alembic/versions/`，加迁移文件。
3. 改 Pydantic schema：`apps/backend/app/schemas/<domain>.py`。
4. 改业务路由（如果新增字段需要查询参数 / 返回字段）：`apps/backend/app/api/routes/<domain>.py`。
5. 在 `apps/frontend` 跑：`npm run gen:api`。这会重新拉 OpenAPI 并生成 TS 类型。
6. 跑 `npm run build`。如果手写契约（`gaokaoDataTypes.ts` / `recommendations/types.ts` / `recommendations/detailTypes.ts`）跟不上后端，会在文件末尾的 `IsAssignable` 断言处直接标红——把那一处对齐就能继续。
7. 业务页面消费新字段。

### B.2 加新接口

1. 新建路由（必要时新建 `app/api/routes/<x>.py` 并在 `app/api/router.py` 挂上）。
2. 写 Pydantic schema，**所有响应类型都用 `XXXRead` 命名约定**，方便后续找。
3. 跑 `cd apps/frontend && npm run gen:api`。
4. 在前端用：

   ```ts
   import { api } from "../api/typedClient";

   // GET 无参
   const data = await api.get("/api/gaokao/data-overview");

   // GET 带 query
   const list = await api.get("/api/students", { query: { page: 1, page_size: 50 } });

   // POST JSON body
   const created = await api.post("/api/students", { body: payload });

   // PUT 路径参数
   await api.put("/api/students/{student_id}", {
     path: { student_id: 42 },
     body: payload,
   });
   ```

5. **不要**继续写 `apiRequest<MyType>("/api/...")`：那种调用没有自动校验路径、query、body 类型，是出错的主要来源。`api.get/post/put/delete` 会按 OpenAPI 推断。

### B.3 加新前端页面

1. 拷一份现有页面骨架（推荐 `pages/GaokaoDataPage.vue` 的 fetch 部分作为样板）。
2. 所有 fetch 都用 `api.*`（见 B.2）。如果接口在后端还没 schema，先把后端补完整再来。
3. 不要写新的「手写后端类型 interface」。需要复用响应类型时，按下例：

   ```ts
   import type { components } from "../types/api.generated";

   type StudentRead = components["schemas"]["StudentRead"];
   ```

4. 跑 `npm run build` 确保编译通过。

### B.4 何时需要在 `gaokaoDataTypes.ts` / `recommendations/types.ts` 那种「手写契约」里加 `IsAssignable`？

- 后端类型已经存在，但前端业务希望**收紧**某些字段（比如 `notes` 后端可选、前端约定永远是数组）。
- 这时把手写 interface 留在前端，再加一行 `IsAssignable<前端契约, 后端 OpenAPI 类型>`，让兼容性差一旦出现就在编译期暴露。

### B.5 不要做的事

- 不要直接读 `data/app.db` 里的 raw 表（前缀 `gaokao_*` 的非 ORM 表），见本文 §3 / §6 / §7。raw 表的字段、类型都没保证。
- 不要在前端写 `JSON.parse` 后端字段。后端已经返回结构化对象。
- 不要为了"避免重复"在前端再封装一层 axios 拦截器。`api.*` 就是统一入口。

---

## 附录 C：B 计划后的结构变化（2026-05-13）

### C.1 raw 表迁出 app.db

22 张 raw 表已通过 `scripts/migrate_raw_tables_to_sidecar.py` 一次性搬到 sidecar
`data/local_edu_tool/local_edu.sqlite3`。结果：

- `data/app.db`：113 张表 → 92 张。文件体积 850 MB → 215 MB。
- `data/local_edu_tool/local_edu.sqlite3`：21 张 raw 表 + `alembic_version`（合计 22）。
- `data/local_edu_tool/local_edu.sqlite3` 以前是指向 handoffs 快照的 symlink，现在已替换为独立真实文件。
- 旧 handoff 快照仍保留在 `handoffs/2026-04-21_mac_db_handoff/database/` 作为历史存档。

### C.2 运行时 ATTACH

`apps/backend/app/db/session.py:DatabaseManager` 新增 `attach_databases` 参数；
`apps/backend/app/main.py:_build_attach_databases` 会自动把 sidecar 以 `gaokao` 别名挂上。
所有业务代码里的 SQL（`FROM gaokao_admission_result` 等）继续透明工作，无需加 schema 限定。

### C.3 运行时探测下线

- `apps/backend/app/services/_recommendations_score_rank.py` 原本每次查询前会 `PRAGMA
  table_info(score_rank_segment)` 探测字段，现改为固定 schema；
  如果 sidecar 未 ATTACH/表不存在，通过 `OperationalError` 优雅降级返回 None。
- `app_db_has_embedded_gaokao_tables` 保留为 no-op（始终返回 False）仅为了不破坏旧 import。
- `get_gaokao_db_session` 保留为 no-op（返回 None），服务层的 `_pick_raw_session` 会继续走主 session。

### C.4 导入脚本状态

- `scripts/import_gaokao_scraper_bundle.py`：已添加 `--sidecar-path` 参数（默认使用 data/local_edu_tool/local_edu.sqlite3），
  在运行时 ATTACH sidecar，`_ensure_raw_tables` 不再无条件在 app.db 建 raw 表。
- `scripts/merge_handoff_gaokao_db.py`：已废弃，仅打印迁移结束的提示。
- `scripts/round5_*` / `round6_*` / `bootstrap_shandong_stage1_public_data.py` 等一次性导入脚本：
  本身 **未** 调整。如果未来重新运行它们，需要手动 ATTACH sidecar（或在脚本里加 ATTACH 语句）。

### C.5 空表的处置结论（D 计划）

45 张空表在本轮评审后的结论：

- 业务未启用但**保留**的表（ORM / 路由 / 前端页面都还在占位，删除会引发级联故障）：
  评价批次、工作量结果、知识点、错题、推荐方案、志愿草稿、学生成长档案、学生规划、教师职称历史、定时课表 等。
  这些表先不动，以后启动相应功能时再填数据即可。
- sidecar 里 0 行、仅 import 脚本用到的表（`gaokao_career_direction`、`gaokao_major_career_mapping`、
  `data_import_batch`、`data_import_error_log`）：**保留**。不占空间、对后续导入链路有用。

如果后续需要进一步瘦身，可以在清空 orm/路由/前端引用后，分模块一次性删除整条「表 + 模型 + 路由 + 页面」。
单纯 `DROP TABLE` 没有意义，只会让代码运行时报错。

