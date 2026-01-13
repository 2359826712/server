# -*- mode: python ; coding: utf-8 -*-
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
]

# 仅对 Paddle 相关库进行完整收集，因为它们有很多动态加载的资源
for pkg in [
    "paddle",
    "paddleocr",
    "paddlex",
    "pyclipper",
    "shapely",
    "nvidia.cudnn",
    "nvidia.cublas",
    "websockets",
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
    "paddle", "paddlepaddle", "paddlepaddle-gpu", "paddleocr", "paddlex", 
    # Prefer dynamically including whichever CUDA runtime is installed.
    # Try cu12 family first (ignore if not installed), then cu11 family.
    "nvidia-cuda-runtime-cu12", "nvidia-cudnn-cu12", "nvidia-cublas-cu12",
    "nvidia-cufft-cu12", "nvidia-curand-cu12", "nvidia-cusolver-cu12",
    "nvidia-cusparse-cu12", "nvidia-nvjitlink-cu12",
    "nvidia-cuda-runtime-cu11", "nvidia-cudnn-cu11", "nvidia-cublas-cu11",
    "nvidia-cufft-cu11", "nvidia-curand-cu11", "nvidia-cusolver-cu11",
    "nvidia-cusparse-cu11", "nvidia-nvjitlink-cu11",
    "pandas", "scipy", "sklearn", "fastapi", "uvicorn",
    "imagesize", "opencv-contrib-python", "pyclipper", "pypdfium2", "python-bidi", "shapely",
    "einops", "ftfy", "Jinja2", "lxml", "openpyxl", "premailer", "regex", "safetensors",
    "sentencepiece", "tiktoken", "tokenizers",
    # Paddlex base requirements
    "aistudio-sdk", "chardet", "colorlog", "filelock", "huggingface-hub", 
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
