# 报表、打印、Excel 导出一致性审计（2026-04-24）

- 执行窗口：窗口 6
- 审计范围：报表中心、打印预览页、Excel 导出、导出前摘要和推荐 / 志愿风险表达
- 本轮原则：不重写报表系统，只修复页面、打印、Excel 之间已经出现的字段和文案不一致

## 1. 总体结论

当前报表中心已经覆盖 10 类输出，统一入口是 `POST /api/reports/export`，导出记录入口是 `GET /api/reports/exports`，下载入口是 `GET /api/reports/exports/{id}/download`。

本轮检查后确认：

- 10 类报表都有 Excel 导出。
- 10 类报表都有打印预览入口。
- 10 类报表都有导出前摘要或摘要概览，其中推荐报告和志愿草稿继续按“历史对照摘要 / 规则差异摘要 / 边界概览 / 风险概览”分组展示。
- 推荐报告和志愿草稿的关键风险必须保持中文表达，不能在 Excel 明细里继续裸露 `sample_insufficient`、`missing_rule_year`、`subject_requirement_check` 这类内部代码。
- 志愿工作台、推荐结果页、打印页和 Excel 现在复用同一套推荐风险标签，不再各自维护容易漂移的内部码映射。

## 2. 输出链路矩阵

| 报表类型 | 报表中心入口 | 后端数据 / 导出入口 | 打印页 | Excel sheet | 导出前摘要 | 风险 / 摘要一致性 | 字段顺序 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 学生成绩分析单 | `student_analysis` | `/api/analytics/students/{student_id}` -> `export_student_analysis_report` | `/print/student-analysis/{studentId}/{examId}` | 学生分析、学科明细、摘要概览 | 有 | 摘要概览与打印页复用同类卡片；本轮修正 Excel 名次字段 | 已对齐 |
| 班级成绩分析报表 | `class_analysis` | `/api/analytics/classes/{class_id}` -> `export_class_analysis_report` | `/print/class-analysis/{classId}/{examId}` | 班级分析、学科统计、摘要概览 | 有 | 班级规模、年级对比、优势 / 攻坚学科一致 | 已对齐 |
| 年级成绩汇总表 | `grade_summary` | `/api/analytics/grades/{grade_id}` -> `export_grade_summary_report` | `/print/grade-summary/{gradeId}/{examId}` | 年级概况、班级汇总、学科汇总、摘要概览 | 有 | 年级概况、领先班级、风险班级、攻坚学科一致 | 已对齐 |
| 教师任教分析报表 | `teacher_analysis` | `/api/analytics/teachers/{teacher_id}` -> `export_teacher_analysis_report` | `/print/teacher-analysis/{teacherId}/{examId}` | 教师分析、任教明细、摘要概览 | 有 | 任教整体、最佳拆分、需跟进拆分一致 | 已对齐 |
| 教师课时与工作量报表 | `teacher_workload` | `/api/workload/results` -> `export_workload_results` | `/print/workload/{semesterId}` | 教师工作量、摘要概览 | 有 | 工作量总览、最高工作量、周课时提示一致 | 已对齐 |
| 学生成长档案摘要 | `growth_summary` | `/api/archives/students/{student_id}/records` -> `export_growth_summary` | `/print/growth-summary/{studentId}` | 学生概况、成长记录、摘要概览 | 有 | 成长类型、最近记录、空档案提示一致；本轮修正 Excel 类型字段 | 已对齐 |
| 学生推荐报告 | `recommendation_summary` | `/api/recommendations/schemes/{scheme_id}/results` -> `export_recommendation_summary` | `/print/recommendations/{studentId}/{schemeId}` | 推荐概况、风险概览、导出前摘要、推荐结果 | 有 | 历史对照、样本不足、位次缺失、普通类回退、省控线 / 计划初筛、章程、年份偏旧一致；本轮修正 Excel 明细风险码 | 已对齐 |
| 学生志愿草稿 | `volunteer_draft_summary` | `/api/recommendations/volunteer-drafts/{draft_id}` -> `export_volunteer_draft_summary` | `/print/volunteer-drafts/{draftId}` | 志愿草稿概况、边界概览、规则差异摘要、导出前摘要、志愿草稿 | 有 | 规则缺失、通用规则回退、类别专用规则、跨省 / 跨年份、选科待核对一致；本轮修正 Excel 明细风险码 | 已对齐 |
| 评教汇总报表 | `evaluation_summary` | `/api/evaluation/batches/{batch_id}/overview` -> `export_evaluation_summary_report` | `/print/evaluation-summary/{batchId}` | 评教汇总、教师总览、维度明细、摘要概览 | 有 | 评教整体、领先教师、需复核教师、高频维度一致 | 已对齐 |
| 班主任量化报表 | `adviser_quant_summary` | `/api/adviser-quant/summary` -> `export_adviser_quant_summary_report` | `/print/adviser-quant/{semesterId}` | 量化汇总、教师汇总、量化明细、摘要概览 | 有 | 量化整体、总分最高、扣分较多、高频类别一致；本轮修正 Excel 明细类型字段 | 已对齐 |

