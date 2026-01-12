@echo off
cd /d "%~dp0"
echo Starting OCR Server...

REM --- Configuration ---
REM Use GPU (True/False)
set OCR_USE_GPU=True

REM Disable PaddlePaddle model source check to speed up startup
set DISABLE_MODEL_SOURCE_CHECK=True

REM Max image side length (640-960)
set OCR_LIMIT_SIDE_LEN=736

REM Worker processes (1 for GPU)
set OCR_WORKERS=1
REM ---------------------

echo Config: GPU=%OCR_USE_GPU%, Size=%OCR_LIMIT_SIDE_LEN%, Workers=%OCR_WORKERS%
echo Please ensure VC++ Redistributable and GPU drivers are installed.
echo.

REM Check if exe exists in current folder (Deployed mode)
if exist "ocr_server_fastapi.exe" (
    echo Found executable in current directory.
    ocr_server_fastapi.exe
    goto :end
)

REM Check if exe exists in dist folder (Dev/Build mode)
if exist "dist\ocr_server_fastapi\ocr_server_fastapi.exe" (
    echo Found executable in dist folder. Switching directory...
    cd "dist\ocr_server_fastapi"
    ocr_server_fastapi.exe
    goto :end
)

REM If not found
echo ERROR: Could not find 'ocr_server_fastapi.exe'.
echo.
echo Attempting to run from source code...
if exist "fastapi_server.py" (
    echo Found fastapi_server.py.
    echo Please ensure dependencies are installed:
    if "%OCR_USE_GPU%"=="True" (
        echo pip install -r requirements-gpu.txt
    ) else (
        echo pip install -r requirements-cpu.txt
    )
    echo.
    python fastapi_server.py
    goto :end
)

echo Please copy this batch file into the 'ocr_server_fastapi' folder
echo where the .exe file is located, or ensure source code is present.
echo.

:end
pause
