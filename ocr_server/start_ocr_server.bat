@echo off
setlocal
cd /d "%~dp0"
set DISABLE_MODEL_SOURCE_CHECK=True
set PADDLEPDX_NO_NETWORK=True
set PYTHONPATH=%CD%
set "PYTHON_BASE=%LOCALAPPDATA%\Programs\Python\Python312\Lib\site-packages\nvidia"
set "CUDNN_BIN=%PYTHON_BASE%\cudnn\bin"
set "CUBLAS_BIN=%PYTHON_BASE%\cublas\bin"
set "NVRTC_BIN=%PYTHON_BASE%\cuda_nvrtc\bin"
set PATH=%CUDNN_BIN%;%CUBLAS_BIN%;%NVRTC_BIN%;%PATH%
python -m app.main
