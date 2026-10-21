#!/usr/bin/env bash
# 一键启动后端（开发模式）
# 使用：cd backend && bash run.sh
set -e
cd "$(dirname "$0")"
echo "==> Installing deps (if needed)..."
pip install -r requirements.txt
echo "==> Starting FastAPI on http://localhost:8000"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --ws-max-size 4194304
