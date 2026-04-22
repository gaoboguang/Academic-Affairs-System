const fs = require("node:fs");
const path = require("node:path");

const repoRoot = path.resolve(__dirname, "..");

const removableNames = new Set([
  ".DS_Store",
  "__pycache__",
  ".pytest_cache",
  ".vite-temp",
  ".vue-global-types",
  "test-results",
  "playwright-report",
]);

const removableSuffixes = [
  ".egg-info",
  ".tsbuildinfo",
];

const skippedDirNames = new Set([
  ".git",
  ".venv",
  "node_modules",
]);

const removed = [];

function shouldRemove(name) {
  if (removableNames.has(name)) return true;
  return removableSuffixes.some((suffix) => name.endsWith(suffix));
}

function walk(currentPath) {
  const entries = fs.readdirSync(currentPath, { withFileTypes: true });

  for (const entry of entries) {
    const entryPath = path.join(currentPath, entry.name);
    const relativePath = path.relative(repoRoot, entryPath) || ".";

    if (shouldRemove(entry.name)) {
      fs.rmSync(entryPath, { recursive: true, force: true });
      removed.push(relativePath);
      continue;
    }

    if (entry.isDirectory()) {
      if (skippedDirNames.has(entry.name)) {
        continue;
      }

      walk(entryPath);
    }
  }
}

walk(repoRoot);

if (removed.length === 0) {
  console.log("No local artifacts removed.");
  process.exit(0);
}

removed.sort();
console.log(`Removed ${removed.length} local artifact(s):`);
for (const target of removed) {
  console.log(target);
}
