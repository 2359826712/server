# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import os

block_cipher = None

datas = []
binaries = []
hiddenimports = []

for pkg in [
    "flask",
    "werkzeug",
    "jinja2",
    "itsdangerous",
    "click",
    "markupsafe",
    "numpy",
    "cv2",
    "paddle",
    "paddleocr",
    "paddlex",
    "shapely",
    "pyclipper",
    "skimage",
    "lxml",
    "scikit_learn",
    "sentencepiece",
    "tokenizers",
    "tiktoken",
    "regex",
    "ftfy",
    "openpyxl",
    "premailer",
    "cssselect",
    "cssutils",
    "cachetools",
    "einops",
]:
    try:
        tmp_ret = collect_all(pkg)
        datas += tmp_ret[0]
        binaries += tmp_ret[1]
        hiddenimports += tmp_ret[2]
    except Exception:
        pass

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
    ["server.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="ocr_server_remote",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
