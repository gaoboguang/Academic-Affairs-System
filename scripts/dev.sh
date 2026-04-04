#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e "./apps/backend[dev]"

pushd apps/backend >/dev/null
alembic upgrade head
popd >/dev/null

python scripts/init_data.py --demo

npm install

python -m uvicorn app.main:app --app-dir apps/backend --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

cleanup() {
  kill "$BACKEND_PID" >/dev/null 2>&1 || true
}

trap cleanup EXIT

npm run frontend:dev

