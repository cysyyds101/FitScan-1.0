@echo off
echo ========================================
echo FitScan - 智能人体尺寸估算系统
echo ========================================
echo.

echo 检查环境...
python --version
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo.
echo 检查依赖...
pip show opencv-python >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 正在安装依赖...
    pip install -r requirements.txt
)

echo.
echo 启动FitScan...
python main.py

pause