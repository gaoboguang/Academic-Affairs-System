# Academic-Affairs-System / 本地教务工具：Codex App 后续开发执行文档 v3

> 适用对象：Codex App 中的开发 agent。  
> 使用者背景：项目 owner 不具备编程基础，后续开发请由 Codex 全权读取仓库、判断实现、修改代码、运行测试、用中文汇报。  
> 开发主阵地：Mac。后续说明、脚本验证、桌面打包优先以 macOS 为准。  
> 生成时间：2026-04-24。  
> 依据来源：已连接 GitHub 仓库 `gaoboguang/Academic-Affairs-System` 的 README、`package.json`、项目记忆，以及当前项目“本地教务系统开发”上下文。

---

## 0. 给 Codex 的最高优先级指令

你不是来给用户讲技术方案的，而是来直接接管开发的。

用户不懂编程，所以不要把技术决策抛给用户。除非存在业务含义不明确、会改变产品方向或会造成数据丢失的风险，否则你必须自行读取仓库、做技术判断、修改代码、运行验证，并用中文报告结果。

每个 Codex 窗口都必须遵守：

1. **先读仓库，再动代码**
   - 必读：`README.md`、`AGENTS.md`、`docs/local_edu_tool_dev_spec.md`、`memory-bank/active-context.md`、`memory-bank/handoff.md`。
   - 与高考志愿 / 推荐 / 数据健康相关的任务，还必须读：`gaokao_dev_bundle_v3/gaokao_dev_doc_v3.md`、`docs/p0_delivery_runbook_2026-04-24.md`。
   - 与脚本、启动、测试相关的任务，还必须读：`package.json`、`scripts/README.md`、`tests/README.md`。

2. **不要重建项目**
   - 这是已经高度开发过的项目，不是空项目。
   - 禁止另起炉灶、重写技术栈、替换框架、删除已有模块。
   - 必须沿用现有架构、现有命名、现有 API 风格、现有测试方式。

3. **不要只写方案**
   - 任务要求开发时，必须实际修改代码。
   - 必须尽量运行对应测试或检查命令。
   - 如果测试无法运行，必须说明原因、已尝试命令、阻塞点、下一步建议。

4. **所有结果必须中文汇报**
   - 用户不是开发者，最终报告必须用中文。
   - 报告中必须包含：改了什么、解决了什么、运行了哪些命令、是否通过、是否还有风险。

5. **保护数据和现有成果**
   - 禁止无备份地覆盖 `data/app.db`、`data/local_edu_tool/local_edu.sqlite3`、`data/backups/`、`handoffs/`。
   - 需要修改数据库结构时，优先使用 Alembic migration、初始化脚本、物化脚本，而不是直接手工改二进制数据库。
   - 需要写入规则数据或演示数据时，必须先确认脚本已有备份机制；没有备份机制就补备份机制。

6. **遵守 `AGENTS.md` 规则**
   - 仓库 README 提到 `AGENTS.md` 由 `rulesync.jsonc` 和 `.rulesync/` 来源维护，不建议手工改生成结果。
   - 因此除非任务明确要求更新 agent 规则，否则不要直接编辑 `AGENTS.md`。
   - 如果确实需要更新 agent 规则，先查清楚 rulesync 的来源文件，再按项目规则更新。

---

## 1. 当前仓库真实基线

### 1.1 项目定位

项目名称在 README 中体现为：**本地教务工具**。

项目目标：面向高中场景的本地单机教务决策台。它不是 SaaS，也不是纯网页 Demo，而是本地运行、本地数据库、本地导入导出、本地桌面壳的教务系统。

核心特征：

- 本地单机运行。
- 面向高中教务场景。
- 支持基础数据、学生、教师、任教关系、考试、成绩、课表、工作量、成长档案、评教、报表、高考志愿、本地备份恢复。
- 当前已经进入较深的高考志愿 / 推荐 / 数据健康阶段，不是早期骨架阶段。

### 1.2 技术栈

后端：

- `FastAPI`
- `SQLAlchemy`
- `SQLite`
- `Alembic`
- Python 3.11+

前端：

- `Vue 3`
- `TypeScript`
- `Vite`
- `Element Plus`
- `Vitest`
- `ESLint`

桌面端：

- `Electron`
- 后端独立二进制
- macOS / Windows 打包能力已存在，但当前后续开发以 Mac 为主

工程结构：

```text
local-edu-tool/
  apps/
    backend/
    frontend/
    desktop/
  data/
    local_edu_tool/
    uploads/
    backups/
    templates/
    exports/
    logs/
  docs/
  handoffs/
  scripts/
  tests/
  memory-bank/
```

### 1.3 关键运行命令

根目录命令以 `package.json` 为准。

常用开发命令：

```bash
npm run dev
```

常用检查命令：

```bash
npm run check
npm run check:e2e
npm run check:all
```

后端相关：

```bash
npm run backend:dev
npm run backend:migrate
npm run backend:init-demo
npm run backend:test
npm run backend:data-health
npm run backend:p0-check
npm run backend:merge-handoff
npm run backend:materialize-gaokao
npm run backend:bootstrap-special-types -- --year 2025 --year 2026
```

前端相关：

```bash
npm run frontend:dev
npm run frontend:lint
npm run frontend:test
npm run frontend:build
```

E2E：

```bash
npm run e2e:install
npm run e2e
```

桌面端：

```bash
npm run desktop:dev
npm run desktop:prepare
npm run desktop:dist:mac
```

### 1.4 数据库约定

当前主库：

```text
data/app.db
```

高考 / handoff 相关 fallback 或同步来源：

```text
data/local_edu_tool/local_edu.sqlite3
handoffs/2026-04-21_mac_db_handoff
```

重要规则：

