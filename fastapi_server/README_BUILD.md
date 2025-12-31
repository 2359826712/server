# FastAPI Server Build Instructions

本文档说明如何将 FastAPI 服务器打包为独立的 Windows 可执行文件 (.exe)。

## 前置要求

1.  已安装 Python 3.8+
2.  已安装依赖项 (在 `fastapi_server` 目录下运行):
    ```bash
    pip install -r requirements.txt
    pip install pyinstaller
    ```

## 打包步骤

在 `fastapi_server` 目录下，运行提供的构建脚本：

```bash
python build.py
```

或者手动运行 PyInstaller 命令：

```bash
pyinstaller --onefile --name=fastapi_server --clean --noconfirm ^
    --hidden-import=uvicorn.logging ^
    --hidden-import=uvicorn.loops ^
    --hidden-import=uvicorn.loops.auto ^
    --hidden-import=uvicorn.protocols ^
    --hidden-import=uvicorn.protocols.http ^
    --hidden-import=uvicorn.protocols.http.auto ^
    --hidden-import=uvicorn.protocols.websockets ^
    --hidden-import=uvicorn.protocols.websockets.auto ^
    --hidden-import=uvicorn.lifespan ^
    --hidden-import=uvicorn.lifespan.on ^
    --hidden-import=pymysql ^
    app/main.py
```

## 输出产物

打包完成后，可执行文件将位于 `dist` 文件夹中：

-   `dist/fastapi_server.exe`: 独立的可执行程序。
-   `dist/.env`: 配置文件 (脚本会自动复制过去)。

## 部署说明

1.  将 `dist` 文件夹中的 `fastapi_server.exe` 和 `.env` 文件复制到目标机器的任意文件夹。
2.  修改 `.env` 文件中的数据库配置，确保目标机器可以连接到 MySQL 数据库。
3.  双击 `fastapi_server.exe` 运行。
4.  控制台窗口将显示启动日志，默认端口为 9091。

## 常见问题

**Q: 启动时报错 "ModuleNotFoundError"**
A: 这通常是因为某些库使用了动态导入，PyInstaller 没能自动检测到。请在 `build.py` 的 `--hidden-import` 列表中添加缺失的模块。

**Q: 数据库连接失败**
A: 请检查 `.env` 文件是否与 exe 在同一目录下，且配置正确。

**Q: 窗口一闪而过**
A: 在命令行 (CMD/PowerShell) 中运行 exe，可以查看具体的错误输出。
