import threading
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from .models import BaseInfo, QueryReq
from .database import get_connection, auto_migrate

logger = logging.getLogger(__name__)

class LockList:
    def __init__(self):
        self._locks = {}
        self._global_lock = threading.Lock()

    def get_lock(self, game_name: str) -> threading.Lock:
        with self._global_lock:
            if game_name not in self._locks:
                self._locks[game_name] = threading.Lock()
            return self._locks[game_name]

class LogicService:
    def __init__(self):
        self.locker = LockList()
        self._conns: Dict[str, sqlite3.Connection] = {}
        self._conn_lock = threading.Lock()

    def _get_connection_pooled(self, game_name: str) -> sqlite3.Connection:
        # Check if we already have a connection for this game
        # Note: Connections are not thread-safe by default, but we use them inside the game lock
        # so only one thread accesses a game's connection at a time.
        # However, checking self._conns needs protection.
        
        # Optimization: We can use double-checked locking or just lock for the dict access.
        # But wait, self._conns access itself needs a lock.
        # Once we have the connection, we use it under the Game Lock.
        
        conn = None
        with self._conn_lock:
            conn = self._conns.get(game_name)
            if conn is None:
                conn = get_connection(game_name)
                self._conns[game_name] = conn
        return conn

    def _get_time_str(self, dt: Optional[datetime] = None) -> str:
        if dt is None:
            dt = datetime.now()
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def _get_talk_channel_field(self, channel: int) -> str:
        if 1 <= channel <= 6:
            return f"last_talk_time{channel}"
        raise ValueError(f"喊话通道{channel}暂无")

    def new_game(self, game_name: str):
        lock = self.locker.get_lock(game_name)
        with lock:
            auto_migrate(game_name)

    def insert(self, base: BaseInfo):
        # 1. Acquire Lock for the game
        lock = self.locker.get_lock(base.GameName)
        with lock:
            # 2. Get (or create) connection (safe to use inside lock)
            conn = self._get_connection_pooled(base.GameName)
            try:
                cursor = conn.cursor()
                # Check if exists
                cursor.execute(f'SELECT id FROM "{base.GameName}" WHERE account = ?', (base.Account,))
                row = cursor.fetchone()
                
                now_str = self._get_time_str()
                
                if row:
                    # Update
                    cursor.execute(f'''
                        UPDATE "{base.GameName}" 
                        SET b_zone = ?, s_zone = ?, rating = ?, online_time = ?
                        WHERE account = ?
                    ''', (base.BZone, base.SZone, base.Rating, now_str, base.Account))
                else:
                    # Insert
                    cursor.execute(f'''
                        INSERT INTO "{base.GameName}" (game_name, account, b_zone, s_zone, rating, online_time, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (base.GameName, base.Account, base.BZone, base.SZone, base.Rating, now_str, now_str))
                conn.commit()
            except Exception as e:
                # We don't close pooled connection, but we might want to rollback on error?
                # SQLite automatically rolls back on close, but we aren't closing.
                # So explicit rollback is good practice if we want to reuse it.
                conn.rollback()
                raise e

    def update(self, base: BaseInfo):
        lock = self.locker.get_lock(base.GameName)
        with lock:
            conn = self._get_connection_pooled(base.GameName)
            try:
                now_str = self._get_time_str()
                cursor = conn.cursor()
                cursor.execute(f'''
                    UPDATE "{base.GameName}" 
                    SET b_zone = ?, s_zone = ?, rating = ?, online_time = ?
                    WHERE account = ?
                ''', (base.BZone, base.SZone, base.Rating, now_str, base.Account))
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e

    def query(self, req: QueryReq) -> List[dict]:
        lock = self.locker.get_lock(req.GameName)
        with lock:
            conn = self._get_connection_pooled(req.GameName)
            try:
                cursor = conn.cursor()
                query_sql = f'SELECT * FROM "{req.GameName}" WHERE 1=1'
                params = []

                if req.Account:
                    query_sql += " AND account = ?"
                    params.append(req.Account)
                if req.BZone:
                    query_sql += " AND b_zone = ?"
                    params.append(req.BZone)
                if req.SZone:
                    query_sql += " AND s_zone = ?"
                    params.append(req.SZone)
                if req.Rating and req.Rating != 0:
                    query_sql += " AND rating = ?"
                    params.append(req.Rating)
                
                if req.OnlineDuration > 0:
                    target_time = datetime.now() - timedelta(minutes=req.OnlineDuration)
                    target_time_str = self._get_time_str(target_time)
                    # online_time > target_time (User was online recently)
                    query_sql += " AND online_time > ?"
                    params.append(target_time_str)

                talk_field = None
                if req.TalkChannel > 0:
                    talk_field = self._get_talk_channel_field(req.TalkChannel)
                    target_time = datetime.now() - timedelta(minutes=req.OnlineDuration)
                    target_time_str = self._get_time_str(target_time)
                    # last_talk_time < target_time (User hasn't talked recently)
                    query_sql += f" AND {talk_field} < ?"
                    params.append(target_time_str)

                cnt = req.Cnt if req.Cnt > 0 else 1
                query_sql += " LIMIT ?"
                params.append(cnt)

                cursor.execute(query_sql, params)
                rows = cursor.fetchall()
                
                results = []
                ids_to_update = []
                for row in rows:
                    results.append(dict(row))
                    ids_to_update.append(row['id'])

                # Update talk time for returned rows if channel specified
                if talk_field and ids_to_update:
                    now_str = self._get_time_str()
                    placeholders = ','.join(['?'] * len(ids_to_update))
                    update_sql = f'UPDATE "{req.GameName}" SET {talk_field} = ? WHERE id IN ({placeholders})'
                    update_params = [now_str] + ids_to_update
                    cursor.execute(update_sql, update_params)
                    conn.commit()

                return results
            except Exception as e:
                # Query usually doesn't need rollback unless update failed
                conn.rollback()
                raise e

    def clear_talk_time(self, game_name: str, channel: int):
        lock = self.locker.get_lock(game_name)
        with lock:
            conn = self._get_connection_pooled(game_name)
            try:
                talk_field = self._get_talk_channel_field(channel)
                cursor = conn.cursor()
                cursor.execute(f'UPDATE "{game_name}" SET {talk_field} = ?', ('2000-01-01 00:00:00',))
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e

logic_service = LogicService()
