# 推荐中心 Stage B 解释链审计

- 日期：2026-04-24
- 执行窗口：窗口 4
- 范围：`/recommendations` 高考志愿工作台、推荐结果、志愿草稿、打印页、报表中心导出前摘要、Excel 导出
- 当前业务范围：山东优先，普通类先可用，特殊类型保持安全初筛和人工复核提示

## 1. 当前链路结论

Stage B 当前已经不是早期推荐 Demo，而是由招生计划、录取参考、省份规则、分数输入、职业意向、章程限制和输出材料共同组成的解释链。

当前可继续沿用的事实：

- 候选池入口在 `apps/backend/app/services/_recommendations_workbench.py`，正式推荐入口在 `apps/backend/app/services/_recommendations_generation.py`。
- 冲 / 稳 / 保分层由 `apps/backend/app/services/_recommendations_result_builder.py` 调用 `classify_ratio()` / `classify_score_gap()` 完成。
- 省份规则来自 `province_volunteer_rule`，规则列表、创建、更新和 bootstrap 在 `apps/backend/app/services/_recommendations_rules.py`。
- 职业方向来自 `employment_direction` 与 `major_employment_mapping`，匹配解释由 `evaluate_career_alignment()` 生成。
- 草稿详情会重新加载当前可用规则，避免保存时的旧规则快照被误当成唯一事实。
- 打印页和报表中心摘要已复用前端 helper；Excel 导出由 `apps/backend/app/exporters/recommendations.py` 独立生成同口径说明。

## 2. 候选池如何生成

工作台预览大致流程：

1. 读取学生、考试、目标年份、考生类别和分数输入模式。
2. 根据省份、年份、考试模式、批次和考生类别加载省份规则。
3. 按 `enrollment_plan` 筛出招生计划，筛选条件包括省份、年份、考生类型、批次、考试模式、目标地区、院校层级、专业关键词和选科组合。
4. 按同省、同类别读取 `admission_record` 作为录取参考。
5. 如果 `spring_exam / independent_recruitment / comprehensive_evaluation` 缺少专门录取结果，允许回退普通类录取参考，并打 `general_reference_fallback`。
6. 如果 `art / sports` 缺少专门录取结果，优先走 `gaokao_score_line` 省控线资格初筛，并打 `score_line_reference_only`。
7. 如果春考 / 综评 / 单招既无专门录取结果，也无可用控制线，则走当年招生计划清单方向性初筛，并打 `plan_only_reference`。
8. 补充职业匹配、章程限制、省份政策、批次词典、命中规则和参考年份信息。

## 3. 冲稳保如何分组

普通录取参考链路：

- 有位次时，按学生位次与参考位次比值分层。
- 只有分数时，按最近最低分差额分层。
- 缺少专业线时可回退院校线，并打 `major_baseline_missing`。
- 样本不足或缺少位次时，分别打 `sample_insufficient` / `rank_missing`。

特殊类型 fallback 链路：

- 省控线和计划清单 fallback 的 `fallback_priority_score / label / notes` 只表示“优先核看顺序”，不表示录取概率。
- 艺体、春考、综评、单招的细分类别来自 `special_type_rule`，用于生成核对清单和初筛优先级。

## 4. 省份规则如何命中

规则命中字段已经下沉到候选：

- `matched_rule_exam_mode`
- `matched_rule_batch`
- `matched_rule_candidate_type`
- `matched_rule_is_baseline`

前端显示位置：

- 工作台候选池“依据”列。
- 工作台“边界概览”。
- 草稿打印页“边界概览”。
- 报表中心 `volunteer_draft_summary` 导出前摘要。
- Excel `volunteer_draft_summary` 的“规则差异摘要”“边界概览”“志愿草稿”明细列。

当前表达：

- 缺省份规则：`missing_rule_province`
- 缺目标年份规则：`missing_rule_year`
- 缺批次规则：`missing_rule_batch`
- 缺类别专用规则：`missing_rule_candidate_type`
- 缺目标模式规则：`missing_rule_exam_mode`
- 回退通用类别规则：`fallback_general_candidate_rule`
- 兼容考试模式：`compatible_exam_mode_fallback`
- 系统基线命中：`baseline_rule_matched`

## 5. 缺少年份规则如何表达

后端在 `_load_applicable_rules()` 内生成 `rule_alerts`，工作台预览直接返回。

输出链路现状：

| 输出位置 | 是否表达 | 说明 |
| --- | --- | --- |
| 工作台预览 | 是 | 边界概览按候选数量汇总 |
| 候选单条说明 | 是 | 依据列展示命中规则或缺口说明 |
| 志愿草稿详情 | 是 | 草稿详情重新加载当前规则 |
| 草稿打印页 | 是 | 复用 `buildVolunteerDraftBoundaryInsightCards()` |
| 报表中心导出前摘要 | 是 | 复用同一草稿摘要 helper |
| Excel 志愿草稿 | 是 | “边界概览”和明细“边界说明”均保留 |

