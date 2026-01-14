
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "OCR Server"
    API_V1_STR: str = "/api/v1"
    USE_GPU: bool = True
    GPU_ID: int = 0
    MAX_CONCURRENT_REQUESTS: int = 100
    OCR_LANG: str = "ch"
    
    class Config:
        case_sensitive = True

settings = Settings()
