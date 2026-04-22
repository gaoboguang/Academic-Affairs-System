const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const rootDir = path.resolve(__dirname, "..", "..", "..");
const desktopDir = path.resolve(__dirname, "..");
const frontendOutDir = path.join(desktopDir, ".dist", "frontend");
const backendOutDir = path.join(desktopDir, ".dist", "backend");
const pyinstallerDistDir = path.join(desktopDir, ".dist", "pyinstaller-dist");
const pyinstallerWorkDir = path.join(desktopDir, ".dist", "pyinstaller-build");
const pyinstallerSpecDir = path.join(desktopDir, ".dist", "pyinstaller-spec");

function run(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: options.cwd || rootDir,
      stdio: "inherit",
      env: options.env || process.env,
    });
    child.on("exit", (code) => {
      if (code === 0) {
        resolve();
        return;
      }
      reject(new Error(`${command} ${args.join(" ")} failed with code ${code}`));
    });
  });
}

function ensureCleanDir(targetDir) {
  fs.rmSync(targetDir, { recursive: true, force: true });
  fs.mkdirSync(targetDir, { recursive: true });
}

async function buildBackendBinary() {
  const python = process.platform === "win32"
    ? path.join(rootDir, ".venv", "Scripts", "python.exe")
    : path.join(rootDir, ".venv", "bin", "python");
  if (!fs.existsSync(python)) {
    throw new Error("未找到 .venv Python，可先执行 ./scripts/dev.sh 或手工创建虚拟环境。");
  }

  const outputName = process.platform === "win32" ? "local-edu-backend-desktop.exe" : "local-edu-backend-desktop";
  await run(python, [
    "-m",
    "PyInstaller",
    "--noconfirm",
    "--clean",
    "--onefile",
    "--name",
    "local-edu-backend-desktop",
    "--distpath",
    pyinstallerDistDir,
    "--workpath",
    pyinstallerWorkDir,
    "--specpath",
    pyinstallerSpecDir,
    "--paths",
    path.join(rootDir, "apps", "backend"),
    path.join(rootDir, "apps", "backend", "app", "desktop_entry.py"),
  ]);

  const sourcePath = path.join(pyinstallerDistDir, outputName);
  const targetPath = path.join(backendOutDir, outputName);
  fs.copyFileSync(sourcePath, targetPath);
}

async function main() {
  ensureCleanDir(frontendOutDir);
  ensureCleanDir(backendOutDir);
  ensureCleanDir(pyinstallerDistDir);
  ensureCleanDir(pyinstallerWorkDir);
  ensureCleanDir(pyinstallerSpecDir);

  await run("npm", ["run", "frontend:build"]);
  fs.cpSync(path.join(rootDir, "apps", "frontend", "dist"), frontendOutDir, { recursive: true });

  await buildBackendBinary();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
