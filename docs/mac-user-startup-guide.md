# Mac 普通用户启动指南

- 文档日期：2026-04-24
- 适用对象：只想在 Mac 上打开本地教务工具的用户
- 默认地址：`http://127.0.0.1:5173`

## 第一次准备

第一次使用前，需要安装这些基础工具：

```bash
brew install node python git
```

进入项目目录：

```bash
cd /Users/gao/local-edu-tool
```

安装前端依赖：

```bash
npm install
```

准备后端环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e './apps/backend[dev]'
```

初始化数据库和模板：

```bash
npm run backend:migrate
npm run backend:init-demo
```

## 双击启动

日常使用时，在项目根目录双击：

```text
start-local-edu.command
```

启动后浏览器会自动打开：

```text
http://127.0.0.1:5173
```

如果浏览器没有自动打开，可以手动复制上面的地址到浏览器。

## 命令启动

也可以在终端执行：

```bash
cd /Users/gao/local-edu-tool
npm run start:local
```

这个命令会在后台启动或复用：

- 前端页面：`http://127.0.0.1:5173`
- 后端服务：`http://127.0.0.1:8000`

启动成功后，可以关闭终端窗口，服务仍会继续运行。日志在：

```text
data/logs/local-services/
```

## 查看状态

启动后可以打开：

- 主页面：`http://127.0.0.1:5173`
- 后端健康检查：`http://127.0.0.1:8000/api/system/health`
- API 文档：`http://127.0.0.1:8000/docs`

最小检查：

```bash
npm run backend:data-health
```

当前高考数据仍可能显示 P0 缺口。数据缺口不是启动失败，具体看页面里的“高考数据 -> 山东覆盖”。

## 关闭服务

如果是双击启动或执行了 `npm run start:local`，关闭终端窗口不会停止服务。要停止后台服务，执行：

```bash
cd /Users/gao/local-edu-tool
npm run stop:local
```

如果是开发调试时执行了 `npm run dev`，在那个终端里按：

```text
Control + C
```

## 启动失败时

先看启动窗口里的提示。常见原因和处理方式：

- 没有 `npm`：先安装 Node.js。
- 没有 `node_modules`：在项目根目录执行 `npm install`。
- 没有 `.venv`：按“第一次准备”重新创建后端环境。
- 端口被占用：确认 `5173` 和 `8000` 没有被其它程序占用。

可以执行下面两个检查：

```bash
curl -I -s http://127.0.0.1:5173
curl -s http://127.0.0.1:8000/api/system/health
```

如果两个地址已经有响应，再次执行 `npm run dev` 会复用已有服务。

日常使用优先执行 `npm run start:local`；`npm run dev` 更适合开发调试，因为终端关闭后前端服务会停止。

## 重要操作前

做导入、并库、物化或规则初始化前，先确认备份：

```bash
npm run backend:p0-check
```

日常只查看、推荐、打印、导出时，不需要手动改数据库文件。