- 2026-04-22 起，若 `data/app.db` 已嵌入 `gaokao_*` 原始表、`data_import_batch`、`score_rank_segment` 等 handoff 表，应用优先走单库。
- `data/local_edu_tool/local_edu.sqlite3` 更适合作为 handoff 同步来源和 fallback 输入。
- 改库前必须先备份。
- 交付前或补数据前必须运行：

```bash
npm run backend:data-health
npm run backend:data-health -- --json
npm run backend:p0-check
```

---

## 2. 当前进度判断

### 2.1 已完成或已有基础的模块

根据 README 当前描述，以下模块已经有明显实现，不要重复从零建设：

- Monorepo 基础骨架。
- SQLite 与 Alembic 初始化。
- 本地 `data/` 目录约定。
- 模板生成与导入导出基础。
- 工作台摘要接口与页面。
- 基础数据管理：学年、学期、年级、班级、学科、字典。
- 学生管理：列表、详情、创建、更新、模板下载、Excel 导入导出。
- 教师管理：列表、详情、创建、更新、模板下载、Excel 导入导出。
- 任教关系维护与列表。
- 考试管理：考试列表、详情、新增、编辑。
- 考试科目配置。
- 成绩导入：模板下载、Excel 导入、错误报告、导入批次记录。
- 成绩快照与分析中心。
- 课表管理、未匹配项修正、工作量规则、工作量计算、Excel 导出。
- 成长档案。
- 推荐中心：院校库、专业库、录取库、普通生/艺体生推荐、策略模板、历史回放、报告导出。
- 高考志愿工作台：招生计划、省份规则、就业方向、职业匹配、志愿草稿、打印/导出。
- 高考数据只读驾驶舱：数据总览、数据审阅、院校证据页、山东监控、数据健康看板。
- 报表中心：多类核心报表导出与打印预览。
- 系统工具：上传、备份、恢复、审计日志。
- 桌面端：Electron 壳、macOS 目录产物、Windows 产物能力。
- 前端工程化：ESLint、Vitest、Playwright。

### 2.2 当前主线

当前主线不是“把教务系统搭起来”，而是继续收口已有大系统：

1. **Mac 主开发环境稳定化**
   - 让普通用户在 Mac 上更容易启动、验证、打包。
   - 收口 Windows 旧描述，保留必要兼容但不作为主线。

2. **P0 数据健康与山东规则覆盖**
   - `backend:data-health`、`backend:p0-check`、`/gaokao-data` 山东覆盖页签已经存在。
   - 后续应继续补规则缺口解释、覆盖矩阵、审计摘要、特殊类型数据风险表达。

3. **高考志愿 Stage B 后续细化**
   - 已落地山东 2025/2026 规则、特殊类型规则、赋分规则、选科字典、就业方向映射。
   - 后续应补更多省份 / 年份边界、规则缺口解释、跨年份样本提示、特殊类型风险说明。

4. **统一导入体验继续收口**
   - 学生、教师、成绩、课表、招生计划、高考数据等已有导入能力，但可能分散。
   - 后续应做“统一导入中心 / 导入批次 / 错误报告 / 模板下载 / 回滚 / 审计”的一致性治理。

5. **核心教务链路回归**
   - 学生 → 班级 → 任教 → 考试 → 成绩 → 分析 → 报表。
   - 课表 → 工作量 → 报表。
   - 推荐 / 高考志愿不能破坏基础教务链路。

6. **报告、打印、导出一致性**
   - README 显示多个摘要和 Excel/打印链已逐步统一。
   - 后续开发要继续保持页面、导出前摘要、打印页、Excel 的风险表达一致。

---

## 3. Codex App 多窗口开发总策略

### 3.1 不要一次开太多窗口

推荐顺序：

1. 先开 **窗口 0：仓库审计与当前状态锁定**。
2. 窗口 0 完成后，再开 **窗口 1：Mac 环境与启动体验**。
3. 窗口 0 和窗口 1 都完成后，再并行开功能窗口。
4. 最后开 **窗口 9：最终整合、测试、验收**。

不要同时开启所有窗口。建议最多同时运行 3 个功能窗口，避免冲突。

### 3.2 使用 Worktree

每个 Codex 窗口建议使用 Codex App 的 Worktree 模式。

每个窗口单独一个分支，避免互相覆盖。

建议分支名：

```text
codex/00-audit-state-lock
codex/01-mac-startup-polish
codex/02-import-center-unification
codex/03-gaokao-data-health-p0
codex/04-volunteer-recommendation-stage-b
codex/05-core-academic-regression
codex/06-reports-export-print
codex/07-frontend-ux-cleanup
codex/08-tests-and-quality-gates
codex/09-final-integration-release
```

### 3.3 每个窗口结束时必须输出

每个 Codex 窗口结束时，必须用中文输出：

```text
1. 本窗口任务目标
2. 已修改文件列表
3. 新增文件列表
4. 删除文件列表
5. 运行过的命令
6. 测试 / 构建 / 检查结果
7. 没有完成的内容
8. 需要下一个窗口注意的事项
9. 是否建议合并
```

### 3.4 合并顺序建议

推荐合并顺序：

1. `codex/00-audit-state-lock`
2. `codex/01-mac-startup-polish`
3. `codex/02-import-center-unification`
4. `codex/03-gaokao-data-health-p0`
5. `codex/04-volunteer-recommendation-stage-b`
6. `codex/05-core-academic-regression`
7. `codex/06-reports-export-print`
8. `codex/07-frontend-ux-cleanup`
9. `codex/08-tests-and-quality-gates`
10. `codex/09-final-integration-release`

如果有冲突，让最后的整合窗口处理，不要让非程序员用户手工解决冲突。

---

## 4. 全局提示词：每个 Codex 窗口都先粘贴这一段

