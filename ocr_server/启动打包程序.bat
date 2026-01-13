@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "OCR_USE_GPU=True"
set "DISABLE_MODEL_SOURCE_CHECK=True"
set "OCR_LIMIT_SIDE_LEN=736"
set "OCR_WORKERS=1"
echo Starting OCR Server...
echo Config: GPU=%OCR_USE_GPU%, Size=%OCR_LIMIT_SIDE_LEN%, Workers=%OCR_WORKERS%
echo Please ensure VC++ Redistributable and GPU drivers are installed.
echo.
if exist "dist_v4\ocr_server_fastapi_v4\ocr_server_fastapi_v4.exe" (
    echo Found v4 executable in dist_v4 folder. Switching directory...
    cd /d "dist_v4\ocr_server_fastapi_v4"
    ocr_server_fastapi_v4.exe
    goto :end
)
if exist "ocr_server_fastapi_v4.exe" (
    echo Found v4 executable in current directory.
    ocr_server_fastapi_v4.exe
    goto :end
)
if exist "dist\ocr_server_fastapi_v4\ocr_server_fastapi_v4.exe" (
    echo Found v4 executable in dist folder. Switching directory...
    cd /d "dist\ocr_server_fastapi_v4"
    ocr_server_fastapi_v4.exe
    goto :end
)
echo ERROR: Could not find 'ocr_server_fastapi_v4.exe'.
echo.
if exist "fastapi_server.py" (
    echo Attempting to run from source code...
    python fastapi_server.py
    goto :end
)
echo Please copy this batch file into the 'ocr_server_fastapi' folder
echo where the .exe file is located, or ensure source code is present.
echo.
:end
endlocal
pause
