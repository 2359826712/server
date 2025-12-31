import os
import sys
from pydantic_settings import BaseSettings

def get_env_path():
    """
    Get the path to the .env file.
    It should be in the same directory as the executable (if frozen)
    or in the project root (if running from source).
    """
    if getattr(sys, 'frozen', False):
        # If frozen, the executable is the .exe file
        application_path = os.path.dirname(sys.executable)
    else:
        # If not frozen, standard python script
        # app/core/config.py -> app/core -> app -> root (fastapi_server)
        application_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    return os.path.join(application_path, ".env")

class Settings(BaseSettings):
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "root"
    MYSQL_DB: str = "fsjs_sql_server"
    MYSQL_CHARSET: str = "utf8mb4"
    
    HTTP_PORT: int = 9091

    class Config:
        env_file = get_env_path()
        env_file_encoding = 'utf-8'
        extra = "ignore"

settings = Settings()
