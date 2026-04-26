# 文档导航

这个目录同时放了规格文档、当前开发说明、外部交接 bundle 和历史参考材料。为了避免第一次进仓库时在大量 Markdown 里迷路，先按下面顺序看。

## 先看这些

1. [`local_edu_tool_dev_spec.md`](./local_edu_tool_dev_spec.md)
   项目规格与产品边界的主入口。
2. [`repo-audit.md`](./repo-audit.md)
   窗口 0 生成的仓库审计，记录真实技术栈、目录、功能状态、启动状态和后续开发顺序。
3. [`repo-audit-2026-04-24.md`](./repo-audit-2026-04-24.md)
   按 Codex App v3 执行文档补齐的 dated 仓库审计与状态锁定。
4. [`current-development-map-2026-04-24.md`](./current-development-map-2026-04-24.md)
   按 Codex App v3 执行文档补齐的当前业务模块开发地图。
5. [`mac-dev-setup.md`](./mac-dev-setup.md)
   Mac 主开发流程，从零安装、配置、迁移、启动、测试和常见问题。
6. [`mac-user-startup-guide.md`](./mac-user-startup-guide.md)
   面向非程序员用户的 Mac 双击启动和排障说明。
7. [`mac-developer-checklist.md`](./mac-developer-checklist.md)
   面向 Codex / 开发窗口的 Mac 开发前后检查、备份和打包清单。
8. [`development-roadmap.md`](./development-roadmap.md)
   多窗口开发路线图，说明每个窗口负责范围、验收标准和公共文件保护清单。
9. [`development_recommendations_2026-04-05.md`](./development_recommendations_2026-04-05.md)
   仓库结构优化建议，适合做整理、拆分、工程化时先看。
10. [`development_plan_to_delivery_2026-04-24.md`](./development_plan_to_delivery_2026-04-24.md)
   按当前进度整理的交付版后续开发计划，适合继续推进到投入使用前先看。
11. [`p0_delivery_runbook_2026-04-24.md`](./p0_delivery_runbook_2026-04-24.md)
   P0 本地交付验收手册，覆盖数据健康、备份恢复、恢复后启动和当前已知缺口。
12. [`test-quality-audit-2026-04-24.md`](./test-quality-audit-2026-04-24.md)
   窗口 8 的测试体系、质量门禁和回归脚本审计。
13. [`codex-task-acceptance-checklist.md`](./codex-task-acceptance-checklist.md)
   后续 Codex 窗口按改动类型选择验证命令的收尾清单。
14. [`final-acceptance-report-2026-04-24.md`](./final-acceptance-report-2026-04-24.md)
   窗口 9 的最终整合、质量门禁、P0 验收和是否建议试用结论。
15. [`import-system-audit-2026-04-24.md`](./import-system-audit-2026-04-24.md)
   窗口 2 的导入体系审计与统一治理记录，覆盖导入入口、错误报告、批次摘要、导入中心和回滚边界。
16. [`round4-baseline-audit.md`](./round4-baseline-audit.md)
   第四轮 E0 的学生批量操作、批量调班和数据库补齐基线审计。
17. [`round4-data-completion-plan.md`](./round4-data-completion-plan.md)
   第四轮 E5 的数据库补齐审计、可补项计划和 E6 导入任务清单。
18. [`round4-official-source-checklist.md`](./round4-official-source-checklist.md)
   第四轮 E5 的山东官方来源核对清单，区分可导入、需人工下载、需复核和未发布数据。
19. [`round4-data-completion-result.md`](./round4-data-completion-result.md)
   第四轮 E6 的数据库补齐导入结果，记录 2020-2022 一分一段和省控线导入、来源追溯、SHA256、补齐前后差异和剩余缺口。
20. [`round4-user-guide-student-bulk-actions.md`](./round4-user-guide-student-bulk-actions.md)
   第四轮面向老师的学生批量删除、批量调班和调班历史查看说明。
21. [`round4-user-guide-data-completion.md`](./round4-user-guide-data-completion.md)
   第四轮面向老师的高考数据库补齐、年份覆盖矩阵、剩余缺口和打印覆盖报告说明。
22. [`round4-final-acceptance-report.md`](./round4-final-acceptance-report.md)
   第四轮 E8 的最终集成验收报告，记录 E0-E7 整合、完整测试、剩余数据缺口和是否可合并 main。
23. [`gaokao-source-import-framework-2026-04-25.md`](./gaokao-source-import-framework-2026-04-25.md)
   窗口 A1 的山东高考官方来源登记、导入批次和本地文件入场框架。
24. [`round3-shandong-pathway-rules.md`](./round3-shandong-pathway-rules.md)
   第三轮 D2 的山东升学路径规则字典、官方来源追溯和后续窗口注意事项。
25. [`round3-student-pathway-profile.md`](./round3-student-pathway-profile.md)
   第三轮 D3 的学生升学画像、材料缺口和路径评估可读化说明。
