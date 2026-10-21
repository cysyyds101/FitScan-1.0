#!/bin/bash
# FitScan 开发环境启动脚本
# Usage: bash scripts/start_dev.sh

set -e

echo "=== FitScan Dev Startup ==="

# Step 1: Start capture.py (RealSense / simulated)
# Requires conda env "fitscan-capture" with pyrealsense2 2.54.1
# Create with: conda create -n fitscan-capture python=3.10
# Then: conda run -n fitscan-capture pip install pyrealsense2==2.54.1.5216 websockets
echo "[1/4] Starting capture.py..."
cd backend/capture
conda run -n fitscan-capture python capture.py &
CAPTURE_PID=$!
cd ../..
sleep 2
echo "    capture.py PID=$CAPTURE_PID (ws://localhost:8765)"

# Step 2: Start FastAPI backend
echo "[2/4] Starting FastAPI backend..."
cd backend
uvicorn app.main:app --reload --port 8000 --ws-max-size 4194304 &
BACKEND_PID=$!
cd ..
sleep 3
echo "    FastAPI PID=$BACKEND_PID (http://localhost:8000)"

# Step 3: Start AI server (mock)
echo "[3/4] Starting AI server..."
cd ai_server
uvicorn main:app --port 8080 &
AI_PID=$!
cd ..
sleep 2
echo "    AI server PID=$AI_PID (http://localhost:8080)"

# Step 4: Start frontend
echo "[4/4] Starting frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
sleep 3
echo "    Frontend PID=$FRONTEND_PID (http://localhost:5173)"

echo ""
echo "=== All services started ==="
echo "  Frontend:   http://localhost:5173"
echo "  Backend:    http://localhost:8000/docs"
echo "  AI Server:  http://localhost:8080/docs"
echo "  Capture WS: ws://localhost:8765"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait and cleanup on Ctrl+C
trap "kill $CAPTURE_PID $BACKEND_PID $AI_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
