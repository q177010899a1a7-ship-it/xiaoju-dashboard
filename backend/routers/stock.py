"""小居数据监控台 - A股数据路由"""
import re
import httpx
from typing import Optional
from fastapi import APIRouter
import config
from services.cache import cache_service
from services.logger import logger

router = APIRouter()

# 内存缓存最新数据
_latest_data: dict = {}

def _parse_sina_stock(raw: str, code: str) -> Optional[dict]:
    """解析新浪财经股票数据
    
    新浪 hq_str 格式: name,price,change,pct,volume,amount
    - price: 现价
    - change: 涨跌额
    - pct: 涨跌幅（百分比数值，如 0.63 表示 0.63%）
    - volume: 成交量（手）
    - amount: 成交额（万元）
    """
    try:
        # 格式: var hq_str_s_sh000001="name,price,change,pct,volume,amount"
        match = re.search(r'"([^"]*)"', raw)
        if not match:
            return None
        fields = match.group(1).split(',')
        if len(fields) < 6:
            return None
        
        name = fields[0]                          # 名称
        price = _safe_float(fields[1])           # 现价
        change = _safe_float(fields[2])         # 涨跌额
        pct = _safe_float(fields[3])             # 涨跌幅百分比（如 0.63）
        volume = _safe_float(fields[4])          # 成交量（手）
        amount = _safe_float(fields[5])         # 成交额（万元）
        
        # amplitude/high/low/open/close/time 在此接口中未返回，设为0
        amplitude = 0.0
        high = 0.0
        low = 0.0
        open_price = 0.0
        close = 0.0
        time_str = ""
        
        return {
            "name": name,
            "price": price,
            "change": change,
            "pct": pct,
            "volume": volume,
            "amount": amount,
            "amplitude": amplitude,
            "high": high,
            "low": low,
            "open": open_price,
            "close": close,
            "time": time_str,
        }
    except Exception as e:
        logger.error(f"解析股票数据失败: {e}")
        return None


def _safe_float(value: str) -> float:
    """安全转换浮点数"""
    try:
        if not value or value == '-' or value == '':
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0


async def fetch_cn_stocks() -> dict:
    """获取A股数据 - 使用新浪实时接口（stale-while-revalidate）"""
    global _latest_data
    
    # 1. 立即返回缓存（秒响）
    cached = cache_service.get("cn_stocks")
    if cached:
        _latest_data = cached
    
    # 2. 检查是否需要后台刷新：条件为无缓存 或 距整点超过70分钟
    need_fetch = False
    refresh_time = cache_service.get_refresh_time("cn_stocks")
    if refresh_time is None:
        # 从未刷新过，必须获取
        need_fetch = True
    else:
        from datetime import datetime
        now = datetime.now()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        last_hour = datetime.fromtimestamp(refresh_time).replace(minute=0, second=0, microsecond=0)
        minutes_since_last_hour = (now - current_hour).total_seconds() / 60
        # 如果当前处于整点后0-50分钟：用上一整点数据；50-60分钟：触发刷新
        # 简化为：距上次刷新超过55分钟 且 距上一整点超过60分钟
        minutes_since_refresh = (now - datetime.fromtimestamp(refresh_time)).total_seconds() / 60
        if minutes_since_last_hour > 55 or (minutes_since_refresh > 55 and minutes_since_last_hour > 50):
            need_fetch = True
    
    # 3. 后台异步刷新（加锁防并发）
    if need_fetch and not cache_service.is_locked("cn_stocks"):
        cache_service.lock("cn_stocks")
        import asyncio
        asyncio.create_task(_background_refresh_cn_stocks())
    
    # 4. 返回现有数据（必定有值，因为启动时已加载）
    return _latest_data if _latest_data else {}


async def _background_refresh_cn_stocks():
    """后台刷新A股数据（不阻塞响应）"""
    try:
        global _latest_data
        
        # 新浪实时行情接口
        symbols_list = list(config.CN_STOCK_CODES.keys())
        # 转换为s_前缀格式
        symbols_param = ",".join([f"s_{code}" for code in symbols_list])
        url = f"https://hq.sinajs.cn/list={symbols_param}"
        
        headers = {
            "Referer": "https://finance.sina.com.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            resp.encoding = 'gbk'
            text = resp.text
            
            results = {}
            
            # 逐行解析
            for line in text.strip().split('\n'):
                if 'hq_str' not in line:
                    continue
                
                # 提取股票代码
                code_match = re.search(r'hq_str_s_(sh\d{6}|sz\d{6})', line)
                if not code_match:
                    continue
                
                raw_code = code_match.group(1)
                
                # 解析数据
                data = _parse_sina_stock(line, raw_code)
                if data and data.get("name"):
                    # 映射到标准代码
                    for std_code, name in config.CN_STOCK_CODES.items():
                        if std_code.upper() == raw_code.upper() or std_code == raw_code:
                            results[std_code] = {
                                "name": name,
                                "code": std_code,
                                "price": data["price"],
                                "change": data["change"],
                                "pct": data["pct"],
                                "volume": data["volume"],
                                "amount": data["amount"],
                                "amplitude": data["amplitude"],
                                "high": data["high"],
                                "low": data["low"],
                                "open": data["open"],
                                "close": data["close"],
                                "time": data["time"],
                            }
                            break
            
            if results:
                _latest_data = results
                # 写缓存（含刷新时间）
                cache_service.set("cn_stocks", results, ttl=3600)
                logger.info(f"[后台刷新] A股数据更新成功: {list(results.keys())}")
    except Exception as e:
        logger.error(f"[后台刷新] A股数据刷新失败: {e}")
    finally:
        cache_service.unlock("cn_stocks")


def get_cached_stocks() -> dict:
    """获取缓存的股票数据"""
    return _latest_data


@router.get("")
async def get_stocks():
    """API: 获取股票数据"""
    return await fetch_cn_stocks()
