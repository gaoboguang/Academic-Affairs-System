# 第三轮 D5 山东普通类推荐算法加固

- 日期：2026-04-25
- 范围：窗口 D5，山东普通类冲稳保推荐小步加固
- 后端入口：`/api/recommendations/shandong-rush-stable-safe/preview`
- 前端入口：`/recommendations` 的“山东普通类推荐”页签

## 目标

D5 不扩展新升学路径，不重构推荐中心，只加固第二轮已落地的山东普通类冲稳保主链。重点是让分数换位次、选科要求、2026 正式计划缺失提示和校内考试估算风险在页面、打印、Excel 和测试里保持一致。

本轮继续保持边界：

- 不伪造 2026 普通类正式招生计划、一分一段、省控线或投档结果。
- 不把校内考试年级名次直接当作山东全省位次。
- 不把单招、综评、春考、艺体、体育、提前批或特殊类型纳入普通类冲稳保概率判断。

## 本轮完成

- 新增 `apps/backend/app/services/_recommendations_score_rank.py`，把一分一段换位次逻辑收成共享 helper。
- `apps/backend/app/services/_recommendations_score_projection.py` 和 `apps/backend/app/services/_recommendations_shandong_rush_stable_safe.py` 已共用同一套换位次逻辑。
- 共享换算会统一处理：
  - 山东 / sd / 山东省 / shandong 等省份写法；
  - `score_type` 只取普通类总分口径；
  - `subject_group` 只取全体 / 通用口径；
  - 目标年缺失时回退到不晚于目标年的最近一年一分一段。
- 山东普通类推荐页在 2026 目标年下直接显示提示：当前主要参考 2023-2025 历史投档数据，正式填报前需导入 2026 官方计划。
- 打印页和 Excel 导出的 2026 数据提示同步为同一口径。
- Excel 风险概览已更稳定识别校内考试估算，`exam_projection` / `school_exam_projection` 都会进入“校内考试估算”风险说明。
- 后端测试新增：
  - 学生预估和普通类推荐共用一分一段过滤口径；
  - “不限 / 不提科目要求 / 物理 / 物理 化学 / 物理或化学 / 物理和化学均须选考”等常见选科表达。
- 前端测试锁定 2026 官方计划缺失提示文案，避免页面、打印、导出文案漂移。

## 后续窗口注意事项

- D6/D7 继续做单招、综评、春考、艺体、体育、提前批和专项路径时，不要复用普通类冲稳保算法输出录取概率。
- 2026 普通类正式计划发布后，应走官方来源导入链补数据，再重新评估 `plan_missing` 风险和分层结果。
- 如后续要做 96 志愿模拟，建议先复用本轮共享换位次 helper 和当前候选解释字段，不要再新增一套分数换位次查询。

## 验证

推荐验证：

```bash
npm run backend:test -- apps/backend/tests/test_shandong_rush_stable_safe_recommendation.py apps/backend/tests/test_gaokao_score_projection.py -q
npm run frontend:test -- tests/shandong-recommendation-workbench.test.ts
npm run frontend:build
git diff --check
```