## 6. 样本年份偏旧如何表达

判断口径：目标年份与最近参考样本年份相差 2 年及以上。

当前字段和位置：

- 工作台候选：`reference_years_json`
- 正式推荐结果：`snapshot_json.reference_years`
- 工作台 / 草稿边界：`stale_reference_years`
- 推荐报告边界：`stale_reference_years`
- 单条说明：显示“参考年份偏旧 / 排序和解释偏保守”
- Excel：推荐报告“风险概览”、志愿草稿“边界概览”和明细“边界说明”

## 7. 特殊类型 fallback 如何表达

当前必须分开理解：

| 类型 | 当前 fallback | 风险字段 | 产品表达 |
| --- | --- | --- | --- |
| `spring_exam` | 缺专门录取结果时可回退普通类录取参考；无结果时可计划清单初筛 | `general_reference_fallback` / `plan_only_reference` | 方向性筛选，需核对春考类别和公告 |
| `art` | 省控线资格初筛 | `score_line_reference_only` / `cross_year_score_line_reference` | 资格参考，不是院校录取把握 |
| `sports` | 省控线资格初筛 | `score_line_reference_only` / `cross_year_score_line_reference` | 资格参考，不是院校录取把握 |
| `independent_recruitment` | 普通类录取参考或计划清单初筛 | `general_reference_fallback` / `plan_only_reference` | 需核对报名、校测、职业适应性测试 |
| `comprehensive_evaluation` | 普通类录取参考或计划清单初筛 | `general_reference_fallback` / `plan_only_reference` | 需核对综评报名、校测和章程限制 |

本窗口修复点：

- 工作台边界概览新增普通类录取参考回退汇总。
- 志愿草稿边界概览新增普通类录取参考回退、省控线初筛、计划清单初筛汇总。
- 候选单条说明、推荐结果页和推荐打印页补齐普通类录取参考回退说明。
- Excel 志愿草稿明细的“边界说明”补齐普通类录取参考回退说明。
- 报表中心志愿草稿摘要把上述特殊类型 fallback 归入“边界概览”，不再只落到零散风险提示。

## 8. 职业意向解释闭环

当前职业闭环已经具备：

1. 学生职业偏好支持首选、次选、替代方向，以及行业、岗位、城市、读研、考公/考编、资格证、长培养周期偏好。
2. 专业与职业方向映射支持 `core / high / medium / transferable` 强度。
3. 工作台候选和正式推荐结果返回 `career_match_score / strength / summary / reasons`。
4. 草稿、推荐结果、打印页、Excel 明细保留职业匹配、目标方向、路径提示和职业说明。

当前边界：

- 职业匹配只做增强排序和解释，不替代录取规则。
- 若专业映射缺失，会打 `career_mapping_pending` 或显示“待维护”。
- 若学生不接受读研、资格证、长培养周期或考公考编路径，结果会打对应 mismatch 风险。

## 9. 页面、打印、导出、Excel 一致性

| 风险 / 边界 | 工作台 | 草稿打印 | 推荐结果 | 推荐打印 | 报表摘要 | Excel |
| --- | --- | --- | --- | --- | --- | --- |
| 缺少省份 / 年份 / 批次 / 模式规则 | 是 | 是 | 不适用 | 不适用 | 是 | 是 |
| 回退通用类别规则 | 是 | 是 | 不适用 | 不适用 | 是 | 是 |
| 普通类录取参考回退 | 已补齐 | 已补齐 | 已补齐 | 已补齐 | 已补齐 | 已补齐 |
| 省控线资格初筛 | 是 | 已补齐 | 是 | 是 | 已补齐 | 是 |
| 计划清单初筛 | 是 | 已补齐 | 是 | 是 | 已补齐 | 是 |
| 院校线回退 | 是 | 是 | 是 | 是 | 是 | 是 |
| 参考年份偏旧 | 是 | 是 | 是 | 是 | 是 | 是 |
| 跨省 / 跨年份口径差异 | 是 | 是 | 历史对照中表达 | 是 | 是 | 是 |
| 职业路径不完全匹配 | 单条表达 | 明细表达 | 是 | 是 | 是 | 是 |

## 10. 仍需后续处理

- 山东真实数据仍缺特殊类型专门录取结果，不能把 fallback 结果当作精准录取预测。
- `score_rank_segment` 和 `gaokao_score_line` 仍缺 2020-2023 覆盖，跨年份分数/位次解释仍需继续补数据。
- `gaokao_policy_reference` 数量偏少，政策摘要还需要继续补官方来源。
- 章程限制链待人工复核仍多，正式填报前必须保留章程核对提示。
- 职业映射已有基线，但高频专业仍需逐批清洗，避免职业说明过泛。
