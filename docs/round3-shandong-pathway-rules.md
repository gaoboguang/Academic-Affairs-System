# 第三轮 D2 山东升学路径规则字典

- 日期：2026-04-25
- 范围：窗口 D2，山东 2026 升学路径官方规则字典与 bootstrap
- 代码入口：`apps/backend/app/services/gaokao_pathways.py`
- API 入口：`POST /api/gaokao/pathways/bootstrap-shandong`
- 本地命令：`npm run backend:bootstrap-pathways -- --target-year 2026`

## 目标

D2 在 D1 的四张表和三态规则引擎基础上，把山东升学路径规则从“基础路径 + 最小边界规则”扩展为“官方来源文档 + 可追溯规则字典”。

本轮只做路径规则、资格提醒、材料缺口和人工复核清单，不做新的复杂推荐算法，不把单招、综评、春考、艺体、体育、提前批或特殊类型包装成录取概率。

## 当前覆盖路径

| 路径编码 | 路径名称 | 当前深度 | D2 规则重点 |
| --- | --- | --- | --- |
| `summer_general_regular` | 普通类常规批 | 可做位次型推荐 | 高考报名、选科组合、2026 正式计划待发布、高校章程复核 |
| `summer_general_early_a` | 普通类提前批A类 | 资格初筛 | 普通类身份、体检/面试/体测接受度、飞行技术等方向专项核验 |
| `summer_general_early_b` | 普通类提前批B类 | 资格初筛 | 普通类身份、定向就业/服务约束、签约和章程复核 |
| `summer_special_type` | 普通类特殊类型批 | 资格初筛 | 特殊类型控制线、资格名单、前置报名和高校测试材料 |
| `spring_exam_undergrad` | 春季高考本科批 | 资格初筛 | 春季高考身份、专业类别一致 |
| `spring_exam_junior` | 春季高考专科批 | 资格初筛 | 春季高考身份、专业类别一致 |
| `vocational_single_exam` | 高职单独招生 | 资格初筛 | 高考报名、中职/社会人员范围、学历或同等学力、院校章程和测试方式 |
| `vocational_comprehensive` | 高职综合评价招生 | 资格初筛 | 普通高中应届、综合素质评价、素质测试或面试 |
| `art_undergrad` | 艺术类本科批 | 资格初筛 | 艺术类别、统考/校考成绩、文化线和章程要求 |
| `art_junior` | 艺术类专科批 | 资格初筛 | 艺术类别、录取原则和章程要求 |
| `sports_regular` | 体育类常规批 | 资格初筛 | 体育类身份、体育专业测试成绩、与体育单招/高水平运动队区分 |
| `sports_single_exam` | 体育单招 | 政策提醒 | 运动员等级、专项报名系统、文化考试和专项考试 |
| `high_level_sports` | 高水平运动队 | 政策提醒 | 高考报名、运动员等级、高校简章和资格审核 |

## 官方来源

bootstrap 会先登记或更新 `gaokao_source_document`，再把 `source_document_id` 写入 `gaokao_pathway` 和 `gaokao_pathway_rule`。本地命令默认会在写入前备份 `data/app.db`，备份放在 `data/backups/`。

本轮来源包括：

- 山东省教育招生考试院：2026 高考报名通知、2025 录取工作意见参考、2026 选科要求、春季高考专业类别考试标准、艺术类实施方案、体育类招生通知、体育单招和高水平运动队山东通知。
- 山东省教育厅：2026 高职单招和综合评价招生通知。
- 教育部办公厅：2026 部分特殊类型招生通知。
- 国家体育总局科教司：2026 运动训练、武术与民族传统体育专业招生管理办法。

注意：普通类常规批、提前批 A/B 的 2026 正式录取意见和正式招生计划在本轮仍按“待官方发布 / 需人工复核”处理；D2 只用 2025 录取工作意见作为结构参考，不把它写成 2026 已发布规则。

## 规则表达

D2 新增规则统一使用 `GaokaoPathwayRule`，不在前端页面硬编码政策。

规则继续走 D1 的三态评估：

- `passed`：画像或材料已满足当前规则。
- `failed`：硬性门槛不满足。
- `unknown`：缺画像、缺材料、待官方发布或必须人工复核。

常见规则类型：

- `hard_gate`：报名、考生类型、是否接受定向服务、是否接受体检面试等硬条件。
- `subject_required`：选科组合或专业选科要求。
- `category_match`：春季高考专业类别一致性。
- `material_required`：综合素质评价、资格名单、艺术/体育成绩、运动员等级等材料。
- `chapter_check` / `manual_check`：高校章程、测试方式、签约约束和特殊说明。
- `time_window`：报名、缴费、考试、测试等时间窗口。

## 后续窗口注意事项

- D3 做学生升学画像时，应优先补齐 D2 规则读取的字段和材料键，如 `has_gaokao_registration`、`subject_combination`、`spring_exam_category`、`comprehensive_quality_evaluation`、`art_exam_score`、`sports_test_score`、`athlete_level_certificate`。
- D4 做前端路径中心时，不要展示内部规则编码；应展示路径状态、缺什么材料、为什么需要人工核验、下一步动作。
- D5 做普通类推荐加固时，继续保留“2026 正式计划待发布 / 导入后复核”的提示，不要伪造计划。
- D6/D7 如继续细化单招、综评、春考、艺体、体育、提前批和专项，应继续复用 `gaokao_pathway_rule`，不要把政策判断散落到页面。

## 验证

本轮新增 / 更新的定向验证：

```bash
npm run backend:test -- apps/backend/tests/test_gaokao_pathways.py -q
npm run backend:bootstrap-pathways -- --target-year 2026 --json
```

当前结果：D2 定向后端测试 `3 passed`；真实主库 bootstrap 会输出本次创建 / 跳过的路径与规则数量。
