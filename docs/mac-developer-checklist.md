# Mac 开发检查清单

- 文档日期：2026-04-24
- 适用对象：Codex 窗口和本机开发者
- 范围：Mac 启动、验证、备份、打包前检查

## 开发前

先确认当前任务边界：

```bash
git status --short --branch
```

如果是接手既有项目，先读：

- `AGENTS.md`
- `docs/repo-audit.md`
- `docs/development-roadmap.md`
- `memory-bank/active-context.md`
- `memory-bank/handoff.md`

确认基础工具：

```bash
node -v
npm -v
python3 --version
```

确认后端虚拟环境：

```bash
test -x .venv/bin/python
```

如果缺少 `.venv`：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e './apps/backend[dev]'
```

## 启动前

优先使用统一入口：

```bash
npm run dev
```

需要排查启动器时：

```bash
node scripts/dev-local.cjs --help
```

确认端口：

```bash
curl -I -s http://127.0.0.1:5173
curl -s http://127.0.0.1:8000/api/system/health
```

如果端口已是本项目服务，`npm run dev` 会复用；如果端口被其它程序占用，应先关闭占用进程，不要强行改业务端口。

## 改动后

按改动面选择最小验证。窗口 1 这类启动和文档收口至少跑：

```bash
node scripts/dev-local.cjs --help
node scripts/backend-cli.cjs --help
npm run backend:data-health -- --json
npm run frontend:build
```

涉及后端或交付检查时再跑：

```bash
npm run backend:test
npm run backend:p0-check -- --json
```

涉及前端逻辑时再跑：

```bash
npm run frontend:lint
npm run frontend:test
```

交付前完整检查：

```bash
npm run check
npm run check:e2e
```

最后检查补丁格式：

```bash
git diff --check
```

## 改数据库前

这些命令会修改 `data/app.db`：

```bash
npm run backend:merge-handoff
npm run backend:materialize-gaokao
npm run backend:bootstrap-special-types -- --year 2025 --year 2026
```

执行前先做：

```bash
npm run backend:data-health -- --json
npm run backend:p0-check -- --json
```

执行后再跑一次：

```bash
npm run backend:data-health -- --json
```

如果健康摘要没有输出，先停止补库，不要继续叠加写库操作。

## 桌面打包前

先确认前后端基础验证通过：

```bash
npm run backend:test
npm run frontend:build
```

安装桌面后端依赖：

```bash
source .venv/bin/activate
pip install -e './apps/backend[desktop]'
```

准备桌面资源：

```bash
npm run desktop:prepare
```

macOS 目录产物：

```bash
npm run desktop:dist:mac
```

Windows 包能力保留，但当前主线不优先验证 Windows；最终交付窗口再单独跑 Windows 产物。

## 交接前

如果本轮改变了启动、验证、文档或接手流程，更新：

- `memory-bank/active-context.md`
- `memory-bank/progress.md`
- `memory-bank/handoff.md`

中文汇报中说明：

1. 改了哪些文件。
2. 修复或新增了什么。
3. 为什么这样做。
4. 运行了哪些验证。
5. 剩余风险或下一步。
