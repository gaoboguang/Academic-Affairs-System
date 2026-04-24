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
12. [`dev/README.md`](./dev/README.md)
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
