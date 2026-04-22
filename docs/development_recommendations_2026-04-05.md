# 开发建议与后续改造说明

- 日期：2026-04-05
- 用途：给后续继续接手本仓库的 Codex 作为结构优化与开发优先级参考
- 范围：本次仅基于当前仓库静态结构、配置和目录分层给出建议，不代表产品范围要调整

## 当前判断

当前仓库没有致命结构错误，仍然具备继续开发和增量重构的基础。

已有优点：

- 前后端分离明确，位于 `apps/backend` 与 `apps/frontend`
- 后端已具备 `api/routes -> services -> repositories -> models/schemas` 的基础分层
- 根目录有 `docs/`、`scripts/`、`data/`、`README.md`，整体工程边界清楚
- 运行产物如 `node_modules`、`dist`、`.venv`、数据库、导出文件当前未被 git 跟踪

当前主要问题不是“目录乱”，而是“复杂度开始堆进少数超大文件”，继续扩展会明显变慢。

## 主要问题

### 1. 前端页面文件过大

当前多个页面已经达到不适合继续直接堆逻辑的体量，例如：

- `apps/frontend/src/pages/RecommendationsPage.vue` 约 2882 行
- `apps/frontend/src/pages/EvaluationQuantPage.vue` 约 1708 行
- `apps/frontend/src/pages/TimetableWorkloadPage.vue` 约 1415 行

风险：

- 页面状态、请求、表单、弹窗、图表、表格逻辑耦合
- 修改局部功能时回归风险高
- 后续新增需求容易继续把页面写成“大总管”

建议：

- 以业务域拆分页面，而不是继续只靠 `pages/`
- 将页面中的筛选区、表格区、弹窗区、分析区、导入导出区拆到独立组件
- 将接口访问和状态协调抽到 composables 或 feature 内部 service 文件

建议目标结构示例：

```text
apps/frontend/src/features/recommendations/
  components/
  composables/
  api.ts
  types.ts
  constants.ts
  sections/
```

然后由 `pages/RecommendationsPage.vue` 只负责页面装配。

### 2. 后端 service 文件开始膨胀

当前后端存在明显超大 service 文件，例如：

- `apps/backend/app/services/evaluation.py` 约 1231 行
- `apps/backend/app/services/recommendations.py` 约 869 行
- `apps/backend/app/services/students.py` 约 611 行

风险：

- 一个文件同时承担查询编排、规则计算、导入导出协调、聚合返回
- 难以对核心计算逻辑做小范围测试
- 后续需求变化时，容易出现“改一处动全身”

建议：

- 保留 `services` 作为业务入口，但将大模块拆成包
- 把“规则计算”“查询聚合”“导出组装”“工作流编排”拆成不同文件
- 复杂计算优先下沉到 `analytics`、`rules` 或独立 `services/<domain>/` 子模块

建议目标结构示例：

```text
apps/backend/app/services/recommendations/
  __init__.py
  workflow.py
  strategy.py
  explain.py
  filters.py
  exports.py
```

`api/routes/*.py` 只调用稳定的 service 入口，不直接承载复杂编排。

### 3. 测试目录约定不一致

当前现状：

- 根目录 `tests/` 存在，但为空
- `apps/backend/pyproject.toml` 里 `pytest` 的 `testpaths` 指向 `apps/backend/tests`
- README 的目录结构仍然展示根级 `tests/`

这会导致后续开发者不清楚：

- 单元测试应该放根目录还是后端内部
- 前端测试未来应该落在哪里
- e2e 测试是否应该放根目录

建议尽快统一约定，推荐二选一：

方案 A：

- 后端单元测试继续放 `apps/backend/tests`
- 前端单元测试放 `apps/frontend/src/**/__tests__` 或 `apps/frontend/tests`
- 根目录 `tests/` 专门保留给跨端 e2e

方案 B：

- 全部测试统一到根目录 `tests/`
- 但这需要同步重构 pytest 与前端测试配置

更建议采用方案 A，改动更小，也更符合当前仓库现状。

