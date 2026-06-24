# GitHub Project Introduction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the GitHub repository's developer-log-style landing content with an accurate, balanced introduction for school users and developers.

**Architecture:** Keep the public introduction in two synchronized surfaces: a short GitHub About description and a concise root README. Preserve detailed progress in `memory-bank/` and specialist docs instead of duplicating it in README; no application code or runtime data changes are involved.

**Tech Stack:** Markdown, GitHub repository metadata through `gh`, Git, existing npm workspace commands.

---

## File Map

- Modify `README.md`: public project landing page and primary navigation.
- Modify `memory-bank/handoff.md`: record the final public description and where progress details now live.
- Modify `memory-bank/progress.md`: record completion of the GitHub introduction rewrite.
- Read `package.json`: source of truth for commands shown in README.
- Read `docs/local_edu_tool_dev_spec.md`: source of truth for product positioning and boundaries.
- Read `docs/server-deployment-and-roles.md`: source of truth for server deployment and account boundaries.
- Update GitHub repository metadata: set the About `description`; leave Homepage, visibility and topics unchanged.

### Task 1: Rewrite the Public README

**Files:**
- Modify: `README.md`
- Reference: `docs/superpowers/specs/2026-06-23-github-project-introduction-design.md`
- Reference: `package.json`

- [ ] **Step 1: Confirm the current command and documentation contracts**

Run:

```bash
node -e 'const p=require("./package.json"); console.log(Object.keys(p.scripts).sort().join("\n"))'
for f in docs/local_edu_tool_dev_spec.md docs/server-deployment-and-roles.md docs/mac-user-startup-guide.md docs/mac-dev-setup.md docs/codex-task-acceptance-checklist.md tests/README.md memory-bank/handoff.md; do test -f "$f" || exit 1; done
```

Expected: the command list includes `start:local`, `stop:local`, `dev`, `backend:migrate`, `backend:init-admin`, `check`, `check:e2e`, and `check:all`; every referenced document exists.

- [ ] **Step 2: Replace README with the approved public structure**

Use this content contract when rewriting `README.md`:

```markdown
# 本地教务工具

面向高中学校的本地优先教务决策台。它把学生、教师、考试、成绩、课表、工作量、成长档案和升学数据统一到一套可导入、可分析、可追溯、可导出的系统中。

系统可以在教师个人电脑上离线运行，也可以部署到学校自有服务器，通过管理员和教师账号受控使用。真实业务数据默认保存在本机或学校服务器，不依赖必须联网才能运行的云服务。

## 适合谁

- 希望减少学生、成绩、教师和课表 Excel 分散管理的教务人员。
- 需要查看班级、年级、教师和学生多视角分析的管理者与教师。
- 需要维护院校、专业、录取数据并形成志愿初筛与报告的升学指导教师。
- 希望继续扩展本地教务业务、数据模型和报表能力的开发者。

## 核心能力

### 学生与成绩

- 学生主档、班级历史、成长档案、附件和教师评语。
- 考试管理、Excel 成绩导入、成绩查询和分析快照。
- 学生、班级、年级和教师视角的趋势、结构与知识点分析。

### 教师与教学

- 教师档案、任教关系、班主任关系和职称历史。
- 课表导入、课时统计、工作量计算、评教与班主任量化。

### 高考志愿与院校数据

- 院校库、专业库、招生计划、历年录取与来源证据。
- 普通类、艺术类、体育类等路径的本地筛选和志愿草稿。
- 推荐历史、方案对比、打印预览和 Excel 报告。

### 系统与报表

- 统一报表中心、Excel 导入导出和本地打印预览。
- SQLite 数据库、本地附件目录、备份恢复和数据健康检查。
- 管理员 / 教师账号、班级访问范围、服务端会话和操作审计。

## 本地优先与数据安全

- 默认监听 `127.0.0.1`，单机使用不需要公网服务。
- 数据库、附件、导出和备份保存在本机或学校自有服务器。
- 仓库不包含真实学生、成绩、账号、附件或运行数据库。
- 学校服务器部署必须使用 HTTPS 反向代理；教师账号由管理员创建，不开放公众注册。

## 快速开始

### 本地使用

```bash
npm run start:local
```

停止后台服务：

```bash
npm run stop:local
```

开发模式：

```bash
npm run dev
```

默认地址为前端 `http://127.0.0.1:5173`、后端 `http://127.0.0.1:8000`、API 文档 `http://127.0.0.1:8000/docs`。

### 学校服务器

首次部署先执行迁移并创建管理员：

```bash
npm run backend:migrate
npm run backend:init-admin -- --username admin
```

完整说明见 [服务器部署与角色权限](./docs/server-deployment-and-roles.md)。

## 技术架构

| 层级 | 技术 |
| --- | --- |
| 前端 | Vue 3、TypeScript、Vite、Element Plus、Pinia、Vue Router、ECharts |
| 后端 | Python 3.11+、FastAPI、SQLAlchemy 2、Pydantic 2、Alembic |
| 数据 | SQLite、pandas、openpyxl |
| 测试 | pytest、Vitest、ESLint、Playwright |
| 桌面 | Electron、后端独立二进制打包链 |

## 项目结构

```text
apps/frontend/      Vue 前端
apps/backend/       FastAPI 后端
apps/desktop/       Electron 桌面壳
data/               本地数据库、附件、导出和备份（运行数据不提交 Git）
docs/               产品、开发、部署和验收文档
scripts/            本地启动、迁移和数据工具
tests/e2e/          跨端业务回归
memory-bank/        当前进展、决策与接手说明
```

