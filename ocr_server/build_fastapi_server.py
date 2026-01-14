import os
import struct
import subprocess
import sys
import shutil
import tempfile
import time

def main():
    if struct.calcsize("P") * 8 != 64:
        print("需要 64 位 Python")
        sys.exit(1)

    os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")

    # 1. 检查 PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("请先安装 PyInstaller: pip install pyinstaller")
        sys.exit(1)

    # 1.1 检查 GPU/CPU 依赖配置
    use_gpu = False
    print(f"Build Configuration: OCR_USE_GPU={use_gpu} (Forced CPU Mode)")
    
    try:
        import paddle
        print(f"PaddlePaddle version: {paddle.__version__}")
    except ImportError:
        print("PaddlePaddle not found!")
        sys.exit(1)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    work_dir = os.path.join(base_dir, "build_v4")
    dist_dir = os.path.join(base_dir, "dist_v4")
    try:
        if os.path.isdir(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)
        if os.path.isdir(dist_dir):
            shutil.rmtree(dist_dir, ignore_errors=True)
    except Exception:
        time.sleep(1)

    # 2. 生成 spec 文件内容
    # 优化：减少不必要的 collect_all，增加 excludes
    spec_content = r"""# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, copy_metadata
import os
import sys

block_cipher = None

datas = []
binaries = []
# 仅保留核心依赖的手动收集，其他让 PyInstaller 自动处理
hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "engineio.async_drivers.threading",
    "fastapi",
    "starlette",
    "paddle",
    "paddleocr",
    "imghdr", 
    "imgaug",
    "pyclipper",
    "shapely",
    "skimage",
    "skimage.feature._orb_descriptor_positions",
    "skimage.filters.edges",
    "scipy.special.cython_special",
    "python_multipart",
    "pandas",
    "sklearn", 
    "h11",
    "lmdb",
]

# 仅对 Paddle 相关库进行完整收集，因为它们有很多动态加载的资源
for pkg in [
    "paddle",
    "paddleocr",
    "pyclipper",
    "shapely",
    "websockets",
    "Cython",
]:
    try:
        tmp_ret = collect_all(pkg)
        datas += tmp_ret[0]
        binaries += tmp_ret[1]
        hiddenimports += tmp_ret[2]
    except Exception:
        pass

# 复制 metadata，解决 pkg_resources 相关问题
metadata_pkgs = [
    "paddle", "paddlepaddle", "paddleocr",
    "pandas", "scipy", "sklearn", "fastapi", "uvicorn",
    "imagesize", "opencv-contrib-python", "pyclipper", "pypdfium2", "python-bidi", "shapely",
    "einops", "ftfy", "Jinja2", "lxml", "openpyxl", "premailer", "regex", "safetensors",
    "sentencepiece", "tiktoken", "tokenizers", "imageio", "scikit-image",
    # Paddlex base requirements
    "chardet", "colorlog", "filelock", "huggingface-hub", 
    "modelscope", "numpy", "packaging", "pillow", "prettytable", "py-cpuinfo", 
    "pydantic", "PyYAML", "requests", "ruamel.yaml", "typing-extensions", "ujson",
    "tqdm", "rich", "click", "flask", "werkzeug"
]
for pkg in metadata_pkgs:
    try:
        datas += copy_metadata(pkg)
    except Exception:
        pass

# 排除大量不必要的库，加快分析速度并减小体积
    # 注意：不要排除 distutils 或 setuptools，因为某些库(如 numpy)可能隐式依赖它们来加载插件或配置
    excluded_modules = [
        "matplotlib", "tkinter", "PyQt5", "PySide2", "wx", 
        "IPython", "notebook", "jupyter",
        "botocore", "boto3", "awscli", 
        "httptools", "uvloop",
    ]

# 尝试手动添加 paddle 的 libs 目录
try:
    import paddle
    paddle_dir = os.path.dirname(paddle.__file__)
    libs_dir = os.path.join(paddle_dir, "libs")
    if os.path.isdir(libs_dir):
        for fn in os.listdir(libs_dir):
            if fn.lower().endswith(".dll"):
                binaries.append((os.path.join(libs_dir, fn), "paddle/libs"))
except Exception:
    pass

a = Analysis(
    ['fastapi_server.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_modules,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ocr_server_fastapi_v4',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ocr_server_fastapi_v4',
)
"""
    
    spec_path = os.path.join(base_dir, "fastapi_server.spec")
    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(spec_content)
        
    print(f"Spec file updated at {spec_path}")
    print("Starting build process (this may take 5-10 minutes)...")
    print("Please do not close the window even if it seems stuck.")
    
    # 3. 调用 PyInstaller
    # --noconfirm: 不询问覆盖
    # --clean: 清理缓存
    subprocess.check_call([
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--workpath", work_dir,
        "--distpath", dist_dir,
        spec_path
    ], cwd=base_dir)

    print("\nBuild completed!")
    print(f"Executable is located at: {os.path.join(dist_dir, 'ocr_server_fastapi_v4', 'ocr_server_fastapi_v4.exe')}")

    # 4. Create run_server.bat
    bat_content = r"""@echo off
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
"""
    bat_path = os.path.join(dist_dir, "run_server.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_content)
    print(f"Created startup script: {bat_path}")

    # 5. Create test_local_connectivity.py
    test_content = r"""import requests
import time
import sys

def test_local_health():
    url = "http://127.0.0.1:8000/ping"
    print(f"Checking {url}...")
    for i in range(10):
        try:
            resp = requests.get(url, timeout=5)
            print(f"Attempt {i+1}: Status Code: {resp.status_code}")
            if resp.status_code == 200:
                print("[SUCCESS] Server is responsive locally.")
                return True
        except Exception as e:
            print(f"Attempt {i+1}: Failed to connect: {e}")
        time.sleep(2)
    print("[FAILURE] Server did not respond after 10 attempts.")
    return False

if __name__ == "__main__":
    if test_local_health():
        sys.exit(0)
    else:
        sys.exit(1)
"""
    test_path = os.path.join(dist_dir, "test_local_connectivity.py")
    with open(test_path, "w", encoding="utf-8") as f:
        f.write(test_content)
    print(f"Created test script: {test_path}")

if __name__ == "__main__":
    main()
