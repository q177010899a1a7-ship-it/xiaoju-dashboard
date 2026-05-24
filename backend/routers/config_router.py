"""小居数据监控台 - 配置管理路由"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import config
from services.logger import logger

router = APIRouter()

DB_PATH = config.DATA_DIR / "config.db"

def _get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def _init_db():
    """初始化配置数据库"""
    conn = _get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS push_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT NOT NULL,
            error TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

# 初始化数据库
_init_db()

class ConfigSaveRequest(BaseModel):
    key: str
    value: str

class ConfigBulkSaveRequest(BaseModel):
    data: dict

# ========== API 端点 ==========

@router.get("/")
async def api_get_config():
    """API: 获取所有配置"""
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM config")
    rows = cursor.fetchall()
    conn.close()
    
    result = {}
    for row in rows:
        result[row["key"]] = row["value"]
    
    # 添加默认值
    defaults = {
        "refresh_interval": str(config.REFRESH_INTERVAL),
        "feishu_webhook": config.FEISHU_WEBHOOK,
        "wecom_webhook": config.WECOM_WEBHOOK,
        "openai_api_key": config.OPENAI_API_KEY,
        "morning_report_time": "08:00",
        "evening_report_time": "18:00",
        "push_enabled": "false",
        "modules": json.dumps(["stock", "us_stock", "metals", "commodity", "hot", "news", "github", "calendar", "horoscope", "report"]),
    }
    
    for k, v in defaults.items():
        if k not in result:
            result[k] = v
    
    return result

@router.post("/save")
async def api_save_config(req: ConfigSaveRequest):
    """API: 保存单个配置"""
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO config (key, value, updated_at) VALUES (?, ?, ?)",
        (req.key, req.value, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    logger.info(f"配置已更新: {req.key}")
    return {"success": True, "key": req.key, "value": req.value}

@router.post("/saveBulk")
async def api_save_bulk_config(req: ConfigBulkSaveRequest):
    """API: 批量保存配置"""
    conn = _get_db()
    cursor = conn.cursor()
    
    for key, value in req.data.items():
        cursor.execute(
            "INSERT OR REPLACE INTO config (key, value, updated_at) VALUES (?, ?, ?)",
            (key, str(value), datetime.now().isoformat())
        )
    
    conn.commit()
    conn.close()
    logger.info(f"批量配置已更新: {list(req.data.keys())}")
    return {"success": True, "keys": list(req.data.keys())}

@router.get("/pushHistory")
async def api_get_push_history(limit: int = 20):
    """API: 获取推送历史"""
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM push_history ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    return {"history": [dict(row) for row in rows]}

@router.get("/systemStatus")
async def api_get_system_status():
    """API: 获取系统状态"""
    from routers import stock, precious_metals, hot_search, news
    from services.cache import cache_service
    
    status = {
        "version": "1.1.0",
        "uptime": "运行中",
        "refresh_interval": config.REFRESH_INTERVAL,
        "cache": {
            "cn_stocks": cache_service.get("cn_stocks") is not None,
            "us_stocks": cache_service.get("us_stocks") is not None,
            "metals": cache_service.get("precious_metals") is not None,
            "commodities": cache_service.get("commodities") is not None,
            "hot": cache_service.get("weibo_hot") is not None,
            "news": cache_service.get("all_news") is not None,
        },
        "config": {
            "feishu_webhook": bool(config.FEISHU_WEBHOOK),
            "wecom_webhook": bool(config.WECOM_WEBHOOK),
            "openai_api_key": bool(config.OPENAI_API_KEY),
        }
    }
    
    return status
