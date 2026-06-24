const { app, BrowserWindow, Menu, dialog, shell } = require("electron");
const http = require("node:http");
const { request: httpRequest } = require("node:http");
const fs = require("node:fs");
const fsp = require("node:fs/promises");
const path = require("node:path");
const { spawn } = require("node:child_process");

const API_PORT = Number(process.env.LOCAL_EDU_DESKTOP_API_PORT || 18000);
const UI_PORT = Number(process.env.LOCAL_EDU_DESKTOP_UI_PORT || 18080);
const DEV_RENDERER_URL = process.env.LOCAL_EDU_DESKTOP_RENDERER_URL || "";

let backendProcess = null;
let frontendServer = null;

function isWindows() {
  return process.platform === "win32";
}

function getProjectRoot() {
  return path.resolve(__dirname, "..", "..");
}

function getDataRoot() {
  return app.isPackaged ? path.join(app.getPath("userData"), "data") : path.join(getProjectRoot(), "data");
}

function getDesktopStatePath() {
  return path.join(app.getPath("userData"), "desktop-state.json");
}

function getDevPython() {
  const projectRoot = getProjectRoot();
  const venvPython = isWindows()
    ? path.join(projectRoot, ".venv", "Scripts", "python.exe")
    : path.join(projectRoot, ".venv", "bin", "python");
  if (fs.existsSync(venvPython)) return venvPython;
  return isWindows() ? "python" : "python3";
}

function getBackendConfig() {
  const commonArgs = [
    "--host",
    "127.0.0.1",
    "--port",
    String(API_PORT),
    "--data-dir",
    getDataRoot(),
  ];
  if (app.isPackaged) {
    return {
      command: path.join(
        process.resourcesPath,
        "backend",
        isWindows() ? "local-edu-backend-desktop.exe" : "local-edu-backend-desktop",
      ),
      args: commonArgs,
      cwd: process.resourcesPath,
    };
  }

  const projectRoot = getProjectRoot();
  return {
    command: getDevPython(),
    args: [
      path.join(projectRoot, "apps", "backend", "app", "desktop_entry.py"),
      ...commonArgs,
    ],
    cwd: projectRoot,
  };
}

function getContentType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  if (ext === ".html") return "text/html; charset=utf-8";
  if (ext === ".js" || ext === ".mjs") return "text/javascript; charset=utf-8";
  if (ext === ".css") return "text/css; charset=utf-8";
  if (ext === ".json") return "application/json; charset=utf-8";
  if (ext === ".svg") return "image/svg+xml";
  if (ext === ".png") return "image/png";
  if (ext === ".jpg" || ext === ".jpeg") return "image/jpeg";
  if (ext === ".woff2") return "font/woff2";
  return "application/octet-stream";
}

function proxyApi(req, res) {
  const proxy = httpRequest(
    {
      hostname: "127.0.0.1",
      port: API_PORT,
      path: req.url,
      method: req.method,
      headers: req.headers,
    },
    (proxyRes) => {
      res.writeHead(proxyRes.statusCode || 502, proxyRes.headers);
      proxyRes.pipe(res);
    },
  );
  proxy.on("error", (error) => {
    res.writeHead(502, { "Content-Type": "application/json; charset=utf-8" });
    res.end(JSON.stringify({ detail: `桌面代理请求失败: ${error.message}` }));
  });
  req.pipe(proxy);
}

async function openLocalPath(targetPath) {
  const errorMessage = await shell.openPath(targetPath);
  if (errorMessage) {
    dialog.showErrorBox("打开目录失败", errorMessage);
  }
}

async function loadDesktopState() {
  try {
    const content = await fsp.readFile(getDesktopStatePath(), "utf-8");
    return JSON.parse(content);
  } catch {
    return {};
  }
}

async function saveDesktopState(nextState) {
  await fsp.mkdir(path.dirname(getDesktopStatePath()), { recursive: true });
  await fsp.writeFile(getDesktopStatePath(), JSON.stringify(nextState, null, 2), "utf-8");
}

function isInternalPrintUrl(targetUrl) {
  try {
    const parsed = new URL(targetUrl);
    return (
      ["127.0.0.1", "localhost"].includes(parsed.hostname) &&
      parsed.pathname.startsWith("/print/")
    );
  } catch {
    return false;
  }
}

function openPrintWindow(targetUrl) {
  const printWindow = new BrowserWindow({
    width: 1180,
    height: 860,
    minWidth: 960,
    minHeight: 700,
    autoHideMenuBar: true,
    title: "打印预览",
    webPreferences: {
      contextIsolation: true,
      sandbox: true,
    },
  });
  void printWindow.loadURL(targetUrl);
}

async function showFirstRunDialog() {
  const state = await loadDesktopState();
  if (state.seenWelcome) return;

  const dataRoot = getDataRoot();
  const result = await dialog.showMessageBox({
    type: "info",
    title: "欢迎使用本地教务工具",
    message: "桌面版已就绪，数据默认保存在本机。",
    detail: `数据目录：${dataRoot}\n\n建议首次使用先确认数据目录位置，并定期在系统设置里执行备份。`,
    buttons: ["知道了", "打开数据目录"],
    defaultId: 0,
    cancelId: 0,
    noLink: true,
  });

  if (result.response === 1) {
    await openLocalPath(dataRoot);
  }

  state.seenWelcome = true;
  await saveDesktopState(state);
}

