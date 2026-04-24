#!/bin/zsh
set -u

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR" || exit 1

echo "Starting local-edu-tool from: $ROOT_DIR"
echo "Frontend: http://127.0.0.1:5173"
echo "Backend:  http://127.0.0.1:8000"
echo

if ! command -v npm >/dev/null 2>&1; then
  echo "npm was not found. Please install Node.js first."
  read -r "?Press Enter to close..."
  exit 1
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
  echo "Service startup failed with exit code $STATUS."
  echo "You can also try manually:"
  echo "  cd \"$ROOT_DIR\""
  echo "  npm run dev"
  read -r "?Press Enter to close..."
fi

exit "$STATUS"
