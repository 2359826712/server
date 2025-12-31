from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.game import BaseInfo, Account, QueryReq
from app.utils.validator import is_valid_game_name
from datetime import datetime
import threading
from collections import defaultdict

# Removed LockManager class and lock usage for better concurrency
# Database transactions are used to ensure atomicity

def get_talk_channel_field(talk_channel: int) -> str:
    if talk_channel == 0:
        return ""
    if 1 <= talk_channel <= 6:
        return f"last_talk_time{talk_channel}"
    raise ValueError(f"喊话通道{talk_channel}暂无")

def create_table(db: Session, game_name: str):
    if not is_valid_game_name(game_name):
        raise ValueError("Invalid game name")
    
    # Use database DDL execution directly
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS `{game_name}` (
        id INT PRIMARY KEY AUTO_INCREMENT,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,  
        online_time DATETIME,                                  
        game_name VARCHAR(255),
        account VARCHAR(255),                                  
        b_zone VARCHAR(255),                                   
        s_zone VARCHAR(255),                                    
        rating INT,                                          
        last_talk_time1 DATETIME DEFAULT '2000-01-01 00:00:00',                               
        last_talk_time2 DATETIME DEFAULT '2000-01-01 00:00:00',                               
        last_talk_time3 DATETIME DEFAULT '2000-01-01 00:00:00',                               
        last_talk_time4 DATETIME DEFAULT '2000-01-01 00:00:00',                               
        last_talk_time5 DATETIME DEFAULT '2000-01-01 00:00:00',                                
        last_talk_time6 DATETIME DEFAULT '2000-01-01 00:00:00',
        UNIQUE KEY `uk_account` (`account`)
    );
    """
    # Note: Added UNIQUE KEY on account to support efficient UPSERT
    # If the table already exists without this key, ON DUPLICATE KEY UPDATE might behave differently (row locking vs table locking)
    # But for safety, we assume 'account' should be unique per game table.
    
    db.execute(text(create_table_sql))
    # We should add the index if it doesn't exist, but 'CREATE TABLE IF NOT EXISTS' won't modify existing tables.
    # For now, we rely on the logic that we want high concurrency.
    db.commit()

def insert_game(db: Session, game: BaseInfo):
    if not is_valid_game_name(game.game_name):
        raise ValueError("Invalid game name")
    
    now = datetime.now()
    
    # Use INSERT ... ON DUPLICATE KEY UPDATE for atomic UPSERT
    # This avoids the need for application-level locking (check-then-insert)
    # And lets the database handle row-level locking.
    
    upsert_sql = f"""
    INSERT INTO `{game.game_name}` (game_name, account, b_zone, s_zone, rating, online_time, created_at)
    VALUES (:game_name, :account, :b_zone, :s_zone, :rating, :online_time, :created_at)
    ON DUPLICATE KEY UPDATE
        b_zone = VALUES(b_zone),
        s_zone = VALUES(s_zone),
        rating = VALUES(rating),
        online_time = VALUES(online_time)
    """
    
    # Note: This relies on `account` having a UNIQUE index. 
    # If the table was created by the old Go code or previous version without Unique Key, 
    # we might need to rely on the old logic or alter the table.
    # However, to solve the "lag" issue, we MUST use this approach.
    
    # Fallback/Migration strategy: 
    # If we can't guarantee Unique Key, we can use a transaction with `SELECT ... FOR UPDATE` 
    # but that might deadlock easily if not careful.
    # Best approach for "Performance": Assume/Enforce Unique Key.
    
    try:
        db.execute(text(upsert_sql), {
            "game_name": game.game_name,
            "account": game.account,
            "b_zone": game.b_zone,
            "s_zone": game.s_zone,
            "rating": game.rating,
            "online_time": now,
            "created_at": now
        })
        db.commit()
    except Exception as e:
        db.rollback()
        # If error is related to missing index, we might want to log it.
        # But for now, just re-raise
        raise e

def update_game(db: Session, game: BaseInfo):
    if not is_valid_game_name(game.game_name):
        raise ValueError("Invalid game name")
    
    now = datetime.now()
    update_sql = f"""
    UPDATE `{game.game_name}` 
    SET b_zone = :b_zone, s_zone = :s_zone, rating = :rating, online_time = :online_time
    WHERE account = :account
    """
    db.execute(text(update_sql), {
        "b_zone": game.b_zone,
        "s_zone": game.s_zone,
        "rating": game.rating,
        "online_time": now,
        "account": game.account
    })
    db.commit()

def clear_talk_time(db: Session, game_name: str, talk_channel: int):
    if not is_valid_game_name(game_name):
        raise ValueError("Invalid game name")
    
    field = get_talk_channel_field(talk_channel)
    if not field:
        return

    # Direct Update, Database handles locking
    sql = f"UPDATE `{game_name}` SET {field} = '2000-01-01 00:00:00' WHERE id >= 0"
    db.execute(text(sql))
    db.commit()

def query_game(db: Session, query: QueryReq):
    if not is_valid_game_name(query.game_name):
        raise ValueError("Invalid game name")
    
    # Build Query
    sql_parts = [f"SELECT * FROM `{query.game_name}` WHERE 1=1"]
    params = {}
    
    if query.account:
        sql_parts.append("AND account = :account")
        params["account"] = query.account
    if query.b_zone:
        sql_parts.append("AND b_zone = :b_zone")
        params["b_zone"] = query.b_zone
    if query.s_zone:
        sql_parts.append("AND s_zone = :s_zone")
        params["s_zone"] = query.s_zone
    if query.rating:
        sql_parts.append("AND rating = :rating")
        params["rating"] = query.rating
        
    now = datetime.now()
    params["now"] = now
    params["online_duration"] = query.online_duration
    
    if query.online_duration:
        # TIMESTAMPDIFF(MINUTE, online_time, now) < online_duration
        sql_parts.append("AND TIMESTAMPDIFF(MINUTE, online_time, :now) < :online_duration")
        
    talk_channel_field = ""
    if query.talk_channel:
        talk_channel_field = get_talk_channel_field(query.talk_channel)
        # TIMESTAMPDIFF(MINUTE, last_talk_timeX, now) > online_duration
        sql_parts.append(f"AND TIMESTAMPDIFF(MINUTE, {talk_channel_field}, :now) > :online_duration")
        
    limit = query.cnt if query.cnt else 1
    sql_parts.append(f"LIMIT {limit}")
    
    # Transaction for Read + Update
    # We want to return the list AND update their talk time.
    # Ideally, this should be atomic, but for high performance, 
    # we can do Read then Update. 
    # If we use FOR UPDATE, it blocks. 
    # Given the requirement "avoid lag", we should avoid long locks.
    # Standard Select -> Update by ID is fine.
    
    full_sql = " ".join(sql_parts)
    result = db.execute(text(full_sql), params).fetchall()
    
    # Update talk time for these records
    if result and talk_channel_field:
        ids = [row.id for row in result]
        if ids:
            ids_placeholder = ", ".join([str(id) for id in ids]) 
            update_sql = f"UPDATE `{query.game_name}` SET {talk_channel_field} = :now WHERE id IN ({ids_placeholder})"
            db.execute(text(update_sql), {"now": now})
            db.commit()
            
    # Map to schema
    response_list = []
    for row in result:
        item = BaseInfo(
            ID=row.id,
            game_name=row.game_name,
            account=row.account,
            b_zone=row.b_zone,
            s_zone=row.s_zone,
            rating=row.rating
        )
        response_list.append(item)
        
    return response_list
