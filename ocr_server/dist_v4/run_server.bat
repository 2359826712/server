@echo off
setlocal
echo Starting OCR Server (CPU Mode)...
set DISABLE_MODEL_SOURCE_CHECK=True
set OCR_SERVER_TASK_TIMEOUT=120
cd /d "%~dp0ocr_server_fastapi_v4"
if exist "ocr_server_fastapi_v4.exe" (
    echo Found executable, launching...
    ocr_server_fastapi_v4.exe
) else (
    echo [ERROR] ocr_server_fastapi_v4.exe not found
    pause
)