26. [`round3-gaokao-pathway-center.md`](./round3-gaokao-pathway-center.md)
   第三轮 D4 的山东升学方案中心页面、路径卡片和数据风险入口说明。
27. [`round3-shandong-general-recommendation-hardening.md`](./round3-shandong-general-recommendation-hardening.md)
   第三轮 D5 的山东普通类推荐算法加固、共享分数换位次和 2026 数据提示说明。
28. [`round3-vocational-spring-pathway-screening.md`](./round3-vocational-spring-pathway-screening.md)
   第三轮 D6 的高职单招、高职综评、春季高考本科/专科路径初筛、材料缺口和人工复核说明。
29. [`round3-special-early-art-sports-pathways.md`](./round3-special-early-art-sports-pathways.md)
   第三轮 D7 的艺体、体育、提前批、特殊类型、体育单招和高水平运动队路径初筛、材料缺口和人工复核说明。
30. [`round3-shandong-pathway-final-report.md`](./round3-shandong-pathway-final-report.md)
   第三轮 D8 的最终集成、验收、报告输出和交接说明。
31. [`round3-shandong-pathway-user-guide.md`](./round3-shandong-pathway-user-guide.md)
   面向老师使用山东升学方案中心、路径卡片、材料缺口、打印和 Excel 报告的说明。
32. [`report-export-print-audit-2026-04-24.md`](./report-export-print-audit-2026-04-24.md)
   窗口 6 的报表、打印、Excel 导出一致性审计与修复记录。
33. [`frontend-navigation-audit-2026-04-24.md`](./frontend-navigation-audit-2026-04-24.md)
   窗口 7 的前端导航、空态、错误提示和非程序员可读性审计记录。
34. [`dev/README.md`](./dev/README.md)
   当前开发主线、分工文档和 prompt 的索引。

## 当前仍在用的文档

- [`local_edu_tool_dev_spec.md`](./local_edu_tool_dev_spec.md)
  本地教务工具的规格说明，优先级最高。
- [`repo-audit.md`](./repo-audit.md)
  窗口 0 仓库审计结果，后续 Codex 窗口先读。
- [`repo-audit-2026-04-24.md`](./repo-audit-2026-04-24.md)
  v3 执行文档指定的 dated 仓库审计与状态锁定。
- [`current-development-map-2026-04-24.md`](./current-development-map-2026-04-24.md)
  v3 执行文档指定的业务模块开发地图。
- [`mac-dev-setup.md`](./mac-dev-setup.md)
  Mac 环境、依赖、启动、测试和常见问题说明。
- [`mac-user-startup-guide.md`](./mac-user-startup-guide.md)
  普通用户在 Mac 上第一次准备、双击启动、命令启动和排障说明。
- [`mac-developer-checklist.md`](./mac-developer-checklist.md)
  Codex / 开发窗口的 Mac 检查清单，覆盖验证、备份和桌面打包前置检查。
- [`development-roadmap.md`](./development-roadmap.md)
  后续多窗口开发路线图。
- [`development_recommendations_2026-04-05.md`](./development_recommendations_2026-04-05.md)
  针对“仓库开始变乱”后的结构化建议。
- [`development_plan_to_delivery_2026-04-24.md`](./development_plan_to_delivery_2026-04-24.md)
  当前高考志愿主线到交付可用的后续计划和验收标准。
- [`p0_delivery_runbook_2026-04-24.md`](./p0_delivery_runbook_2026-04-24.md)
  当前 P0 安全底座验收步骤和恢复演练入口。
- [`test-quality-audit-2026-04-24.md`](./test-quality-audit-2026-04-24.md)
  当前测试覆盖、质量门禁和 E2E 覆盖面的窗口 8 审计。
- [`codex-task-acceptance-checklist.md`](./codex-task-acceptance-checklist.md)
  后续 Codex 每个窗口的验收命令选择规则。
- [`final-acceptance-report-2026-04-24.md`](./final-acceptance-report-2026-04-24.md)
  窗口 9 的最终整合结果，包含完整验证、P0 备份恢复验收、Mac 启动方式和当前试用建议。
- [`import-system-audit-2026-04-24.md`](./import-system-audit-2026-04-24.md)
  窗口 2 对学生、教师、成绩、课表、录取数据、招生计划等导入入口与 `/import-center` 的统一治理记录。
- [`round4-baseline-audit.md`](./round4-baseline-audit.md)
  第四轮 E0 对学生批量删除、批量调班、成长档案系统事件和数据库补齐入口的基线审计。
- [`round4-data-completion-plan.md`](./round4-data-completion-plan.md)
  第四轮 E5 对数据库补齐缺口、可补项、不可补边界和 E6 导入顺序的审计计划。
- [`round4-official-source-checklist.md`](./round4-official-source-checklist.md)
  第四轮 E5 对 2020-2026 山东高考官方来源、招生计划补充信息、政策参考和章程复核的检查清单。
- [`round4-data-completion-result.md`](./round4-data-completion-result.md)
  第四轮 E6 对 2020-2022 一分一段和省控线的实际导入结果、来源追溯、SHA256 和剩余缺口记录。
