# 山东普通类冲稳保推荐引擎说明（窗口 B4）

## 当前结论

窗口 B4 已新增山东普通类冲稳保推荐预览接口，用 2023-2025 年山东普通类历史投档记录、目标年份招生计划、选科要求和学生预估位次，输出“冲 / 稳 / 保 / 仅关注”四类候选。

当前实现只做预览推荐，不新增持久化推荐结果表，不写入 `data/app.db`。后续窗口 C1 可以直接调用接口做页面，C2 可把结果接入打印 / Excel / 报表链。

## 接口入口

- 方法：`POST`
- 路径：`/api/recommendations/shandong-rush-stable-safe/preview`
- 代码入口：`apps/backend/app/services/_recommendations_shandong_rush_stable_safe.py`
- Schema：`apps/backend/app/schemas/recommendation.py`
- 路由：`apps/backend/app/api/routes/recommendations.py`

## 输入方式

接口支持三类学生位次来源：

1. `projection`
   - 读取 B3 的 `student_gaokao_score_projection` 快照。
   - 使用 `predicted_rank`，缺失时使用 `rank_range_low / rank_range_high` 的均值。
   - 如果真实库还没有迁移到 `20260425_0017`，会返回清晰错误，提示先运行后端迁移。
2. `manual_rank`
   - 直接使用手动填写的山东全省位次。
3. `manual_score`
   - 按 `score_rank_segment` 一分一段把分数换成位次。
   - 目标年份一分一段缺失时，使用不晚于目标年份的最近年份，并标记 `previous_year_score_rank_segment`。

## 核心分层口径

- 历史数据年份：2025、2024、2023。
- 权重：2025 为 `0.50`，2024 为 `0.30`，2023 为 `0.20`。
- 分组粒度：学校 + 专业。
- 位次边际：`rank_margin = historical_reference_rank - predicted_rank`。
- 正值表示学生预估位次优于历史参考位次，负值表示弱于历史参考位次。

风险偏好阈值：

| 风险偏好 | 冲刺下限 | 稳妥下限 | 保底下限 |
| --- | ---: | ---: | ---: |
| `conservative` | -6% | 6% | 22% |
| `balanced` | -12% | 3% | 18% |
| `aggressive` | -16% | 0% | 15% |

重要降级规则：

- 近三年只有 1 年历史样本时，不进入冲 / 稳 / 保，归为“仅关注”。
- 近三年样本不足 3 年时，标记 `three_year_data_incomplete`。
- 缺少目标年份招生计划时，标记 `plan_missing`，不把结果包装成低风险。
- 计划数明显减少时，标记 `plan_decreased`，并阻止进入“保”。
- 用户提供选科组合且不满足选科要求时，候选会被排除，不进入任何分层。

## 输出字段

每条候选包含开发文档要求的关键解释字段：

- `bucket` / `bucket_label`
- `rank_margin`
- `rank_margin_ratio`
- `score_summary`
- `years_used`
- `historical_summary`
- `risk_flags`
- `explanation_text`
- `source_document_ids`

响应摘要会额外返回：

- `rush_count`
- `stable_count`
- `safe_count`
- `watch_count`
- `excluded_subject_mismatch_count`

## 风险码说明

- `rank_projection_from_previous_year`：分数换位次时使用了上一年一分一段。
- `rank_projection_from_school_exam`：位次来自校内考试估算，不能直接等同于山东全省位次。
- `three_year_data_incomplete`：近三年历史样本不完整。
- `historical_data_missing`：只有单年历史样本，只能仅关注。
- `plan_missing`：缺少目标年份招生计划。
- `plan_decreased`：招生计划存在缩招迹象。
- `subject_requirement_check`：有选科要求但本次没有提供学生选科组合，需要人工核对。

## 当前边界

- 当前只支持山东普通类夏季高考。
- 当前只使用 2023-2025 历史投档数据作为普通类推荐依据，不伪造 2026 普通类招生计划或投档结果。
- 特殊类型仍只能做初筛和人工核对，不进入本 B4 普通类冲稳保引擎。
- 真实 `data/app.db` 如未执行 B3 迁移，`projection` 模式不可用；`manual_rank` 和 `manual_score` 仍可用于预览。

## 验证记录

- `npm run backend:test -- apps/backend/tests/test_shandong_rush_stable_safe_recommendation.py -q`：`3 passed`
- `npm run backend:test -- apps/backend/tests/test_recommendation_workflow.py apps/backend/tests/test_gaokao_score_projection.py apps/backend/tests/test_shandong_rush_stable_safe_recommendation.py -q`：`20 passed`
- `npm run backend:data-health -- --json`：可运行，当前仍为 `warning`，P0 数据缺口仍为 6 条
- `git diff --check`：通过
