@echo off

rem 检查虚拟环境是否存在
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

rem 激活虚拟环境
echo Activating virtual environment...
call venv\Scripts\activate

rem 安装依赖
echo Installing dependencies...
pip install -r requirements.txt

rem 检查.env文件是否存在
if not exist ".env" (
    echo Creating .env file from .env.example...
    copy .env.example .env
)

rem 初始化数据库
echo Initializing database...
python init_db.py

rem 启动服务
echo Starting server...
python run.py
