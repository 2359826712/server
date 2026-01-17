@echo off
chcp 65001 >nul
echo ==========================================
echo 正在启动 OCR 服务器...
echo 访问地址: http://127.0.0.1:5000/ocr
echo 健康检查: http://127.0.0.1:5000/ping
echo 提示: 按 Ctrl+C 可停止服务
echo ==========================================

:: 1. (可选) 设置鉴权密钥，不设置则为开放模式
:: set OCR_API_KEY=your-secret-key

:: 2. 检查环境依赖
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Flask 库。
    echo 请先运行以下命令安装依赖：
    echo pip install flask paddlepaddle paddleocr opencv-python
    echo.
    pause
    exit /b
)

:: 3. 启动服务
set OCR_VERSION=PP-OCRv4
python ocr_server_other/server.py
if %errorlevel% neq 0 (
    echo.
    echo [错误] 服务器异常退出
    pause
)