```text
你现在接管的是 GitHub 仓库 gaoboguang/Academic-Affairs-System。

用户本人不懂编程，因此你必须作为自主开发 agent 工作：读取仓库、判断技术栈、修改代码、运行测试、用中文汇报，不要把技术决策抛给用户。

本项目不是初始项目。请先阅读 README.md、AGENTS.md、docs/local_edu_tool_dev_spec.md、memory-bank/active-context.md、memory-bank/handoff.md、package.json，再开始当前窗口任务。

当前真实项目基线：
- 项目是面向高中场景的本地单机教务决策台 / 本地教务工具。
- 后端：FastAPI + SQLAlchemy + SQLite + Alembic。
- 前端：Vue 3 + TypeScript + Vite + Element Plus。
- 桌面端：Electron。
- 主数据库：data/app.db。
- 当前开发主阵地：Mac。
- 常用命令：npm run dev、npm run check、npm run check:all、npm run backend:test、npm run frontend:build、npm run backend:data-health、npm run backend:p0-check。

重要约束：
1. 禁止重建项目、替换框架、删除已有模块。
2. 禁止无备份地覆盖 data/app.db、data/local_edu_tool/local_edu.sqlite3、data/backups/、handoffs/。
3. AGENTS.md 由 rulesync.jsonc 和 .rulesync/ 来源维护，不要随意手工改 AGENTS.md。
4. 每次修改必须尽量运行对应测试；无法运行时说明原因。
5. 最终报告必须用中文，包含修改内容、运行命令、测试结果、风险和下一步。

如果遇到业务规则不明确，请优先按高中本地教务系统的常规逻辑实现；只有涉及产品方向、数据删除、用户必须选择的业务规则时，才向用户提问。
```

---

## 5. 窗口 0：仓库审计与当前状态锁定

### 5.1 目标

把当前仓库真实状态锁定下来，避免后续窗口凭空开发。

### 5.2 重点目录

允许读取全仓库。重点读取：

```text
README.md
AGENTS.md
rulesync.jsonc
.rulesync/
docs/
memory-bank/
handoffs/
package.json
scripts/
tests/
apps/backend/
apps/frontend/
apps/desktop/
```

### 5.3 不要做什么

- 不要大改业务代码。
- 不要新增大功能。
- 不要直接重写 `AGENTS.md`。
- 不要删除任何数据文件。

### 5.4 提示词

```text
请执行“窗口 0：仓库审计与当前状态锁定”。

你需要完整读取当前仓库，基于真实代码和真实文档生成后续开发基线。不要只看 README，要继续检查 apps/backend、apps/frontend、apps/desktop、scripts、tests、docs、memory-bank、handoffs。

请完成以下工作：

1. 生成或更新 docs/repo-audit-2026-04-24.md
   内容必须包括：
   - 当前技术栈
   - 当前目录结构
   - 后端模块结构
   - 前端页面结构
   - 桌面端结构
   - 数据库 / Alembic / seed / migration 结构
   - 已完成模块
   - 半完成模块
   - 明显风险点
   - 当前最应该继续开发的 5 个方向

2. 生成或更新 docs/current-development-map-2026-04-24.md
   内容必须包括：
   - 学生、教师、班级、课程、任教关系现状
   - 考试、成绩、分析、报表现状
   - 课表、工作量现状
   - 成长档案、评教、量化现状
   - 推荐中心、高考志愿、数据健康现状
   - Mac 启动、测试、打包现状

3. 检查 AGENTS.md 的来源维护方式
   - 如果 AGENTS.md 是生成物，请不要直接改它。
   - 记录应修改 rulesync.jsonc 还是 .rulesync/ 中的哪个来源文件。
   - 如果不需要改规则，只在文档里记录即可。

4. 运行基础检查
   优先尝试：
   - npm run backend:test
   - npm run frontend:lint
   - npm run frontend:test
   - npm run frontend:build
   - npm run backend:data-health
   - npm run backend:p0-check

   如果因为环境、依赖、数据库、端口或权限导致失败，请不要停止，请记录失败原因和下一步建议。

5. 最终用中文汇报：
   - 当前项目到底处于什么阶段
   - 哪些模块已经完成，不要重复开发
   - 哪些模块适合后续并行开发
   - 后续窗口应该优先做什么
   - 是否可以合并本窗口产出

验收标准：
- 文档必须基于真实文件，而不是猜测。
- 不得破坏现有代码。
- 至少完成两个 docs 文档。
- 必须列出实际运行过的命令和结果。
```

---

## 6. 窗口 1：Mac 环境、启动体验与桌面启动收口

### 6.1 目标

让非程序员用户在 Mac 上更稳定地启动、检查和使用项目。

### 6.2 重点目录

```text
README.md
docs/
scripts/
start-local-edu.command
package.json
apps/desktop/
apps/backend/
apps/frontend/
```

### 6.3 不要做什么

- 不要改业务功能。
- 不要改数据库业务表。
- 不要把 Windows 作为主线；Windows 说明可保留但不要优先。

### 6.4 提示词

