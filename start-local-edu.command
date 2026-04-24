#!/bin/zsh
set -u

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR" || exit 1

echo "正在从下面的目录启动本地教务工具："
echo "$ROOT_DIR"
echo
echo "前端页面：http://127.0.0.1:5173"
echo "后端服务：http://127.0.0.1:8000"
echo

if ! command -v npm >/dev/null 2>&1; then
  echo "没有找到 npm。"
  echo "请先安装 Node.js，然后重新双击这个文件。"
  echo "可参考 docs/mac-user-startup-guide.md 的“第一次准备”。"
  read -r "?按回车关闭窗口..."
  exit 1
fi

if [ ! -d "node_modules" ]; then
  echo "提示：当前没有找到 node_modules，首次启动可能会失败。"
  echo "如果后面报错，请先在终端执行："
  echo "  cd \"$ROOT_DIR\""
  echo "  npm install"
  echo
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "提示：当前没有找到后端虚拟环境 .venv。"
  echo "如果后面报错，请先在终端执行："
  echo "  cd \"$ROOT_DIR\""
  echo "  python3 -m venv .venv"
  echo "  source .venv/bin/activate"
  echo "  pip install -e './apps/backend[dev]'"
  echo
fi

(
  for _ in {1..60}; do
    if curl -s -o /dev/null http://127.0.0.1:5173; then
      open http://127.0.0.1:5173 >/dev/null 2>&1 || true
      exit 0
    fi
    sleep 1
  done
) &

npm run dev
STATUS=$?

if [ "$STATUS" -ne 0 ]; then
  echo
  echo "本地教务工具启动失败，退出码：$STATUS"
  echo
  echo "可以按下面步骤手动排查："
  echo "  cd \"$ROOT_DIR\""
  echo "  node scripts/dev-local.cjs --help"
  echo "  npm run dev"
  echo
  echo "常见原因："
  echo "- 5173 或 8000 端口被其它程序占用"
  echo "- 没有执行 npm install"
  echo "- 没有创建 .venv 或没有安装后端依赖"
  echo
  echo "详细说明见 docs/mac-user-startup-guide.md。"
  read -r "?按回车关闭窗口..."
fi

exit "$STATUS"
