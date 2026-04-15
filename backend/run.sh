#!/bin/bash

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "Activating virtual environment..."
source venv/bin/activate

# 安装依赖
echo "Installing dependencies..."
pip install -r requirements.txt

# 检查.env文件是否存在
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
fi

# 初始化数据库
echo "Initializing database..."
python init_db.py

# 启动服务
echo "Starting server..."
python run.py
