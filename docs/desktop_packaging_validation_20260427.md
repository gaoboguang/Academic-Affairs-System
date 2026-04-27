# 桌面端交付验证记录（2026-04-27）

## 验证结论

- 状态：macOS 目录构建通过。
- 构建产物：`dist/desktop/mac/本地教务工具.app`
- 后端二进制：`dist/desktop/mac/本地教务工具.app/Contents/Resources/backend/local-edu-backend-desktop`
- 前端资源：`dist/desktop/mac/本地教务工具.app/Contents/Resources/frontend/index.html`
- 本轮未改业务逻辑、未改数据库结构、未写 `data/app.db`。

## 打包链路

桌面端由 `apps/desktop/scripts/dist.cjs` 驱动：

1. 先执行 `npm run bundle --workspace @local-edu/desktop`。
2. `apps/desktop/scripts/prepare.cjs` 执行前端生产构建，并复制 `apps/frontend/dist` 到 `apps/desktop/.dist/frontend`。
3. 同一脚本使用 `.venv/bin/python -m PyInstaller` 将 `apps/backend/app/desktop_entry.py` 打为单文件后端二进制，并复制到 `apps/desktop/.dist/backend`。
4. `electron-builder` 根据 `apps/desktop/package.json` 的 `extraResources`，把 `.dist/frontend` 放入 `Resources/frontend`，把 `.dist/backend` 放入 `Resources/backend`。

## 运行时定位

- 后端端口：默认 `18000`，可用 `LOCAL_EDU_DESKTOP_API_PORT` 覆盖。
- 前端本地资源端口：默认 `18080`，可用 `LOCAL_EDU_DESKTOP_UI_PORT` 覆盖。
- 打包后后端入口：`process.resourcesPath/backend/local-edu-backend-desktop`。
- 打包后前端资源：`process.resourcesPath/frontend`，由 Electron 主进程内置 HTTP server 提供。
- 打包后数据目录：`app.getPath("userData")/data`。
- 开发态数据目录：仓库根目录 `data/`。
- 后端启动参数：`--host 127.0.0.1 --port <API_PORT> --data-dir <dataRoot>`。
- `desktop_entry.py` 会把 `--data-dir` 映射为：
  - 主库：`<dataRoot>/app.db`
  - 附件：`<dataRoot>/uploads`
  - 备份：`<dataRoot>/backups`
  - 模板：`<dataRoot>/templates`
  - 导出：`<dataRoot>/exports`
  - 日志：`<dataRoot>/logs`

## 本轮验证命令

```bash
npm run desktop:dist:mac
```

结果：通过。前端生产构建、PyInstaller 后端二进制、Electron macOS `dir` 打包均完成。

非阻断提示：

- `default Electron icon is used`：当前未配置正式应用图标。
- `skipped macOS application code signing`：本地构建禁用了签名自动发现，尚未做正式签名 / 公证。
- PyInstaller 提示若干未安装的数据库驱动 hidden import，例如 `psycopg2`、`MySQLdb`，当前项目使用 SQLite，不影响本轮桌面后端启动。

## 二进制冒烟

使用打包后的后端二进制和临时数据目录执行启动检查：

```bash
dist/desktop/mac/本地教务工具.app/Contents/Resources/backend/local-edu-backend-desktop \
  --host 127.0.0.1 \
  --port 18092 \
  --data-dir /tmp/local-edu-desktop-smoke-1777272736370
```

结果：通过。后端能创建临时 `app.db`，并且 `/api/dashboard/summary` 返回成功。

## 待后续处理

- 若要给老师分发 macOS 应用，需要补正式图标、签名和公证流程。
- 若要交付 Windows 安装包，还需要在 Windows 环境或可交叉构建环境中单独验证 `npm run desktop:dist:win:dir` 与 `npm run desktop:dist:win:nsis`。
- 当前桌面版首次启动使用用户数据目录的新库，不会自动拷贝仓库 `data/app.db`；正式交付前需明确“空库初始化”和“迁移现有主库”的用户操作说明。