```text
请执行“窗口 1：Mac 环境、启动体验与桌面启动收口”。

目标：让不懂编程的用户在 Mac 上可以更可靠地启动、检查、验证、打包本项目。当前开发主阵地已经转为 Mac，不再以 Windows 为主。

请先读取：
- README.md
- package.json
- scripts/README.md
- start-local-edu.command
- scripts/dev.sh
- scripts/dev-local.cjs
- scripts/backend-cli.cjs
- apps/desktop/
- docs/ 中与运行、交付、P0、桌面端有关的文档

请完成：

1. 检查 Mac 启动流程
   - npm run dev 是否能在 Mac 上作为主入口。
   - start-local-edu.command 是否适合非程序员双击启动。
   - scripts/dev.sh 是否仍然有效。
   - 端口 5173 / 8000 预检是否清晰。
   - 后端虚拟环境、前端依赖、数据库迁移、模板初始化流程是否清晰。

2. 修复明显问题
   - 如果启动脚本报错信息不清楚，请优化错误提示。
   - 如果 Mac 权限、可执行位、路径、空格路径、python3/node 检测有问题，请修复。
   - 如果 README 与实际脚本不一致，请更新文档。

3. 生成或更新 docs/mac-user-startup-guide.md
   面向不懂编程的用户，写清楚：
   - 第一次在 Mac 上怎么准备
   - 怎么双击启动
   - 怎么用命令启动
   - 启动失败怎么看提示
   - 如何查看前端、后端、API 文档
   - 如何关闭服务
   - 如何运行最小检查

4. 生成或更新 docs/mac-developer-checklist.md
   面向 Codex / 开发 agent，写清楚：
   - 每次开发前检查什么
   - 每次开发后运行什么命令
   - 数据库改动前如何备份
   - 桌面打包前如何验证

5. 验证命令
   至少尝试：
   - npm run backend:test
   - npm run frontend:build
   - npm run backend:data-health
   如果环境允许，再尝试 npm run check。

最终中文汇报：
- Mac 启动入口是否可靠
- 具体改了哪些脚本或文档
- 用户以后应该点哪个文件或运行哪个命令
- 哪些检查通过，哪些没通过

验收标准：
- 非程序员用户可以按 docs/mac-user-startup-guide.md 操作。
- 不改变业务功能。
- 不破坏 Windows 兼容脚本，但不再以 Windows 为主线。
```

---

## 7. 窗口 2：统一导入中心与导入体验治理

### 7.1 目标

把已有导入能力进一步统一，减少学生、教师、成绩、课表、招生计划、高考数据等导入体验不一致的问题。

### 7.2 重点目录

```text
apps/backend/app/
apps/backend/tests/
apps/frontend/src/
apps/frontend/tests/
data/templates/
data/uploads/
data/exports/
docs/
```

### 7.3 不要做什么

- 不要重写已有学生/教师/成绩/课表导入器。
- 不要删除已有模板。
- 不要直接覆盖导入批次历史。
- 不要让导入失败后留下半成功脏数据。

### 7.4 提示词

```text
请执行“窗口 2：统一导入中心与导入体验治理”。

目标：在不推翻已有导入功能的前提下，统一学生、教师、成绩、课表、招生计划、高考数据等导入体验，包括模板下载、字段校验、错误报告、导入批次、审计日志、回滚/撤销提示。

请先读取：
- README.md 中已完成导入相关模块
- apps/backend/app 中与 import、template、upload、batch、student、teacher、exam、score、timetable、enrollment、gaokao 相关代码
- apps/frontend/src 中与导入页面、模板下载、错误报告、批次列表有关的代码
- apps/backend/tests 中已有导入测试
- tests/e2e 中已有跨端流程

请完成：

1. 盘点现有导入能力
   写入 docs/import-system-audit-2026-04-24.md：
   - 每类导入入口
   - 后端接口
   - 前端页面
   - 模板位置
   - 错误报告机制
   - 导入批次记录机制
   - 是否支持回滚或撤销
   - 目前体验不一致之处

2. 统一导入约定
   在不大拆架构的情况下补齐：
   - 统一导入状态：pending / running / success / failed / partially_failed / rolled_back
   - 统一错误结构：行号、列名、字段名、原始值、错误原因、建议修复
   - 统一批次摘要：总行数、成功数、失败数、跳过数、创建数、更新数
   - 统一模板下载说明
   - 统一前端错误展示方式

3. 优先处理四类核心导入
   - 学生信息导入
   - 考试 / 考试科目创建导入
   - 成绩导入
   - 课表导入

   如果这些功能已有实现，不要重写；请补齐一致性、错误提示、测试和文档。

4. 后端要求
   - 所有导入必须有事务边界。
   - 导入失败不得静默成功。
   - 不得仅靠前端校验，后端必须完整校验。
   - 不得使用姓名作为唯一身份键。
   - 学生优先使用学号 / 学籍号；教师优先使用工号；课程、班级、考试必须使用稳定标识或明确匹配规则。

5. 前端要求
   - 提供清晰的模板下载、上传、预检、结果查看、错误下载入口。
   - 错误信息必须让非程序员看得懂。
   - 导入完成后能跳转到对应业务页面或批次详情。

6. 测试要求
   至少新增或补齐：
   - 一个成功导入测试
   - 一个字段缺失测试
   - 一个重复数据测试
   - 一个冲突数据测试
   - 一个错误报告测试

7. 运行检查
   优先运行：
   - npm run backend:test
   - npm run frontend:test
   - npm run frontend:build

最终中文汇报：
- 当前有哪些导入入口
- 本次统一了哪些体验
- 改了哪些接口/页面/测试
- 哪些导入还需要下一轮继续治理

验收标准：
- 不破坏已有导入能力。
- 四类核心导入至少完成审计和明显一致性修复。
- 后端测试覆盖导入关键错误场景。
- 前端构建通过或明确说明未通过原因。
```

---

## 8. 窗口 3：高考数据健康、P0 交付与山东覆盖矩阵

### 8.1 目标

继续强化 P0 数据健康检查、山东覆盖矩阵、特殊类型规则、审计摘要，让交付前可用性更清楚。

### 8.2 重点目录

```text
apps/backend/app/
apps/backend/tests/
apps/frontend/src/components/
apps/frontend/src/views/
docs/p0_delivery_runbook_2026-04-24.md
gaokao_dev_bundle_v3/
data/
```

### 8.3 不要做什么

- 不要直接删除或覆盖 `data/app.db`。
- 不要把特殊类型数据和普通类数据混成一类。
- 不要隐藏 fallback、规则缺失、样本偏旧等风险。

