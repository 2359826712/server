
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api import endpoints
from app.core.config import settings
from app.core.ocr import OCREngine
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize OCR Engine
    logger.info("Starting up OCR Server...")
    try:
        OCREngine.get_instance()
    except Exception as e:
        logger.error(f"Failed to initialize OCR Engine: {e}")
    yield
    # Shutdown
    logger.info("Shutting down OCR Server...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    description="High-performance GPU-accelerated OCR Server"
)

# Include router at root for backward compatibility with /ocr
app.include_router(endpoints.router)

# Also include at /api/v1 for better structure
app.include_router(endpoints.router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