## 开发与验证

```bash
npm run backend:test
npm run frontend:lint
npm run frontend:test
npm run frontend:build
npm run check:e2e
npm run check:all
```

## 文档导航

- [产品与开发规格](./docs/local_edu_tool_dev_spec.md)
- [服务器部署与角色权限](./docs/server-deployment-and-roles.md)
- [Mac 普通用户启动指南](./docs/mac-user-startup-guide.md)
- [Mac 开发环境说明](./docs/mac-dev-setup.md)
- [任务验收清单](./docs/codex-task-acceptance-checklist.md)
- [测试布局说明](./tests/README.md)
- [最新交接状态](./memory-bank/handoff.md)

## 使用边界

- 本项目是本地或学校自有服务器上的教务决策工具，不是开放注册的多租户 SaaS。
- 高考推荐用于本地数据整理、初筛和决策辅助，不替代省级志愿系统、官方政策或院校招生章程。
- 特殊类型缺少专门录取结果时只能提供初筛信息，不应解释为录取把握。
```

- [ ] **Step 3: Check README headings, links and commands**

Run:

```bash
rg -n '^#{1,3} ' README.md
for f in docs/local_edu_tool_dev_spec.md docs/server-deployment-and-roles.md docs/mac-user-startup-guide.md docs/mac-dev-setup.md docs/codex-task-acceptance-checklist.md tests/README.md memory-bank/handoff.md; do test -f "$f" || exit 1; done
for cmd in start:local stop:local dev backend:migrate backend:init-admin backend:test frontend:lint frontend:test frontend:build check:e2e check:all; do node -e 'const p=require("./package.json"); process.exit(p.scripts[process.argv[1]] ? 0 : 1)' "$cmd" || exit 1; done
```

Expected: headings match the approved order; all referenced files and npm scripts exist.

### Task 2: Update Project Memory

**Files:**
- Modify: `memory-bank/handoff.md`
- Modify: `memory-bank/progress.md`

- [ ] **Step 1: Add the public introduction handoff entry**

Add a compact 2026-06-24 entry near the top of `memory-bank/handoff.md` stating:

```markdown
## GitHub 项目介绍改版（2026-06-24）

- GitHub About 与 README 已改为“产品与技术并重”的公开项目介绍。
- README 只保留用途、能力、安全边界、启动、架构和文档入口；阶段流水账继续由 `memory-bank/` 和专项文档维护。
- 本轮未修改应用代码、数据库、迁移或运行数据。
```

- [ ] **Step 2: Record the completed documentation milestone**

Add this item under a new `## 2026-06-24 新增` section in `memory-bank/progress.md`:

```markdown
- 已重写 GitHub About 与 README 项目介绍，平衡学校使用者和开发者视角；移除 README 阶段流水账，保留产品定位、核心能力、数据安全、快速启动、技术架构、验证命令和文档入口。
```

- [ ] **Step 3: Verify memory files are concise and consistent**

Run:

```bash
rg -n 'GitHub 项目介绍改版|2026-06-24 新增' memory-bank/handoff.md memory-bank/progress.md
git diff --check -- README.md memory-bank/handoff.md memory-bank/progress.md
```

Expected: one current entry in each memory file and no whitespace errors.

### Task 3: Update GitHub About Metadata

**Files:**
- No repository file changes.
- External target: `gaoboguang/Academic-Affairs-System` repository description.

- [ ] **Step 1: Set the approved description**

Run:

```bash
gh repo edit gaoboguang/Academic-Affairs-System --description "本地优先的高中教务决策台，统一管理学生、教师、成绩、课表、工作量与升学推荐，支持 Excel 导入导出、SQLite 离线存储及学校服务器受控部署。"
```

Expected: command exits with status 0.

- [ ] **Step 2: Read the description back**

Run:

```bash
gh repo view gaoboguang/Academic-Affairs-System --json description --jq .description
```

Expected:

```text
本地优先的高中教务决策台，统一管理学生、教师、成绩、课表、工作量与升学推荐，支持 Excel 导入导出、SQLite 离线存储及学校服务器受控部署。
```

### Task 4: Verify, Commit and Publish

**Files:**
- Modify: `README.md`
- Modify: `memory-bank/handoff.md`
- Modify: `memory-bank/progress.md`

- [ ] **Step 1: Review the final documentation diff**

Run:

```bash
git diff -- README.md memory-bank/handoff.md memory-bank/progress.md
git diff --check
```

Expected: only the approved README rewrite and compact memory entries appear; no whitespace errors.

- [ ] **Step 2: Commit the documentation changes**

Run:

```bash
git add README.md memory-bank/handoff.md memory-bank/progress.md
git commit -m "docs: rewrite GitHub project introduction"
```

Expected: one documentation commit is created.

- [ ] **Step 3: Push the current branch**

Run:

```bash
git push origin codex/server-auth-rbac-20260601
```

Expected: the remote branch advances without force.

- [ ] **Step 4: Verify the remote branch and draft PR**

Run:

```bash
local_head=$(git rev-parse HEAD)
remote_head=$(git ls-remote origin refs/heads/codex/server-auth-rbac-20260601 | awk '{print $1}')
test "$local_head" = "$remote_head"
gh pr view 1 --json url,state,isDraft,headRefName --jq '{url,state,isDraft,headRefName}'
```

Expected: local and remote hashes match; PR #1 remains open and draft on `codex/server-auth-rbac-20260601`.
