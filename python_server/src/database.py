import sqlite3
import logging
import os
from .config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_connection(game_name: str):
    """Create a new database connection for a specific game."""
    db_path = config.get_db_path(game_name)
    # check_same_thread=False allows sharing connection across threads, 
    # BUT we must ensure serialized access (which we do via LockList).
    conn = sqlite3.connect(db_path, timeout=config.SQLITE_TIMEOUT, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Access columns by name
    
    # Apply performance pragmas
    for pragma in config.SQLITE_PRAGMA:
        conn.execute(pragma)
    
    return conn

def init_db():
    """Initialize the database directory."""
    if not os.path.exists(config.DATA_DIR):
        os.makedirs(config.DATA_DIR, exist_ok=True)
    logger.info(f"Database directory initialized at {config.DATA_DIR}")

def auto_migrate(game_name: str):
    """Create the game table if it doesn't exist."""
    
    table_sql = f"""
    CREATE TABLE IF NOT EXISTS "{game_name}" (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        online_time TEXT,
        game_name TEXT,
        account TEXT,
        b_zone TEXT,
        s_zone TEXT,
        rating INTEGER,
        last_talk_time1 TEXT DEFAULT '2000-01-01 00:00:00',
        last_talk_time2 TEXT DEFAULT '2000-01-01 00:00:00',
        last_talk_time3 TEXT DEFAULT '2000-01-01 00:00:00',
        last_talk_time4 TEXT DEFAULT '2000-01-01 00:00:00',
        last_talk_time5 TEXT DEFAULT '2000-01-01 00:00:00',
        last_talk_time6 TEXT DEFAULT '2000-01-01 00:00:00'
    );
    """
    
    indices_sql = [
        f'CREATE INDEX IF NOT EXISTS "idx_{game_name}_account" ON "{game_name}" (account);',
        f'CREATE INDEX IF NOT EXISTS "idx_{game_name}_zone" ON "{game_name}" (b_zone, s_zone);',
        f'CREATE INDEX IF NOT EXISTS "idx_{game_name}_online_time" ON "{game_name}" (online_time);'
    ]
    
    # Use a fresh connection for migration (rare operation)
    conn = get_connection(game_name)
    try:
        cursor = conn.cursor()
        cursor.execute(table_sql)
        for idx_sql in indices_sql:
            cursor.execute(idx_sql)
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed for {game_name}: {e}")
        raise e
    finally:
        conn.close()
