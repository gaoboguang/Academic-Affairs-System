# Codex 任务验收清单

本清单用于每个后续开发窗口收尾。原则：先跑最小相关检查，再按风险扩大；失败时修原因，不删测试、不跳过门禁。

## 1. 通用收尾

每个窗口至少确认：

1. `git status --short --branch`：确认自己改了哪些文件，识别是否存在其它窗口留下的改动。
2. 运行和改动范围匹配的定向测试。
3. `git diff --check`：确认没有空白和补丁格式问题。
4. 若改动影响接手成本，更新 `memory-bank/handoff.md`；阶段性完成时同步 `progress.md`。

## 2. 按改动类型选择检查

| 改动类型 | 必跑 | 视情况加跑 |
| --- | --- | --- |
| 后端接口、service、repository、exporter | `npm run backend:test -- <相关测试文件>` | `npm run backend:test`、`npm run check` |
| 前端页面、组件、helper、文案 | `npm run frontend:test -- <相关测试文件>`、`npm run frontend:build` | `npm run frontend:lint`、相关 Playwright |
| 数据库 model / Alembic 迁移 | 定向后端测试、临时库 `npm run backend:migrate` | `npm run backend:p0-check -- --json` |
| 会写 `data/app.db` 的脚本 | 脚本自带备份验证、`npm run backend:data-health -- --json` | `npm run backend:p0-check -- --json` |
| 高考数据、山东覆盖、规则字典 | `npm run backend:test -- apps/backend/tests/test_gaokao_api.py apps/backend/tests/test_data_health.py -q` | `npm run backend:p0-check -- --json`、相关前端构建或 E2E |
| 推荐 / 高考志愿解释链 | `npm run backend:test -- apps/backend/tests/test_recommendation_workflow.py apps/backend/tests/test_recommendation_exporters.py -q`、相关前端推荐测试 | `npm run check:e2e` 或定向 `--grep` |
| 报表、打印、Excel 导出 | `npm run backend:test -- apps/backend/tests/test_recommendation_exporters.py apps/backend/tests/test_exam_workflow.py -q`、相关 `report-*` 前端测试 | 报表相关 Playwright |
| 导入体验、错误报告、导入中心 | `npm run backend:test -- apps/backend/tests/test_student_importer.py apps/backend/tests/test_archive_and_system.py -q`、`npm run frontend:test -- tests/import-feedback.test.ts tests/import-center.test.ts` | `npm run check:e2e` 的导入相关流程 |
| 桌面端或启动脚本 | `npm run frontend:build`、`node scripts/dev-local.cjs --help` 或相关脚本 `--help` | `npm run desktop:prepare`、`npm run desktop:dist:mac` |
| 文档-only | `git diff --check` | 如文档描述命令行为，运行对应命令的 `--help` 或 `--list` |

## 3. 根级门禁怎么读

- `npm run check`：日常代码门禁。看到“质量门禁通过”表示后端全量、前端 lint、前端单测和前端构建都通过。
- `npm run check:e2e`：跨端流程门禁。失败时先看第一条 Playwright 失败和 trace，不要先改无关页面。
- `npm run check:all`：完整门禁。适合阶段合并、公共文件修改后和交付前。
- `npm run backend:p0-check -- --json`：P0 本地交付安全底座。`ok: true` 表示健康检查、备份、临时恢复和恢复后接口检查通过；有数据 warning 不等于数据已补齐。

## 4. 失败处理规则

1. 先记录失败命令、失败阶段、第一条报错。
2. 判断是否与本窗口改动相关；相关则修复，不相关也要在最终说明中明确残留风险。
3. 不用删除测试、降低断言、跳过 E2E 的方式制造绿色结果。
4. 如果是缺依赖或本机环境问题，按 `docs/mac-dev-setup.md` 和脚本输出补环境，再重跑。
5. 如果完整门禁太慢，先跑定向测试，但最终汇报必须说明没有跑完整门禁的原因。

## 5. 非程序员结果口径

- 通过：对应范围可以继续合并或交给下一窗口。
- 警告：代码检查过了，但数据、环境、Windows 或桌面打包仍有未验项。
- 不通过：不要交付使用；先处理第一条失败，再重跑同一命令。