### 8.4 提示词

```text
请执行“窗口 3：高考数据健康、P0 交付与山东覆盖矩阵”。

目标：继续强化已有的 npm run backend:data-health、npm run backend:p0-check 和 /gaokao-data 山东覆盖页签，让 P0 交付前的数据缺口、规则缺口、特殊类型风险和审计摘要更清晰。

请先读取：
- README.md 当前主线中与 /gaokao-data、backend:data-health、backend:p0-check、山东覆盖、特殊类型规则有关的段落
- docs/p0_delivery_runbook_2026-04-24.md
- gaokao_dev_bundle_v3/gaokao_dev_doc_v3.md
- apps/backend/app 中 gaokao、data-health、bootstrap-special-types、materialize-gaokao、merge-handoff 相关代码
- apps/frontend/src 中 /gaokao-data 页面和相关组件
- apps/backend/tests 中数据健康相关测试

请完成：

1. 审计 data-health 输出
   - 检查 JSON 是否包含核心表数量、山东年份覆盖、考生类型覆盖、批次覆盖、特殊类型缺口、疑似重复、冲突、待人工复核、audit_summary。
   - 如果缺少字段，请补齐。
   - 如果字段名称不清楚，请补充面向非技术用户的 label / explanation。

2. 强化山东覆盖矩阵
   - 前端 /gaokao-data 的“山东覆盖”页签应能让非程序员看出：
     - 哪些年份有数据
     - 哪些考生类型有数据
     - 哪些批次有数据
     - 哪些是完整数据
     - 哪些只能初筛
     - 哪些存在规则缺失或 fallback
   - 后端接口要提供足够结构化的数据，不要只返回一段字符串。

3. 强化特殊类型风险表达
   必须区分：
   - 普通类
   - 春季高考
   - 艺术类
   - 体育类
   - 单独招生
   - 综合评价招生

   对缺少专门录取结果而参考普通类结果的场景，必须明确标风险，不得伪装成完整匹配。

4. 强化 P0 runbook
   更新 docs/p0_delivery_runbook_2026-04-24.md 或新增 docs/p0-data-health-checklist.md：
   - P0 交付前运行哪些命令
   - 什么结果算通过
   - 什么结果算警告
   - 什么结果必须阻断交付
   - 非程序员用户应该怎么看结果

5. 测试
   至少运行：
   - npm run backend:data-health
   - npm run backend:data-health -- --json
   - npm run backend:p0-check
   - npm run backend:test
   如果改了前端，再运行：
   - npm run frontend:test
   - npm run frontend:build

最终中文汇报：
- P0 健康检查目前能检查什么
- 山东覆盖矩阵新增或修复了什么
- 哪些数据仍然不足
- 哪些风险已经在页面和 JSON 中显式表达

验收标准：
- data-health JSON 对机器和人都可读。
- /gaokao-data 页面不隐藏特殊类型风险。
- P0 runbook 可被非程序员照着执行。
```

---

## 9. 窗口 4：高考志愿 / 推荐中心 Stage B 继续细化

### 9.1 目标

在现有推荐中心和高考志愿工作台基础上，继续完善规则解释、跨年份样本风险、特殊类型推荐边界、职业意向解释。

### 9.2 重点目录

```text
apps/backend/app/services/
apps/backend/app/routers/
apps/backend/tests/
apps/frontend/src/components/recommendations/
apps/frontend/src/views/
tests/e2e/
gaokao_dev_bundle_v3/
```

### 9.3 不要做什么

- 不要推翻已有推荐算法。
- 不要把 fallback 结果展示成精准结果。
- 不要让普通类、春考、艺体、综评、单招混用。
- 不要破坏旧推荐中心的策略模板、历史回放、导出。

### 9.4 提示词

```text
请执行“窗口 4：高考志愿 / 推荐中心 Stage B 继续细化”。

目标：基于现有 /recommendations 高考志愿工作台、推荐中心、规则库和职业匹配能力，继续完善规则解释、跨年份样本风险、特殊类型推荐边界、职业意向解释。

请先读取：
- README.md 当前主线中与推荐中心、高考志愿、Stage B、山东规则、特殊类型、职业方向、志愿草稿有关的内容
- gaokao_dev_bundle_v3/gaokao_dev_doc_v3.md
- apps/backend/app/services 中 recommendations、volunteer、gaokao、rule、employment 相关文件
- apps/frontend/src/components/recommendations/
- tests/e2e/dashboard-smoke.spec.ts 中推荐 / 高考志愿相关流程

请完成：

1. 审计当前推荐解释链
   写入 docs/recommendation-stage-b-audit-2026-04-24.md：
   - 候选池如何生成
   - 冲稳保如何分组
   - 省份规则如何命中
   - 缺少年份规则如何表达
   - 样本年份偏旧如何表达
   - 特殊类型如何 fallback
   - 页面、打印、导出、Excel 是否一致

2. 继续细化解释一致性
   检查并修复以下场景：
   - 工作台预览
   - 志愿草稿详情
   - 草稿打印页
   - 推荐结果页
   - 推荐打印页
   - 报表中心导出前摘要
   - Excel 风险概览 / 边界概览

   同一风险在不同输出链路中表达要一致。

3. 强化跨年份样本提示
   当目标年份与最近录取样本年份差距较大时：
   - 后端结果必须带结构化风险字段。
   - 前端必须显示“参考年份偏旧 / 排序和解释偏保守”。
   - 打印和导出不能丢失这类提示。

4. 强化特殊类型边界
   对以下类型分别处理：
   - spring_exam
   - art
   - sports
   - independent_recruitment
   - comprehensive_evaluation

   如果缺少专门录取结果，只能显式标注参考口径，不得混为普通类精准推荐。

5. 职业意向解释
   检查职业方向、专业就业映射、学生职业意向输入、职业匹配解释是否形成闭环。
   如果解释过短或过技术化，请补充非程序员可读的说明。

6. 测试
   优先运行：
   - npm run backend:test
   - npm run frontend:test
   - npm run frontend:build
   - npm run check:e2e

最终中文汇报：
- 本次强化了哪些推荐解释
- 哪些输出链路已对齐
- 哪些风险字段新增或修复
- 哪些省份/年份/类别仍需后续补数据

验收标准：
- 不破坏已有推荐结果生成。
- 风险解释不能只在页面有，导出/打印也要保留。
- 特殊类型必须显式标风险或口径。
```

