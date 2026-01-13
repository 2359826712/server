@echo off
setlocal

echo ===================================================
echo Setting up Build Environment for OCR Server (CUDA 11)
echo ===================================================

echo Checking for Python 3.10...
py -3.10 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python 3.10 not found via 'py -3.10'. Checking 'python' command...
    python --version 2>&1 | findstr "3.10" >nul
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Python 3.10 is required but not found!
        echo Please install Python 3.10.11 manually.
        echo IMPORTANT: During installation, check "Add Python to PATH".
        echo.
        pause
        exit /b 1
    )
    set PYTHON_CMD=python
) else (
    set PYTHON_CMD=py -3.10
)

echo Using Python: %PYTHON_CMD%
echo.

if exist venv_cu11 (
    echo Virtual environment 'venv_cu11' already exists.
    set /p RECREATE="Do you want to recreate it? (y/n) [n]: "
    if /i "%RECREATE%"=="y" (
        echo Removing existing venv...
        rmdir /s /q venv_cu11
        echo Creating virtual environment venv_cu11...
        %PYTHON_CMD% -m venv venv_cu11
    )
) else (
    echo Creating virtual environment venv_cu11...
    %PYTHON_CMD% -m venv venv_cu11
)

echo Activating virtual environment...
call venv_cu11\Scripts\activate

echo.
echo Installing PaddlePaddle GPU (CUDA 11.8)...
echo This makes sure we get the version compatible with GTX 1080 (Pascal)...
pip install paddlepaddle-gpu -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install paddlepaddle-gpu.
    pause
    exit /b 1
)

echo.
echo Installing other dependencies from requirements-gpu-cu11.txt...
pip install -r requirements-gpu-cu11.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo ===================================================
echo Starting Build Process...
echo ===================================================
python build_fastapi_server.py

echo.
echo ===================================================
if exist "dist_v4\ocr_server_fastapi_v4\ocr_server_fastapi_v4.exe" (
    echo [SUCCESS] Build completed successfully!
    echo Executable is located at: dist_v4\ocr_server_fastapi_v4\ocr_server_fastapi_v4.exe
    echo.
    echo You can now copy the 'dist_v4' folder to your GTX 1080 machine.
) else (
    echo [FAILURE] Build failed. Executable not found.
)
echo ===================================================
pause