## 3. 本轮修复

1. 推荐报告和志愿草稿 Excel 明细中的“风险提示”改为中文：
   - `sample_insufficient` -> `样本不足`
   - `rank_missing` -> `缺少位次，分数参考`
   - `general_reference_fallback` -> `缺少专门录取结果，按普通类参考`
   - `subject_requirement_check` -> `需复核选科要求`
   - `simulation_mode` -> `模拟测算`

2. 学生成绩分析单 Excel 字段改为老师能直接理解的表头：
   - `班名` -> `班级名次`
   - `年名` -> `年级名次`

3. 成长档案 Excel 明细的“类型”改为中文：
   - `reward` -> `奖励记录`
   - `activity` -> `活动记录`
   - 其他成长类型同打印页口径。

4. 班主任量化 Excel 明细的“类型”改为中文：
   - `bonus` -> `特殊加分项`
   - `penalty` -> `扣分项`

5. 报表中心“导出记录”的参数展示改为中文字段名：
   - `report_type=student_analysis / exam_id=12` 改为 `报表类型=学生成绩分析单 / 考试=12`。

6. 志愿工作台风险提示改为复用 `recommendationCopy.ts`：
   - 和推荐结果页、推荐打印页、志愿草稿打印页、Excel 导出保持同一套中文标签。
   - 避免后续新增 `simulation_mode` 等风险标记时，工作台仍显示内部英文码。

## 4. 后续增强

- 当前导出文件名仍以报表类型 + 时间戳为主，例如 `student_analysis_report_*.xlsx`。如要把学生、考试、草稿名写进文件名，需要先统一文件名安全规则，避免中文特殊字符和同名冲突。
- 报表中心导出记录目前能把字段名改成中文，但历史记录里仍只保存 ID；如果后续要显示“张三 / 高三一模”这类对象名，需要在导出记录里补充快照字段。
- 工作量、评教、班主任量化的打印页只展示汇总摘要和主体表，尚未把所有 Excel 明细字段都搬到打印页；当前这符合打印页不宜过密的原则，后续如需要可增加“明细附录”打印区。

## 5. 建议验证

本轮相关最小验证：

```bash
npm run backend:test -- apps/backend/tests/test_exam_workflow.py apps/backend/tests/test_archive_and_system.py apps/backend/tests/test_evaluation_quant_workflow.py apps/backend/tests/test_recommendation_exporters.py -q
npm run frontend:test -- tests/report-type-config.test.ts tests/recommendation-copy.test.ts
npm run frontend:build
```

如交付前做总验收，再运行：

```bash
npm run e2e -- --grep "报表主流程|报表打印扩展|报表异常提示" tests/e2e/dashboard-smoke.spec.ts
```
