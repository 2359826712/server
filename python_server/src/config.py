import os

class Config:
    DATA_DIR = "data"
    HTTP_PORT = 9097
    # Performance tuning for SQLite
    SQLITE_TIMEOUT = 10.0  # Seconds
    SQLITE_PRAGMA = [
        "PRAGMA journal_mode=WAL;",  # Write-Ahead Logging for concurrency
        "PRAGMA synchronous=NORMAL;", # Revert to NORMAL for safety + speed (WAL handles it well)
        "PRAGMA busy_timeout=5000;", # Wait up to 5s if locked
        "PRAGMA cache_size=-64000;", # 64MB cache
        "PRAGMA foreign_keys=ON;"
    ]
    
    def get_db_path(self, game_name: str) -> str:
        # Ensure data directory exists
        if not os.path.exists(self.DATA_DIR):
            os.makedirs(self.DATA_DIR, exist_ok=True)
        return os.path.join(self.DATA_DIR, f"{game_name}.db")

config = Config()
