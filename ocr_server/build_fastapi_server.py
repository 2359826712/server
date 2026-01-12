import os
import struct
import subprocess
import sys

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
    use_gpu = os.environ.get("OCR_USE_GPU", "True").lower() == "true"
    print(f"Build Configuration: OCR_USE_GPU={use_gpu}")
    
    try:
        import paddle
        is_compiled_with_cuda = paddle.is_compiled_with_cuda()
        print(f"Current PaddlePaddle compiled with CUDA: {is_compiled_with_cuda}")
        
        if use_gpu and not is_compiled_with_cuda:
            print("WARNING: OCR_USE_GPU=True but paddlepaddle is CPU version!")
            print("Suggest installing GPU version:")
            print("pip uninstall paddlepaddle")
            print("pip install -r requirements-gpu.txt")
            # Ask user if they want to continue? Or just warn.
            print("Continuing build, but runtime might fail if GPU is expected...")
            # sys.exit(1) # Uncomment to enforce
            
        if not use_gpu and is_compiled_with_cuda:
            print("NOTE: OCR_USE_GPU=False but paddlepaddle-gpu is installed.")
            print("This is generally fine (can run on CPU), but package size might be larger.")
            
    except ImportError:
        print("PaddlePaddle not found!")
        sys.exit(1)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    
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
]

# 仅对 Paddle 相关库进行完整收集，因为它们有很多动态加载的资源
for pkg in [
    "paddle",
    "paddleocr",
    "paddlex",
    "pyclipper",
    "shapely",
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
    "nvidia-cuda-runtime-cu12", "nvidia-cudnn-cu12", "nvidia-cublas-cu12",
    "nvidia-cufft-cu12", "nvidia-curand-cu12", "nvidia-cusolver-cu12",
    "nvidia-cusparse-cu12", "nvidia-nvjitlink-cu12",
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
    name='ocr_server_fastapi',
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
    name='ocr_server_fastapi',
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
    subprocess.check_call([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", spec_path], cwd=base_dir)
    
    print("\nBuild completed!")
    print(f"Executable is located at: {os.path.join(base_dir, 'dist', 'ocr_server_fastapi', 'ocr_server_fastapi.exe')}")

if __name__ == "__main__":
    main()
