@echo off
cd /d "%~dp0"
echo Starting FastAPI OCR Server...
set OCR_USE_GPU=True
set DISABLE_MODEL_SOURCE_CHECK=True
set OCR_LIMIT_SIDE_LEN=736
set OCR_WORKERS=1
python fastapi_server.py
pause
