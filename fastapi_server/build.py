import PyInstaller.__main__
import os
import shutil
import sys

def build_executable():
    """
    使用 PyInstaller 打包 FastAPI 应用程序
    """
    # 获取脚本所在目录的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 切换工作目录到脚本所在目录，确保相对路径正确
    os.chdir(current_dir)
    
    # 定义应用程序名称
    app_name = "fastapi_server"
    
    # 定义入口文件
    entry_point = os.path.join("app", "main.py")
    
    # 检查入口文件是否存在
    if not os.path.exists(entry_point):
        print(f"Error: Entry point '{entry_point}' not found.")
        print(f"Current working directory: {os.getcwd()}")
        return

    # PyInstaller 参数配置
    args = [
        entry_point,                            # 脚本路径
        f'--name={app_name}',                   # 生成的可执行文件名称
        '--onefile',                            # 单文件模式
        '--clean',                              # 清理临时文件
        '--noconfirm',                          # 不确认覆盖
        
        # 隐藏导入 (FastAPI/Uvicorn/SQLAlchemy 可能需要的隐式依赖)
        '--hidden-import=uvicorn.logging',
        '--hidden-import=uvicorn.loops',
        '--hidden-import=uvicorn.loops.auto',
        '--hidden-import=uvicorn.protocols',
        '--hidden-import=uvicorn.protocols.http',
        '--hidden-import=uvicorn.protocols.http.auto',
        '--hidden-import=uvicorn.protocols.websockets',
        '--hidden-import=uvicorn.protocols.websockets.auto',
        '--hidden-import=uvicorn.lifespan',
        '--hidden-import=uvicorn.lifespan.on',
        '--hidden-import=pymysql',
        '--hidden-import=tzdata',
        
        # 排除不必要的包，减少 "module not found" 警告
        '--exclude-module=tkinter',
        '--exclude-module=unittest',
        '--exclude-module=email.test',
        '--exclude-module=pydoc',
        '--exclude-module=pdb',
        # 排除 SQLAlchemy 可能尝试导入的其他数据库驱动
        '--exclude-module=psycopg2',      # PostgreSQL
        '--exclude-module=MySQLdb',       # Old MySQL driver
        '--exclude-module=cx_Oracle',     # Oracle
        '--exclude-module=pysqlite2',     # Old SQLite
        '--exclude-module=sqlite3',       # SQLite (如果不使用)
        '--exclude-module=pg8000',        # PostgreSQL
        '--exclude-module=pyodbc',        # MSSQL/ODBC
        
        # 路径配置
        '--distpath=.',                         # 输出目录 (当前目录)
        '--workpath=build',                     # 临时工作目录
        '--specpath=.',                         # spec文件生成位置
    ]
    
    print(f"Starting build process in {current_dir}...")
    print(f"Command: pyinstaller {' '.join(args)}")
    
    try:
        PyInstaller.__main__.run(args)
        print("\nBuild completed successfully!")
        
        # .env 不需要复制，因为它已经在当前目录（fastapi_server）中，
        # 且 exe 也生成在当前目录，运行时会直接读取。
            
    except Exception as e:
        print(f"\nAn error occurred during build: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_executable()
