import os
import struct
import subprocess
import sys


def _check_deps():
    missing = []
    for name in ["flask", "paddleocr", "paddle", "cv2", "numpy"]:
        try:
            __import__(name)
        except Exception:
            missing.append(name)
    return missing


def main():
    if struct.calcsize("P") * 8 != 64:
        print("需要 64 位 Python")
        sys.exit(1)

    os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")

    missing = _check_deps()
    if missing:
        print("缺少依赖: " + ", ".join(missing))
        print("建议安装: pip install -r requirements.txt")
        sys.exit(1)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    spec_path = os.path.join(base_dir, "ocr_server_remote.spec")

    spec_content = r"""# -*- mode: python ; coding: utf-8 -*-
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
"""

    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(spec_content)

    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            spec_path,
            "--clean",
            "--noconfirm",
            "--distpath",
            os.path.join(base_dir, "dist"),
            "--workpath",
            os.path.join(base_dir, "build"),
        ]
    )
    print("打包完成: dist/ocr_server_remote.exe")


if __name__ == "__main__":
    main()

