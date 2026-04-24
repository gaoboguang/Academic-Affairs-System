# Mac 开发与启动说明

- 文档日期：2026-04-24
- 适用环境：macOS + zsh
- 默认地址：前端 `http://127.0.0.1:5173`，后端 `http://127.0.0.1:8000`

相关入口：

- 普通用户双击启动：[`mac-user-startup-guide.md`](./mac-user-startup-guide.md)
- Codex / 开发窗口检查：[`mac-developer-checklist.md`](./mac-developer-checklist.md)

## 1. 准备环境

需要本机具备：

- Node.js `20+`
- npm `10+`
- Python `3.11+`
- Git

如果使用 Homebrew，可以用下面方式准备：

```bash
brew install node python git
```

如果本机已经安装过这些工具，可以直接进入下一步。

## 2. 获取代码

```bash
git clone <仓库地址> local-edu-tool
cd local-edu-tool
```

当前 Codex 本机路径是：

```bash
/Users/gao/local-edu-tool
```

## 3. 安装前端依赖

```bash
npm install
```

根目录使用 npm workspace，前端依赖会安装到 `apps/frontend`，桌面壳依赖会安装到 `apps/desktop`。

## 4. 安装后端依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e './apps/backend[dev]'
```

如需桌面打包能力，再安装：

```bash
pip install -e './apps/backend[desktop]'
```

## 5. 配置环境变量

通常不需要手工配置，后端会默认读取：

- 主库：`data/app.db`
- 数据目录：`data/`
- 高考 fallback 库：`data/local_edu_tool/local_edu.sqlite3`

如果需要显式配置：

```bash
cp .env.example .env
```

`.env.example` 使用相对路径，适合从仓库根目录运行。不要提交真实 `.env`。

## 6. 初始化数据库

执行迁移：

```bash
npm run backend:migrate
```

初始化模板和演示数据：

```bash
npm run backend:init-demo
```

检查高考数据健康：

```bash
npm run backend:data-health
npm run backend:data-health -- --json
```

当前主库已并入高考 raw 表。需要同步 handoff 或重新物化时再使用：

```bash
npm run backend:merge-handoff
npm run backend:materialize-gaokao
npm run backend:bootstrap-special-types -- --year 2025 --year 2026
```

这些命令会改 `data/app.db`，执行前后应确认有备份和健康摘要。

## 7. 启动项目

最简单方式：

```bash
npm run dev
```

它会同时启动：

- 后端：`http://127.0.0.1:8000`
- 前端：`http://127.0.0.1:5173`

macOS 双击方式：

```text
start-local-edu.command
```

只启动后端：

```bash
npm run backend:dev
```

只启动前端：

```bash
npm run frontend:dev
```

启动后可以打开：

- 前端页面：`http://127.0.0.1:5173`
- 后端健康检查：`http://127.0.0.1:8000/api/system/health`
- API 文档：`http://127.0.0.1:8000/docs`

## 8. 运行测试和构建

后端测试：

```bash
npm run backend:test
```

前端检查：

```bash
npm run frontend:lint
npm run frontend:test
npm run frontend:build
```

跨端 E2E：

```bash
npm run e2e:install
npm run check:e2e
```

统一检查：

```bash
npm run check
npm run check:all
```

P0 本地交付验收：

```bash
npm run backend:p0-check
npm run backend:p0-check -- --json
```

## 9. 生产构建和桌面包

前端生产构建：

```bash
npm run frontend:build
```

桌面壳准备：

```bash
npm run desktop:prepare
```

macOS 目录产物：

```bash
npm run desktop:dist:mac
```

Windows 目录产物或安装包：

```bash
npm run desktop:dist:win:dir
npm run desktop:dist:win:nsis
```

窗口 0 未重新验证 Windows 产物；交付前需要窗口 9 或窗口 10 单独验收。

## 10. 常见问题

### 端口被占用

`npm run dev` 会先检查 `127.0.0.1:5173` 和 `127.0.0.1:8000`。如果端口已被本项目占用，会复用；如果端口被其它程序占用，会给出错误。

检查后端：

```bash
curl -s http://127.0.0.1:8000/api/system/health
```

检查前端：

```bash
curl -I -s http://127.0.0.1:5173
```

### 缺少虚拟环境

如果后端命令提示找不到 `.venv/bin/python`、`alembic` 或 `pytest`，重新执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e './apps/backend[dev]'
```

### 数据库迁移失败

先不要删除 `data/app.db`。执行：

```bash
npm run backend:p0-check -- --json
npm run backend:data-health -- --json
```

确认备份目录 `data/backups/` 是否已有可恢复备份，再决定下一步。

### 高考数据缺口

高考数据缺口不是启动故障。当前已知缺口包括特殊类型录取结果、一分一段 2020-2023、省控线 2020-2023、政策参考偏少和章程待复核。查看入口：

```text
http://127.0.0.1:5173/gaokao-data
```

进入“山东覆盖”页签。

## 11. 非程序员日常使用路径

1. 双击 `start-local-edu.command`。
2. 浏览器打开 `http://127.0.0.1:5173`。
3. 进入“高考数据”看山东覆盖和数据缺口。
4. 进入“高考志愿”维护规则、生成候选、保存志愿草稿。
5. 进入“报表中心”打印或导出材料。
6. 做重要数据操作前，先在“系统设置”创建备份。
