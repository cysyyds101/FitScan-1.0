#!/usr/bin/env bash
# FitScan MVP 一键启动
# 启动后端 (8000) 与前端 (5173)，Ctrl-C 同时停止
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

cleanup() {
  echo
  echo "==> Stopping..."
  jobs -p | xargs -r kill 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# 后端
echo "==> Backend: installing & starting on :8000"
cd "$ROOT/backend"
pip install -q -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACK_PID=$!

# 前端
echo "==> Frontend: installing & starting on :5173"
cd "$ROOT/frontend"
if [ ! -d node_modules ]; then
  npm install --no-audit --no-fund
fi
npm run dev &
FRONT_PID=$!

echo
echo "============================================"
echo "  Backend:  http://localhost:8000  (Swagger: /docs)"
echo "  Frontend: http://localhost:5173/tryon"
echo "  Press Ctrl-C to stop both."
echo "============================================"
wait $BACK_PID $FRONT_PID
