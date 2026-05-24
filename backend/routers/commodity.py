"""小居数据监控台 - 大宗商品路由"""
import re
import httpx
from fastapi import APIRouter
from services.cache import cache_service
from services.logger import logger
import config

router = APIRouter()

_latest_data: dict = {}

SINA_COMMODITY_URL = "https://hq.sinajs.cn/list={}"


async def fetch_commodities() -> dict:
    """获取大宗商品数据（stale-while-revalidate）"""
    global _latest_data
    
    # 1. 立即返回缓存
    cached = cache_service.get("commodities")
    if cached:
        _latest_data = cached
    
    # 2. 检查是否需要后台刷新
    need_fetch = False
    refresh_time = cache_service.get_refresh_time("commodities")
    if refresh_time is None:
        need_fetch = True
    else:
        from datetime import datetime
        minutes_since_refresh = (datetime.now() - datetime.fromtimestamp(refresh_time)).total_seconds() / 60
        if minutes_since_refresh > 55:
            need_fetch = True
    
    # 3. 后台异步刷新
    if need_fetch and not cache_service.is_locked("commodities"):
        cache_service.lock("commodities")
        import asyncio
        asyncio.create_task(_background_refresh_commodities())
    
    return _latest_data if _latest_data else {}


async def _background_refresh_commodities():
    """后台刷新大宗商品数据"""
    global _latest_data
    try:
        symbols = list(config.COMMODITY_CODES.keys())
        symbols_param = ",".join(symbols)
        url = SINA_COMMODITY_URL.format(symbols_param)
        
        headers = {
            "Referer": "https://finance.sina.com.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            resp.encoding = 'gbk'
            text = resp.text
            
            results = {}
            for line in text.strip().split('\n'):
                if 'hq_str' not in line:
                    continue
                code_match = re.search(r'hq_str_(\w+)=', line)
                if not code_match:
                    continue
                code = code_match.group(1)
                data = _parse_commodity_data(line, code)
                if data:
                    results[code] = data
            
            if results:
                _latest_data = results
                cache_service.set("commodities", results, ttl=3600)
                logger.info(f"[后台刷新] 大宗商品数据更新成功: {list(results.keys())}")
                
    except Exception as e:
        logger.error(f"[后台刷新] 大宗商品数据刷新失败: {e}")
    finally:
        cache_service.unlock("commodities")


def _parse_commodity_data(raw: str, code: str) -> dict | None:
    """解析大宗商品数据
    
    新浪商品 hq_str 格式:
    name,time,open,close,high,low,settle,?,volume,open_interest,exchange,market,name2,date,
    ?,?,?,?,settle2,?,...,high2,low2,...
    
    字段说明:
    - 0: 名称 (如 "沪铜连续")
    - 1: 时间戳
    - 2: 开盘价
    - 3: 收盘价（当前价）
    - 4: 最高价
    - 5: 最低价
    - 6: 结算价（昨收）
    - 8: 成交量
    - 14: 交易所
    - 15: 品种名
    - 16: 日期
    - 22: 主力合约最高价
    - 23: 主力合约最低价
    
    涨跌幅 = (收盘价 - 结算价) / 结算价 * 100
    """
    try:
        match = re.search(r'"([^"]*)"', raw)
        if not match:
            return None
        fields = match.group(1).split(',')
        if len(fields) < 10:
            return None
        
        name = fields[16] if len(fields) > 16 else fields[0]  # 品种全名(如"沪铜")
        # 计算涨跌
        close = _safe_float(fields[3])   # 当前价/收盘价
        settle = _safe_float(fields[6])   # 结算价/昨收
        
        if settle > 0 and close > 0:
            pct = (close - settle) / settle * 100
            change = close - settle
        else:
            pct = 0.0
            change = 0.0
        
        return {
            "name": name,
            "symbol": code,
            "price": close,
            "previousClose": settle,
            "change": round(change, 2),
            "pct": round(pct, 2),
            "high": _safe_float(fields[4]),
            "low": _safe_float(fields[5]),
            "open": _safe_float(fields[2]),
            "volume": _safe_float(fields[8]),
            "unit": config.COMMODITY_CODES.get(code, {}).get("unit", ""),
        }
    except Exception as e:
        logger.error(f"解析大宗商品 {code} 数据失败: {e}")
        return None


def _safe_float(value: str) -> float:
    """安全转换浮点数"""
    try:
        if not value or value == '-' or value == '':
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def get_cached_data() -> dict:
    """获取缓存的大宗商品数据"""
    return _latest_data


@router.get("")
async def get_commodities():
    """API: 获取大宗商品数据"""
    return await fetch_commodities()