---

## 10. 窗口 5：核心教务链路回归与小修复

### 10.1 目标

保护基础教务功能，不让高考志愿和复杂模块把核心教务链路拖坏。

### 10.2 重点目录

```text
apps/backend/app/
apps/backend/tests/
apps/frontend/src/
apps/frontend/tests/
tests/e2e/
```

### 10.3 不要做什么

- 不要新增大型模块。
- 不要重写学生、教师、考试、成绩、课表页面。
- 不要改变已有 API 合约，除非测试和前端同步更新。

### 10.4 提示词

```text
请执行“窗口 5：核心教务链路回归与小修复”。

目标：系统性检查并修复基础教务闭环，确保学生、教师、班级、任教、考试、成绩、分析、课表、工作量、报表这些核心链路稳定可用。

请先读取：
- README.md 已完成模块列表
- apps/backend/app 中 student、teacher、class、course、teaching、exam、score、analytics、timetable、workload、report 相关代码
- apps/frontend/src 中对应页面和 API 调用
- apps/backend/tests、apps/frontend/tests、tests/e2e

请完成：

1. 梳理核心链路
   写入 docs/core-academic-flow-audit-2026-04-24.md：
   - 学生信息链路
   - 教师信息链路
   - 班级 / 课程 / 任教关系链路
   - 考试创建链路
   - 成绩导入与成绩快照链路
   - 分析中心链路
   - 课表导入、未匹配修正、工作量计算链路
   - 报表导出链路

2. 运行或补齐关键测试
   优先检查：
   - 学生新增/编辑/导入
   - 教师新增/编辑/导入
   - 考试创建与科目配置
   - 成绩导入与错误报告
   - 班级/年级/学科分析
   - 课表导入与工作量计算
   - 报表导出

3. 做小修复
   如果发现：
   - 空态显示不清楚
   - 错误提示过技术化
   - 页面按钮无效
   - API 参数不一致
   - 排序/筛选/分页明显异常
   - 导出文件名或字段不清楚

   请直接修复。

4. 不做大改
   如果发现需要重构的大问题，请记录到文档，不要在本窗口大面积重构。

5. 运行检查
   - npm run backend:test
   - npm run frontend:test
   - npm run frontend:build
   - npm run check:e2e 或至少运行相关 e2e

最终中文汇报：
- 核心教务链路是否稳定
- 修复了哪些小问题
- 哪些问题需要单独开窗口继续处理
- 哪些测试通过/失败

验收标准：
- 基础教务功能不能因为本次修改变差。
- 发现大问题要记录清楚。
- 小问题能修就修。
```

---

## 11. 窗口 6：报表、打印、Excel 导出一致性

### 11.1 目标

继续统一页面摘要、打印页、报表中心、Excel 导出的字段和风险提示。

### 11.2 重点目录

```text
apps/backend/app/services/
apps/backend/app/routers/
apps/frontend/src/components/
apps/frontend/src/views/
apps/backend/tests/
apps/frontend/tests/
```

### 11.3 不要做什么

- 不要只改页面不改导出。
- 不要只改 Excel 不改打印。
- 不要隐藏风险摘要。

### 11.4 提示词

```text
请执行“窗口 6：报表、打印、Excel 导出一致性”。

目标：检查并继续统一本地教务工具中的报表、打印、Excel 导出，尤其是学生分析、班级分析、年级汇总、教师分析、工作量、成长档案、推荐报告、评教汇总、班主任量化、高考志愿草稿和推荐摘要。

请先读取：
- README.md 中报表、打印、Excel、推荐解释统一相关内容
- apps/backend/app 中 report、export、analytics、recommendation、volunteer、workload、evaluation 相关服务
- apps/frontend/src 中报表中心、打印页、推荐打印页、志愿草稿打印页相关组件
- 现有测试

请完成：

1. 审计输出链路
   写入 docs/report-export-print-audit-2026-04-24.md：
   - 每类报表入口
   - 对应后端接口
   - 是否支持打印
   - 是否支持 Excel
   - 是否有导出前摘要
   - 风险提示是否一致
   - 字段顺序是否一致

2. 修复不一致
   优先修复：
   - 页面有的摘要，Excel 没有
   - 打印页有的风险，报表中心没有
   - Excel 字段名不清楚
   - 文件名不包含关键上下文
   - 空态导出没有说明

3. 统一非技术表达
   导出和打印面向学校老师使用，避免技术字段裸露。
   例如：
   - 不要只显示 missing_rule_year，应显示“缺少年份规则”。
   - 不要只显示 stale_sample，应显示“参考年份偏旧，排序和解释偏保守”。

4. 测试
   - npm run backend:test
   - npm run frontend:test
   - npm run frontend:build
   如果已有 e2e 覆盖报表中心，请运行相关 e2e。

最终中文汇报：
- 本次检查了哪些报表
- 统一了哪些字段和风险提示
- 哪些导出仍需要后续增强
- 测试结果

验收标准：
- 页面、打印、Excel 对关键风险表达一致。
- 面向非技术用户可读。
- 不破坏已有报表导出。
```

---

