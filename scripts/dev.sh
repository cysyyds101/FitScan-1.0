#!/usr/bin/env bash
# dev.sh — start FitScan on THIS machine (Windows, RTX 5070, no conda on PATH).
#
# Replaces start-dev.sh and scripts/start_dev.sh, both of which were broken here:
#   - start-dev.sh        called bare `pip` / `uvicorn` — not on PATH
#   - scripts/start_dev.sh called `conda run -n fitscan-capture` — that env does not exist
# This script uses absolute interpreter paths only. See docs/FOUNDATION.md §2.1.
#
# Usage:  bash scripts/dev.sh [--no-capture] [--no-ai]
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/Scripts/python.exe"

NO_CAPTURE=0; NO_AI=0
for a in "$@"; do
  case "$a" in
    --no-capture) NO_CAPTURE=1 ;;
    --no-ai)      NO_AI=1 ;;
    *) echo "unknown flag: $a" >&2; exit 2 ;;
  esac
done

if [ ! -x "$PY" ]; then
  echo "FATAL: $PY not found. Run: bash scripts/setup_mirror_env.sh" >&2
  exit 1
fi

cleanup() {
  echo
  echo "[stop] killing $(jobs -p | wc -l) background job(s)"
  jobs -p | xargs -r kill 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# ── 1. capture (SR300, or simulated if absent) ───────────────────────────────
if [ "$NO_CAPTURE" -eq 0 ]; then
  echo "[1/4] capture.py  -> ws://localhost:8765"
  ( cd "$ROOT/backend/capture" && exec "$PY" capture.py ) &
else
  echo "[1/4] capture.py  SKIPPED (--no-capture)"
fi

# ── 2. FastAPI monolith ──────────────────────────────────────────────────────
# --ws-max-size is required: a 640x480 float32 frame is 1.2 MB and uvicorn's
# default 100 KB limit drops it silently. Matches backend/run.sh.
echo "[2/4] FastAPI       -> http://localhost:8000/docs"
( cd "$ROOT/backend" && exec "$PY" -m uvicorn app.main:app --port 8000 \
    --ws-max-size 4194304 --reload ) &

# ── 3. AI server (mock only) ─────────────────────────────────────────────────
# Only ai_server/main.py is startable here. ai_server/api.py is launched by
# launcher.py, which raises on win32 (launcher.py:50-68). See FOUNDATION D-11.
if [ "$NO_AI" -eq 0 ] && ( cd "$ROOT" && "$PY" -c "import ai_server.main" ) 2>/dev/null; then
  echo "[3/4] AI server     -> http://localhost:8080/docs"
  ( cd "$ROOT" && exec "$PY" -m uvicorn ai_server.main:app --port 8080 ) &
else
  echo "[3/4] AI server     SKIPPED (disabled, or ai_server.main not importable)"
fi

# ── 4. Frontend ──────────────────────────────────────────────────────────────
echo "[4/4] Vite          -> http://localhost:5173"
( cd "$ROOT/frontend" && exec npm run dev ) &

echo
echo "  frontend   http://localhost:5173/virtual-tryon"
echo "  backend    http://localhost:8000/docs"
echo "  ai (mock)  http://localhost:8080/docs"
echo "  capture    ws://localhost:8765"
echo
echo "Not started: the MIRROR real-time process (docs/FOUNDATION.md §4.1, T007)."
echo "Ctrl-C stops everything."
wait
