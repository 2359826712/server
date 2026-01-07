import uvicorn
from src.config import config

if __name__ == "__main__":
    # Increase workers to handle concurrency better
    print(f"Starting server on port {config.HTTP_PORT} with 4 workers...")
    uvicorn.run("src.main:app", host="0.0.0.0", port=config.HTTP_PORT, reload=False, workers=4)