### 4. Monorepo 只完成了一半

当前根目录 `package.json` 只管理前端 workspace，后端没有统一入口脚本。

现状可用，但问题在于：

- 根目录没有统一的后端开发、测试、迁移命令
- 后续 CI 或日常维护时，需要记忆多套入口
- “monorepo” 在目录层成立，在任务编排层不完全成立

建议：

- 保留 Python 后端独立构建方式，不必强行把后端纳入 npm workspace
- 但要在根目录补齐统一脚本入口，例如：
  - `backend:test`
  - `backend:migrate`
  - `backend:init-demo`
  - `dev`

目标不是统一技术栈，而是统一操作入口。

### 5. 运行态内容与版本化内容需要继续明确边界

当前 `data/` 目录符合规格文档要求，应该继续保留在仓库根。

但建议继续强化以下约定：

- `data/uploads/`、`data/exports/`、`data/backups/` 只放运行生成物
- `data/templates/` 如果是运行时自动生成模板，继续不纳入版本控制
- 模板的“生成逻辑”应该放在源码里，而不是依赖手工维护静态文件
- README 里应明确哪些内容是运行生成、哪些内容是需要手工准备

这不是要把 `data/` 挪走，而是要减少“本地生成物看起来像源码资产”的混淆。

### 6. 前端工程质量工具还没补齐

当前前端 `lint` 还是占位命令，且未见前端单元测试落地。

这与 `AGENTS.md` 中推荐的 `Vitest`、`Playwright` 方向不一致。

建议：

- 先补 ESLint，不要求一次性清空全部历史告警
- 再给高风险业务域补最小可用的 Vitest
- e2e 只覆盖关键主流程，不要一开始全量铺开

## 建议的改造优先级

### P1 先做

1. 拆前端超大页面，优先 `RecommendationsPage.vue`
2. 拆后端超大 service，优先 `evaluation.py`
3. 统一测试目录规则并在 README 中写清

### P2 再做

1. 补根目录统一脚本入口
2. 补前端 lint 和最小单测
3. 清理和文档化 `data/` 的运行态边界

### P3 后续优化

1. 继续按业务域整理前端目录
2. 继续把后端复杂规则下沉到更细粒度模块
3. 再考虑更大范围的构建、打包、CI 统一

## 明天继续修改时的建议切入点

如果下一位 Codex 需要继续改结构，建议按以下顺序推进：

1. 先只拆一个前端页面，验证拆分模式
2. 再只拆一个后端超大 service，验证包结构
3. 然后补 README 与测试约定
4. 最后再考虑统一脚本和工程化细节

不建议一开始同时大改前端、后端、测试目录和脚本入口，否则回归面太大。

## 推荐的第一批落地任务

### 任务 1：拆 `RecommendationsPage.vue`

最低目标：

- 保持现有功能不变
- 只把筛选区、推荐结果区、方案详情区、弹窗拆走
- 页面保留路由入口与顶层状态编排

### 任务 2：拆 `app/services/evaluation.py`

最低目标：

- 保持 API 形态不变
- 拆出规则计算、导入处理、汇总统计三个子模块
- 在拆分前后保持现有测试通过

### 任务 3：统一测试说明

最低目标：

- 明确根目录 `tests/` 的用途
- 若暂时不用根目录测试，则在 README 中说明
- 给前端测试预留目录，不必一次性写完测试

## 不建议现在做的事

- 不要把整个仓库一次性重排目录
- 不要为了“更像标准 monorepo”强行改掉 Python 后端工作流
- 不要在没有测试保护的情况下重写推荐与量化核心逻辑
- 不要把大量业务规则从后端搬回前端
- 不要改变项目的核心定位：本地、单用户、离线优先、中文后台

## 给下一位 Codex 的一句话结论

这个仓库的问题不在基础骨架，而在“复杂业务已经开始集中到少数超大文件”。下一步最有效的工作不是重搭架构，而是做小步、可回归、按业务域的拆分。
