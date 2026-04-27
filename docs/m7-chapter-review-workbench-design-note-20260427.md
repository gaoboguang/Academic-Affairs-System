# M7 章程复核工作台补充设计说明

日期：2026-04-27

## 结论

开发文档 M7 要求增强“章程限制链人工复核工作台”：优先级、状态筛选、官方候选链接、复核备注、导出清单。当前仓库已经完成只读审阅工作台和证据链展示；“复核备注写入”和“专门导出清单”不应在没有明确字段与更新接口的情况下硬做，因此本说明按开发文档约束补齐设计交接。

## 已落地范围

1. `/gaokao-data` 的“数据审阅”页签已支持：
   - 审阅状态筛选：全部、待人工复核、待人工复核（已有官方候选）、仍未解决。
   - 优先级排序：优先级优先、最近更新时间。
   - 学校名、学校代码、省份、招生网关键词检索。
   - 快捷过滤、队列统计、优先级原因、重复组 / 同名组对比。
   - 招生网、章程入口、fallback 链接、来源标题 / URL、更新时间和单校证据链查看。
2. 后端 `/api/gaokao/review-summary` 已支持 `filter`、`focus`、`sort`、`keyword`，并优先读取 `gaokao_college_chapter_rule`，兼容 `gaokao_college` / `gaokao_policy_reference` 兜底字段。
3. `/api/gaokao/college-evidence/{college_id}` 已展示单校官方站、招生网、章程入口、备用链接、来源链接、审阅状态、抓取状态和说明。
4. 推荐页、志愿输出和 Excel 导出已持续保留章程待人工复核风险，不把机器预审包装成已确认。

## 未直接实现的原因

1. **复核备注写入**：当前可读字段包括 `review_status`、`retrieval_status`、`source_title`、`source_url`、`chapter_url`、`chapter_fallback_url`、`updated_at` 等，但没有明确的人工复核备注写入字段、操作者字段和更新接口。若直接复用无关字段，会污染证据链。
2. **专门导出清单**：当前已有推荐结果导出风险提示，但高考数据审阅队列尚无独立 Excel / CSV 导出入口。这个功能可以基于现有只读汇总生成，不需要数据库迁移，但需要新增导出端点和前端按钮。

## 后续实现建议

1. 先新增只读导出端点，例如 `GET /api/gaokao/review-summary/export`，参数与 `/api/gaokao/review-summary` 保持一致。
2. 导出字段建议固定为：
   - 优先级：`priority_code`、`priority_label`、`priority_score`、`priority_reasons`
   - 学校：`college_id`、`college_code`、`college_name`、`province`
   - 状态：`review_status`、`retrieval_status`
   - 链接：`recruit_site`、`chapter_url`、`fallback_url`、`source_title`、`source_url`
   - 分组：`duplicate_group_key`、`same_name_group_key`
   - 时间和建议：`updated_at`、`suggested_action`
3. 复核备注如需真正写入，应先确认是否可以在 `gaokao_college_chapter_rule` 增加 `review_note`、`reviewed_by`、`reviewed_at` 等字段，并通过 Alembic 迁移落地；在这之前，只允许展示现有备注/来源说明，不应写库。
4. 若只需临时人工清单，可先导出 CSV / XLSX 供线下标注，再由单独导入流程带审计摘要回写，避免前端页面直接绕过数据安全规则。

## 当前验收口径

M7 当前按“只读工作台 + 风险可见 + 设计说明”闭环。后续若用户明确要求在线复核闭环，再进入数据库字段设计、迁移、导出端点和回写审计实现。