- [`round4-user-guide-student-bulk-actions.md`](./round4-user-guide-student-bulk-actions.md)
  第四轮学生批量删除、批量调班、调班历史和成长档案系统事件的老师使用说明。
- [`round4-user-guide-data-completion.md`](./round4-user-guide-data-completion.md)
  第四轮高考数据库补齐结果、年份覆盖矩阵、剩余缺口和打印覆盖报告的老师使用说明。
- [`round4-final-acceptance-report.md`](./round4-final-acceptance-report.md)
  第四轮 E8 最终集成验收报告，记录批量操作、调班、数据补齐、完整验证和合并结论。
- [`gaokao-source-import-framework-2026-04-25.md`](./gaokao-source-import-framework-2026-04-25.md)
  窗口 A1 对山东高考官方来源文档、导入运行批次和本地文件目录的框架说明。
- [`round3-shandong-pathway-rules.md`](./round3-shandong-pathway-rules.md)
  第三轮 D2 对山东多升学路径官方规则字典、来源追溯和 bootstrap 边界的说明。
- [`round3-student-pathway-profile.md`](./round3-student-pathway-profile.md)
  第三轮 D3 对学生升学画像、资格材料缺口和路径评估可读提示的说明。
- [`round3-gaokao-pathway-center.md`](./round3-gaokao-pathway-center.md)
  第三轮 D4 对山东升学方案中心、路径卡片、详情抽屉和数据风险入口的说明。
- [`round3-shandong-general-recommendation-hardening.md`](./round3-shandong-general-recommendation-hardening.md)
  第三轮 D5 对山东普通类冲稳保推荐加固、共享一分一段换位次和 2026 官方计划缺失提示的说明。
- [`round3-vocational-spring-pathway-screening.md`](./round3-vocational-spring-pathway-screening.md)
  第三轮 D6 对高职单招、高职综评、春季高考本科/专科路径初筛、材料缺口和人工复核清单的说明。
- [`round3-special-early-art-sports-pathways.md`](./round3-special-early-art-sports-pathways.md)
  第三轮 D7 对艺体、体育、提前批、特殊类型、体育单招和高水平运动队路径初筛、材料缺口和人工复核清单的说明。
- [`round3-shandong-pathway-final-report.md`](./round3-shandong-pathway-final-report.md)
  第三轮 D8 最终集成报告，记录 D1-D8 成果、报告输出、数据健康、验收和边界。
- [`round3-shandong-pathway-user-guide.md`](./round3-shandong-pathway-user-guide.md)
  山东升学方案中心使用说明，适合非程序员老师按步骤查看路径卡、补材料、打印或导出报告。
- [`report-export-print-audit-2026-04-24.md`](./report-export-print-audit-2026-04-24.md)
  窗口 6 对报表中心、打印页和 Excel 导出的一致性审计与修复记录。
- [`frontend-navigation-audit-2026-04-24.md`](./frontend-navigation-audit-2026-04-24.md)
  窗口 7 对导航结构、复杂页说明、空态与错误提示的审计记录。
- [`dev/`](./dev/)
  当前工作流文档和阶段计划。
- [`../tests/README.md`](../tests/README.md)
  当前测试布局和定向回归入口。

## 参考 bundle

- [`gaokao_dev_bundle_v3/`](./gaokao_dev_bundle_v3/)
  当前高考志愿主线最值得优先参考的一组文档。
- [`gaokao_docs_bundle_v2/`](./gaokao_docs_bundle_v2/)
  较早一轮的高考资料包，适合查背景和历史说明。
- [`local_edu_tool_dev_doc_v2_bundle/`](./local_edu_tool_dev_doc_v2_bundle/)
  较早阶段的项目开发文档快照。
- [`codex_dev_docs_bundle_2026-04-14/`](./codex_dev_docs_bundle_2026-04-14/)
  一组外部规划/拆解材料，适合做交叉参考，不是日常开发入口。

## 建议阅读路径

- 想理解项目边界：
  先看 `local_edu_tool_dev_spec.md`，再看 `memory-bank/project-context.md`。
- 想做结构整理：
  先看 `development_recommendations_2026-04-05.md`，再看 `dev/README.md`。
- 想继续高考主线：
  先看 `development_plan_to_delivery_2026-04-24.md`，再看 `gaokao_dev_bundle_v3/`，不要先扎进旧 bundle。
- 想在 Mac 上启动或交接启动体验：
  普通用户先看 `mac-user-startup-guide.md`，开发窗口先看 `mac-developer-checklist.md`。
- 想判断文档是不是历史遗留：
  先看这里的索引，再决定要不要进具体 bundle。

## 边界说明

- `docs/dev/` 放的是当前仍可直接指导开发的说明。
- 各种 `*_bundle*` 目录主要是阶段性打包资料或外部交接包，不是默认真相来源。
- 项目运行规则、当前进度和交接状态仍以 `memory-bank/` 与根目录 `README.md` 为准。
