const { spawn } = require("node:child_process");
const path = require("node:path");

const rootDir = path.resolve(__dirname, "..", "..", "..");
const desktopDir = path.resolve(__dirname, "..");
const electronDistPath = path.join(desktopDir, "node_modules", "electron", "dist");

function resolveRequestedPlatform(args) {
  if (args.includes("--win")) return "win32";
  if (args.includes("--mac")) return "darwin";
  if (args.includes("--linux")) return "linux";
  return process.platform;
}

function shouldUseLocalElectronDist(targetPlatform) {
  return targetPlatform === process.platform;
}

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

async function main() {
  const cliArgs = process.argv.slice(2);
  const builderArgs = ["electron-builder", ...cliArgs];
  if (builderArgs.length === 1) {
    builderArgs.push("--dir");
  }
  const targetPlatform = resolveRequestedPlatform(cliArgs);
  await run("npm", ["run", "bundle"], { cwd: desktopDir });
  const builderEnv = {
    ...process.env,
    CSC_IDENTITY_AUTO_DISCOVERY: "false",
  };
  if (shouldUseLocalElectronDist(targetPlatform)) {
    builderEnv.ELECTRON_OVERRIDE_DIST_PATH = electronDistPath;
  }
  await run("npx", builderArgs, {
    cwd: desktopDir,
    env: builderEnv,
  });
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