function buildApplicationMenu(mainWindow) {
  const dataRoot = getDataRoot();
  const template = [
    {
      label: "文件",
      submenu: [
        {
          label: "打开数据目录",
          click: () => {
            void openLocalPath(dataRoot);
          },
        },
        {
          label: "打开导出目录",
          click: () => {
            void openLocalPath(path.join(dataRoot, "exports"));
          },
        },
        { type: "separator" },
        { role: "quit", label: "退出" },
      ],
    },
    {
      label: "查看",
      submenu: [
        { role: "reload", label: "重新加载" },
        { role: "toggledevtools", label: "开发者工具" },
        { type: "separator" },
        { role: "resetzoom", label: "重置缩放" },
        { role: "zoomin", label: "放大" },
        { role: "zoomout", label: "缩小" },
      ],
    },
    {
      label: "帮助",
      submenu: [
        {
          label: "打开 API 文档",
          click: () => {
            void shell.openExternal(`http://127.0.0.1:${API_PORT}/docs`);
          },
        },
        {
          label: "打开数据目录",
          click: () => {
            void openLocalPath(dataRoot);
          },
        },
      ],
    },
  ];

  if (process.platform === "darwin") {
    template.unshift({
      label: app.name,
      submenu: [
        { role: "about", label: "关于本地教务工具" },
        { type: "separator" },
        { role: "services", label: "服务" },
        { type: "separator" },
        { role: "hide", label: "隐藏本地教务工具" },
        { role: "hideOthers", label: "隐藏其他" },
        { role: "unhide", label: "全部显示" },
        { type: "separator" },
        { role: "quit", label: "退出" },
      ],
    });
    template[2].submenu.unshift(
      { role: "front", label: "前置全部窗口" },
      { type: "separator" },
    );
  }

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
  if (mainWindow) {
    mainWindow.setMenuBarVisibility(true);
  }
}

async function createFrontendServer() {
  if (!app.isPackaged) return null;

  const frontendRoot = path.join(process.resourcesPath, "frontend");
  const server = http.createServer(async (req, res) => {
    const url = new URL(req.url || "/", `http://127.0.0.1:${UI_PORT}`);
    if (url.pathname.startsWith("/api")) {
      proxyApi(req, res);
      return;
    }

    const sanitizedPath = url.pathname === "/" ? "/index.html" : url.pathname;
    let targetPath = path.join(frontendRoot, sanitizedPath.replace(/^\/+/, ""));

    if (!targetPath.startsWith(frontendRoot)) {
      res.writeHead(403).end("Forbidden");
      return;
    }

    let filePath = targetPath;
    try {
      const stat = await fsp.stat(filePath);
      if (stat.isDirectory()) {
        filePath = path.join(filePath, "index.html");
      }
    } catch {
      filePath = path.join(frontendRoot, "index.html");
    }

    try {
      const content = await fsp.readFile(filePath);
      res.writeHead(200, { "Content-Type": getContentType(filePath) });
      res.end(content);
    } catch (error) {
      res.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
      res.end(`读取前端资源失败: ${error.message}`);
    }
  });

  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(UI_PORT, "127.0.0.1", () => resolve());
  });
  return server;
}

async function waitForBackend(timeoutMs = 30000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    try {
      const response = await fetch(`http://127.0.0.1:${API_PORT}/api/system/health`);
      if (response.ok) return;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error("桌面版后端启动超时");
}

function startBackend() {
  const config = getBackendConfig();
  backendProcess = spawn(config.command, config.args, {
    cwd: config.cwd,
    env: {
      ...process.env,
      LOCAL_EDU_HOST: "127.0.0.1",
      LOCAL_EDU_PORT: String(API_PORT),
    },
    stdio: "inherit",
  });
  backendProcess.once("exit", (code) => {
    if (!app.isQuitting && code !== 0) {
      dialog.showErrorBox("桌面后端已退出", `后端进程异常退出，退出码：${code ?? "unknown"}`);
    }
  });
}

async function createMainWindow() {
  startBackend();
  await waitForBackend();
  frontendServer = await createFrontendServer();

  const mainWindow = new BrowserWindow({
    width: 1480,
    height: 920,
    minWidth: 1200,
    minHeight: 760,
    autoHideMenuBar: true,
    title: "本地教务工具",
    webPreferences: {
      contextIsolation: true,
      sandbox: true,
    },
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (isInternalPrintUrl(url)) {
      openPrintWindow(url);
      return { action: "deny" };
    }
    shell.openExternal(url);
    return { action: "deny" };
  });

  const entryUrl = app.isPackaged ? `http://127.0.0.1:${UI_PORT}` : DEV_RENDERER_URL;
  if (!entryUrl) {
    throw new Error("桌面开发模式缺少 LOCAL_EDU_DESKTOP_RENDERER_URL");
  }
  await mainWindow.loadURL(entryUrl);
  buildApplicationMenu(mainWindow);
  await showFirstRunDialog();
}

function cleanup() {
  app.isQuitting = true;
  if (frontendServer) {
    frontendServer.close();
    frontendServer = null;
  }
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill();
    backendProcess = null;
  }
}

app.on("window-all-closed", () => {
  cleanup();
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
  cleanup();
});

app.whenReady().then(() => createMainWindow().catch((error) => {
  cleanup();
  dialog.showErrorBox("桌面版启动失败", error.message);
  app.quit();
}));