## 12. 窗口 7：前端体验、导航与非程序员可读性

### 12.1 目标

让整个系统更像给学校老师用的本地工具，而不是给程序员用的调试界面。

### 12.2 重点目录

```text
apps/frontend/src/
apps/frontend/tests/
tests/e2e/
```

### 12.3 不要做什么

- 不要重写前端框架。
- 不要大改业务逻辑。
- 不要删除已有入口。

### 12.4 提示词

```text
请执行“窗口 7：前端体验、导航与非程序员可读性”。

目标：在不重写业务逻辑的情况下，改善 Vue 前端的导航、空态、错误提示、按钮文案、页面说明，让不懂技术的学校老师也能理解当前页面在做什么。

请先读取：
- apps/frontend/src 的路由、布局、导航、主要页面
- components/recommendations、workload、evaluation 等已抽出的组合逻辑
- tests/e2e/dashboard-smoke.spec.ts
- README.md 中已有页面入口说明

请完成：

1. 审计导航结构
   写入 docs/frontend-navigation-audit-2026-04-24.md：
   - 当前主导航有哪些入口
   - 哪些入口命名不清楚
   - 哪些页面缺少说明
   - 哪些复杂页面需要增加“这是什么 / 怎么用 / 风险说明”

2. 优化空态和错误提示
   优先处理：
   - 高考志愿 / 推荐中心
   - 高考数据驾驶舱
   - 导入页面
   - 报表中心
   - 课表工作量
   - 评教量化

3. 优化操作反馈
   - 上传中、导入中、生成中、导出中要有明确状态。
   - 失败时说明用户下一步该做什么。
   - 成功后提供跳转或查看结果入口。

4. 保持组件拆分
   README 显示多个复杂页面已经拆 helper / composition，不要把逻辑重新塞回大页面。

5. 测试
   - npm run frontend:lint
   - npm run frontend:test
   - npm run frontend:build
   - 如修改关键流程，运行相关 e2e

最终中文汇报：
- 哪些页面体验变清楚了
- 哪些文案改成了非技术表达
- 哪些页面仍建议后续设计优化
- 测试结果

验收标准：
- 不改变核心业务逻辑。
- 页面文案和错误提示更适合非程序员。
- 前端构建通过。
```

---

## 13. 窗口 8：测试体系、质量门禁与回归脚本

### 13.1 目标

把后续每次开发的检查流程收口，让 Codex 多窗口开发后能可靠验收。

### 13.2 重点目录

```text
package.json
scripts/
tests/
apps/backend/tests/
apps/frontend/tests/
docs/
```

### 13.3 不要做什么

- 不要为了通过测试而删除重要测试。
- 不要跳过失败用例。
- 不要降低质量门禁。

### 13.4 提示词

```text
请执行“窗口 8：测试体系、质量门禁与回归脚本”。

目标：检查并完善项目测试体系、质量门禁和 Codex 开发后的回归流程，让后续每个窗口都知道该运行什么命令、失败如何处理。

请先读取：
- package.json
- scripts/README.md
- tests/README.md
- apps/backend/tests
- apps/frontend/tests
- tests/e2e/dashboard-smoke.spec.ts
- docs/p0_delivery_runbook_2026-04-24.md

请完成：

1. 审计测试体系
   写入 docs/test-quality-audit-2026-04-24.md：
   - 后端测试覆盖哪些模块
   - 前端单测覆盖哪些模块
   - E2E 覆盖哪些流程
   - check / check:e2e / check:all 分别做什么
   - 哪些关键模块测试不足

2. 建立 Codex 任务验收规则
   生成 docs/codex-task-acceptance-checklist.md：
   - 改后端必须跑什么
   - 改前端必须跑什么
   - 改数据库必须跑什么
   - 改高考数据必须跑什么
   - 改报表导出必须跑什么
   - 改桌面端必须跑什么

3. 改善脚本输出
   如果当前脚本错误提示不适合非程序员，请优化说明。
   例如：
   - 缺 Node 版本
   - 缺 Python
   - 没装依赖
   - 数据库不存在
   - 端口被占用
   - Playwright 浏览器未安装

4. 补测试
   针对窗口 0 审计或当前运行发现的明显缺口，补最有价值的测试。
   优先补：
   - 数据健康
   - 导入错误报告
   - 推荐风险解释
   - 报表导出摘要
   - 核心教务链路

5. 运行检查
   尽量运行：
   - npm run check
   - npm run check:e2e
   - npm run check:all

最终中文汇报：
- 当前质量门禁是否可靠
- 新增/修复了哪些测试
- 哪些测试仍不足
- 后续 Codex 每个窗口应该怎么验收

验收标准：
- 不删除关键测试。
- 给出明确的验收清单。
- 能让非程序员知道“通过/不通过”意味着什么。
```

---

## 14. 窗口 9：最终整合、冲突处理、发布前验收

### 14.1 目标

整合前面窗口的修改，处理冲突，运行完整检查，给用户一份可理解的发布前结论。

### 14.2 重点目录

全仓库。

### 14.3 不要做什么

- 不要新增大功能。
- 不要在最终整合阶段引入架构性重构。
- 不要跳过测试失败。

### 14.4 提示词

