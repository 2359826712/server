# -*- coding: utf-8 -*-
import os
import sys
import subprocess

# 检查依赖库
try:
    import flask
    import paddleocr
    import paddle
except ImportError as e:
    print(f"\n{'!'*50}")
    print(f"错误: 缺少必要的依赖库: {e.name}")
    print("请确保你在 64位 Python 环境下，并运行以下命令安装依赖：")
    print("pip install flask paddlepaddle paddleocr")
    print(f"{'!'*50}\n")
    sys.exit(1)

print("正在生成 ocr_server.spec 文件...")

# 生成 spec 文件内容
spec_content = r"""# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

# 收集核心库及 PaddleX OCR 额外依赖的资源
# 注意：不收集 paddle 本身，避免 libpaddle.pyd 冲突
for pkg in [
    'paddleocr',
    'paddlex',
    'cv2',
    'shapely',
    'pyclipper',
    'skimage',
    # PaddleX OCR extras 依赖
    'lxml',
    'scikit_learn',
    'sentencepiece',
    'tokenizers',
    'tiktoken',
    'regex',
    'ftfy',
    'openpyxl',
    'premailer',
    'cssselect',
    'cssutils',
    'cachetools',
    'einops',
]:
    try:
        tmp_ret = collect_all(pkg)
        datas += tmp_ret[0]
        binaries += tmp_ret[1]
        hiddenimports += tmp_ret[2]
    except Exception as e:
        print(f"Warning: collect_all({pkg}) failed: {e}")

block_cipher = None

# 手动添加 paddle.libs 中的所有 DLL
import paddle
paddle_libs_path = os.path.join(os.path.dirname(paddle.__file__), "libs")
if os.path.exists(paddle_libs_path):
    for file in os.listdir(paddle_libs_path):
        if file.endswith(".dll"):
            src = os.path.join(paddle_libs_path, file)
            binaries.append((src, "."))
            print(f"Adding paddle DLL: {src}")

a = Analysis(
    ['ocr_server_other/server.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'PIL.ImageTk'], # 排除不需要的重型库
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
    name='ocr_server',
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
    name='ocr_server',
)
"""

with open("ocr_server.spec", "w", encoding="utf-8") as f:
    f.write(spec_content)

print("spec 文件生成完毕。开始调用 PyInstaller...")

# 调用 PyInstaller 运行 spec 文件
try:
    subprocess.check_call([sys.executable, "-m", "PyInstaller", "ocr_server.spec", "--clean", "--noconfirm"])
    print("\n打包成功！ocr_server.exe 已生成。")
except subprocess.CalledProcessError as e:
    print(f"\n打包失败，错误代码: {e.returncode}")
    sys.exit(1)
