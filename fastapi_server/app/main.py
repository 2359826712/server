import uvicorn
from fastapi import FastAPI
from sqlalchemy import text, create_engine
from contextlib import asynccontextmanager
from app.api import endpoints
from app.core.config import settings
from app.core.database import engine
import sys

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: 1. Try to create database if not exists
    print("\n" + "="*40)
    print(f"正在检查/初始化数据库 '{settings.MYSQL_DB}' ...")
    
    try:
        # Construct URL without database name to connect to MySQL server directly
        # Format: mysql+pymysql://user:password@host:port/?charset=utf8mb4
        server_url = f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/?charset={settings.MYSQL_CHARSET}"
        
        # Use isolation_level="AUTOCOMMIT" for DDL operations like CREATE DATABASE
        temp_engine = create_engine(server_url, isolation_level="AUTOCOMMIT")
        
        with temp_engine.connect() as conn:
            # Create database if not exists
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{settings.MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"))
            
        print(f"✅  数据库初始化完成 (Database Initialization Complete)")
        temp_engine.dispose()
    except Exception as e:
        print(f"⚠️  自动创建数据库失败 (Failed to create database automatically)")
        print(f"    Error: {e}")
        print("    尝试直接连接...")

    # Startup: 2. Check connection to the specific database
    print("正在尝试连接数据库... (Connecting to Database...)")
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("✅  数据库连接成功! (Database Connection Successful)")
        print(f"    Host: {settings.MYSQL_HOST}")
        print(f"    Port: {settings.MYSQL_PORT}")
        print(f"    DB:   {settings.MYSQL_DB}")
    except Exception as e:
        print("❌  数据库连接失败! (Database Connection Failed)")
        print(f"    Error: {e}")
        print("    请检查 .env 文件配置是否正确，及 MySQL 服务是否启动")
    print("="*40 + "\n")
    
    yield
    
    print("Server shutting down...")

app = FastAPI(title="FSJS SQL Server", lifespan=lifespan)

app.include_router(endpoints.router)

if __name__ == "__main__":
    # When running as a frozen app (exe), reload must be False
    # and we should pass the app object directly instead of import string
    # Use 0.0.0.0 to allow external access if needed, or stick to what config implies
    uvicorn.run(app, host="0.0.0.0", port=settings.HTTP_PORT, reload=False)
