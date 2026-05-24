"""小居数据监控台 - 缓存服务"""
import time
import json
import sqlite3
from typing import Any, Optional
from pathlib import Path
import config

# 全局缓存时间记录（供 API 响应头使用）
_cache_refresh_time: dict[str, float] = {}

class CacheService:
    def __init__(self):
        self._memory_cache: dict[str, tuple[float, Any]] = {}
        self._db_path = config.CACHE_DIR
        self._lock_cache: dict[str, bool] = {}  # 防止同一 key 并发刷新
        
    def get(self, key: str) -> Optional[Any]:
        """获取缓存，优先内存其次SQLite"""
        # 优先检查内存
        if key in self._memory_cache:
            expire_at, value = self._memory_cache[key]
            if time.time() < expire_at:
                return value
            else:
                del self._memory_cache[key]
        
        # 检查SQLite
        try:
            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value, expire_at FROM cache WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            conn.close()
            
            if row:
                value, expire_at = row
                if time.time() < expire_at:
                    # 回填内存
                    self._memory_cache[key] = (expire_at, json.loads(value))
                    return json.loads(value)
                else:
                    self._delete_from_db(key)
        except Exception:
            pass
        
        return None
    
    def get_with_metadata(self, key: str) -> tuple[Optional[Any], Optional[float]]:
        """获取缓存同时返回刷新时间（秒级时间戳），无缓存返回 (None, None)"""
        value = self.get(key)
        refresh_time = _cache_refresh_time.get(key)
        return value, refresh_time
    
    def set(self, key: str, value: Any, ttl: int = None):
        """设置缓存并更新刷新时间"""
        ttl = ttl or config.CACHE_TTL
        expire_at = time.time() + ttl
        
        # 写入内存
        self._memory_cache[key] = (expire_at, value)
        # 记录刷新时间
        _cache_refresh_time[key] = time.time()
        
        # 写入SQLite
        try:
            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expire_at REAL NOT NULL
                )
            """)
            cursor.execute(
                "INSERT OR REPLACE INTO cache (key, value, expire_at) VALUES (?, ?, ?)",
                (key, json.dumps(value), expire_at)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass
    
    def is_locked(self, key: str) -> bool:
        """检查某 key 是否正在刷新中（防止并发刷新）"""
        return self._lock_cache.get(key, False)
    
    def lock(self, key: str):
        """加锁"""
        self._lock_cache[key] = True
    
    def unlock(self, key: str):
        """解锁"""
        self._lock_cache[key] = False
    
    def get_refresh_time(self, key: str) -> Optional[float]:
        """获取某 key 的刷新时间"""
        return _cache_refresh_time.get(key)
    
    def _delete_from_db(self, key: str):
        try:
            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()
            conn.close()
        except Exception:
            pass
    
    def clear_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        
        # 清理内存
        expired_keys = [k for k, (exp, _) in self._memory_cache.items() if current_time >= exp]
        for k in expired_keys:
            del self._memory_cache[k]
        
        # 清理SQLite
        try:
            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cache WHERE expire_at < ?", (current_time,))
            conn.commit()
            conn.close()
        except Exception:
            pass

cache_service = CacheService()
