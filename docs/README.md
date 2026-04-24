# 文档导航

这个目录同时放了规格文档、当前开发说明、外部交接 bundle 和历史参考材料。为了避免第一次进仓库时在大量 Markdown 里迷路，先按下面顺序看。

## 先看这些

1. [`local_edu_tool_dev_spec.md`](./local_edu_tool_dev_spec.md)
   项目规格与产品边界的主入口。
2. [`development_recommendations_2026-04-05.md`](./development_recommendations_2026-04-05.md)
   仓库结构优化建议，适合做整理、拆分、工程化时先看。
3. [`development_plan_to_delivery_2026-04-24.md`](./development_plan_to_delivery_2026-04-24.md)
   按当前进度整理的交付版后续开发计划，适合继续推进到投入使用前先看。
4. [`p0_delivery_runbook_2026-04-24.md`](./p0_delivery_runbook_2026-04-24.md)
   P0 本地交付验收手册，覆盖数据健康、备份恢复、恢复后启动和当前已知缺口。
5. [`dev/README.md`](./dev/README.md)
   当前开发主线、分工文档和 prompt 的索引。

## 当前仍在用的文档

- [`local_edu_tool_dev_spec.md`](./local_edu_tool_dev_spec.md)
  本地教务工具的规格说明，优先级最高。
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
- 想判断文档是不是历史遗留：
  先看这里的索引，再决定要不要进具体 bundle。

## 边界说明

- `docs/dev/` 放的是当前仍可直接指导开发的说明。
- 各种 `*_bundle*` 目录主要是阶段性打包资料或外部交接包，不是默认真相来源。
- 项目运行规则、当前进度和交接状态仍以 `memory-bank/` 与根目录 `README.md` 为准。
