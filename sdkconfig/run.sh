#!/bin/bash

echo "========================================"
echo "FitScan - 智能人体尺寸估算系统"
echo "========================================"
echo ""

echo "检查环境..."
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到Python3，请先安装Python 3.7+"
    exit 1
fi

python3 --version

echo ""
echo "检查依赖..."
if ! python3 -c "import cv2" 2>/dev/null; then
    echo "[提示] 正在安装依赖..."
    pip3 install -r requirements.txt
fi

echo ""
echo "启动FitScan..."
python3 main.py