```text
请执行“窗口 9：最终整合、冲突处理、发布前验收”。

目标：整合前面 Codex 窗口的开发成果，处理冲突，运行完整检查，生成面向非程序员用户的最终验收报告。

请先读取：
- README.md
- docs/repo-audit-2026-04-24.md
- docs/current-development-map-2026-04-24.md
- docs/mac-user-startup-guide.md
- docs/import-system-audit-2026-04-24.md
- docs/p0_delivery_runbook_2026-04-24.md
- docs/codex-task-acceptance-checklist.md
- 各窗口新增的审计和验收文档

请完成：

1. 整合代码
   - 检查各窗口是否修改了同一文件。
   - 处理冲突。
   - 保留更完整、更安全、更符合现有架构的实现。

2. 全量检查
   尽量运行：
   - npm run backend:test
   - npm run frontend:lint
   - npm run frontend:test
   - npm run frontend:build
   - npm run backend:data-health
   - npm run backend:p0-check
   - npm run check
   - npm run check:e2e
   - npm run check:all
   - 如桌面端相关有修改，再运行 npm run desktop:prepare 或 npm run desktop:dist:mac

3. 生成最终验收文档
   生成 docs/final-acceptance-report-2026-04-24.md：
   - 本轮开发合并了哪些窗口
   - 新增了哪些能力
   - 修复了哪些问题
   - 哪些命令通过
   - 哪些命令失败，失败原因是什么
   - 当前是否建议给用户试用
   - 用户在 Mac 上应该怎么启动
   - 下一轮最建议开发什么

4. 更新 README 或 docs/README.md
   只在必要时更新，不要塞入过多细节。
   保持 README 是导航入口，详细内容放 docs。

5. 最终中文汇报
   用非程序员能理解的话说明：
   - 当前项目能不能启动
   - 能不能交付给学校试用
   - 还存在哪些风险
   - 用户下一步应该做什么

验收标准：
- 完整检查尽可能运行。
- 失败必须有解释。
- 最终文档清楚。
- 不引入新大功能。
```

---

## 15. 用户遇到 Codex 提问时的固定回复

用户不懂编程，因此如果 Codex 问技术实现问题，可以直接复制下面回复。

### 15.1 Codex 问“用什么技术方案？”

```text
我不懂编程，请你按当前仓库已有技术栈和最佳实践自行判断。不要更换框架，不要重建项目。请优先选择最小、安全、可测试、符合现有代码风格的实现。完成后用中文告诉我你选择了什么方案、为什么这样做、运行了哪些测试。
```

### 15.2 Codex 只写计划、不动代码

```text
请不要只写方案。这个任务需要你直接读取仓库并修改代码。请按当前仓库结构实际实现，运行能运行的测试，最后用中文汇报修改内容、测试结果和风险。
```

### 15.3 Codex 让用户手动解决报错

```text
我不懂编程。请你先自行分析报错并尝试修复。如果确实无法修复，请用中文说明：报错原因、你已经尝试了什么、为什么需要我介入、我需要做的具体操作。不要只把英文报错贴给我。
```

### 15.4 Codex 要删除或覆盖数据库

```text
不要直接删除或覆盖数据库。请先备份，并说明为什么必须改数据库。优先通过 Alembic migration、初始化脚本、数据修复脚本来处理，不要手工覆盖 data/app.db。完成后运行 data-health 和 p0-check。
```

### 15.5 Codex 问是否可以改 AGENTS.md

```text
README 里说明 AGENTS.md 可能由 rulesync.jsonc 和 .rulesync/ 来源维护，不建议手工改生成结果。请先确认 AGENTS.md 的维护来源。如果需要改规则，请修改正确的来源文件，并说明理由。不要随意直接改 AGENTS.md。
```

### 15.6 Codex 问是否继续支持 Windows

```text
当前主开发阵地是 Mac。Windows 兼容可以保留，但不要作为主线，不要为了 Windows 牺牲 Mac 启动、Mac 打包和 Mac 用户体验。
```

---

## 16. 后续开发优先级

### P0：必须先稳住

1. Mac 启动、测试、打包入口。
2. 数据库备份与数据健康检查。
3. 核心教务链路稳定性。
4. 导入失败不可造成脏数据。
5. 高考志愿风险解释不能误导用户。

### P1：继续增强

1. 统一导入中心。
2. 山东覆盖矩阵和 P0 数据健康看板。
3. 高考志愿 Stage B 解释细化。
4. 报表、打印、Excel 一致性。
5. 非程序员可读的页面文案和错误提示。

### P2：体验优化

1. 桌面端首次启动引导。
2. 一键检查 / 一键备份 / 一键恢复流程。
3. 更多 E2E 测试。
4. 更多省份 / 年份 / 批次规则补齐。
5. 更完整的用户手册。

---

## 17. 不允许破坏的现有成果

后续任何窗口都不得破坏：

- `npm run dev`
- `npm run backend:test`
- `npm run frontend:build`
- `npm run backend:data-health`
- `npm run backend:p0-check`
- 学生、教师、考试、成绩、课表、工作量基础功能
- 推荐中心历史方案、策略模板、报告导出
- 高考志愿工作台、志愿草稿、打印/导出
- 高考数据驾驶舱
- 报表中心
- 备份恢复
- Electron 桌面端基础启动能力
- `data/backups/` 安全约定
- `handoffs/` 接管资料
- `memory-bank/` 项目记忆资料

---

## 18. 每个窗口的最终汇报模板

Codex 完成任务后必须按这个模板汇报：

```text
本窗口任务：

一、完成内容
1. ...
2. ...
3. ...

二、修改文件
- ...

三、新增文件
- ...

四、删除文件
- 无 / ...

五、运行命令与结果
- npm run xxx：通过 / 失败
- npm run xxx：通过 / 失败

六、失败或未完成内容
- ...

七、风险说明
- ...

八、建议下一步
- ...

九、是否建议合并
- 建议 / 暂不建议，原因：...
```

---

## 19. 给 Codex 的最后提醒

这个项目已经有大量功能。后续开发的关键不是“炫技”，而是：

- 稳定。
- 可运行。
- 数据安全。
- 风险解释清楚。
- 非程序员能使用。
- Mac 上能顺利启动。
- 每次修改都有测试或明确验证。

你应当像维护一个已经接近交付的本地教务产品一样工作，而不是像搭建一个新 Demo。
