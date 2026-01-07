# Python Database Server

This is a Python implementation of the database server, migrating from the original Go version. It uses SQLite as the storage engine and FastAPI for the HTTP server.

## Features
- **Compatible API**: Fully compatible with the Go version's HTTP API.
- **SQLite**: Local database storage with WAL mode for concurrency.
- **Thread Safety**: Implements per-game locking mechanisms.
- **Performance**: Optimized for low latency (<50ms) and high concurrency.

## Requirements
- Python 3.8+

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running

1. Start the server:
   ```bash
   python run.py
   ```
   Or on Windows, simply double-click `start.bat`.

2. The server listens on port **9096** by default.

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:9096/docs`
- ReDoc: `http://localhost:9096/redoc`

## Project Structure
- `src/`: Source code
  - `api.py`: HTTP route handlers
  - `config.py`: Configuration
  - `database.py`: SQLite connection and migration
  - `logic.py`: Core business logic and locking
  - `models.py`: Pydantic data models
- `run.py`: Entry point script
- `requirements.txt`: Python dependencies

## Performance Tuning
Configuration can be adjusted in `src/config.py`. The default SQLite PRAGMA settings are tuned for performance (WAL mode, synchronous=NORMAL).
