#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON="${LAB_PYTHON:-work/.venv/bin/python}"
if [[ ! -x "$PYTHON" || ! -d frontend/node_modules ]]; then
  echo "Install dependencies first: ./scripts/install.sh"; exit 1
fi
"$PYTHON" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
(cd frontend && exec node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173) &
FRONTEND_PID=$!
cleanup() { kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
printf 'Strategy Research Lab: http://127.0.0.1:5173\nAPI docs: http://127.0.0.1:8000/docs\n'
while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do sleep 1; done
