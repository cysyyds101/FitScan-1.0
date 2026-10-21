#!/bin/bash
# 快速连通性验证脚本

echo "=== FitScan Connectivity Check ==="

check() {
  local label=$1; local url=$2
  if curl -sf "$url" > /dev/null 2>&1; then
    echo "  [OK] $label ($url)"
  else
    echo "  [FAIL] $label ($url) -- NOT REACHABLE"
  fi
}

check "Backend health"     "http://localhost:8000/api/health"
check "AI Server health"   "http://localhost:8080/health"
check "Clothing API"       "http://localhost:8000/api/clothing"
check "Static models"      "http://localhost:8000/static/models/clothing_01.glb"
check "Frontend"           "http://localhost:5173"

echo ""
echo "WebSocket check (capture.py):"
python3 -c "
import asyncio, websockets, sys
async def check():
    try:
        async with websockets.connect('ws://localhost:8765', open_timeout=3) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=3)
            print('  [OK] capture.py ws://localhost:8765 -- receiving frames')
    except Exception as e:
        print(f'  [FAIL] capture.py ws://localhost:8765 -- {e}')
asyncio.run(check())
" 2>/dev/null || echo "  [SKIP] python3/websockets not available for WS check"

echo ""
echo "WebSocket relay check (FastAPI /ws/camera):"
python3 -c "
import asyncio, websockets
async def check():
    try:
        async with websockets.connect('ws://localhost:8000/ws/camera', open_timeout=3) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=3)
            print('  [OK] FastAPI relay ws://localhost:8000/ws/camera -- relaying frames')
    except Exception as e:
        print(f'  [FAIL] FastAPI relay ws://localhost:8000/ws/camera -- {e}')
asyncio.run(check())
" 2>/dev/null

echo ""
echo "=== Done ==="
