"""小居数据监控台 - 贵金属数据路由"""
import re
import httpx
from typing import Optional
from fastapi import APIRouter
import config
from services.cache import cache_service
from services.logger import logger

router = APIRouter()

_latest_metals: dict = {}

# 腾讯财经贵金属接口 - 国内可访问
TENCENT_METAL_URL = "https://qt.gtimg.cn/q={}"


async def fetch_metals() -> dict:
    """获取贵金属数据 - 使用腾讯财经接口（国内可访问）（stale-while-revalidate）"""
    global _latest_metals
    
    # 1. 立即返回缓存
    cached = cache_service.get("precious_metals")
    if cached:
        _latest_metals = cached
    
    # 2. 检查是否需要后台刷新
    need_fetch = False
    refresh_time = cache_service.get_refresh_time("precious_metals")
    if refresh_time is None:
        need_fetch = True
    else:
        from datetime import datetime
        now = datetime.now()
        minutes_since_refresh = (now - datetime.fromtimestamp(refresh_time)).total_seconds() / 60
        if minutes_since_refresh > 55:
            need_fetch = True
    
    # 3. 后台异步刷新
    if need_fetch and not cache_service.is_locked("precious_metals"):
        cache_service.lock("precious_metals")
        import asyncio
        asyncio.create_task(_background_refresh_metals())
    
    return _latest_metals if _latest_metals else {}


async def _background_refresh_metals():
    """后台刷新贵金属数据"""
    global _latest_metals
    try:
        symbols = ",".join(config.METAL_CODES.keys())
        url = TENCENT_METAL_URL.format(symbols)
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                url,
                headers={
                    "Referer": "https://finance.qq.com",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            
            text = resp.text
            results = {}
            
            for line in text.strip().split(';'):
                if not line.strip() or '=' not in line:
                    continue
                
                for code, name in config.METAL_CODES.items():
                    if code in line:
                        data = _parse_metal_data(line, code, name)
                        if data:
                            results[code] = data
                        break
            
            if results:
                _latest_metals = results
                cache_service.set("precious_metals", results, ttl=3600)
                logger.info(f"[后台刷新] 贵金属数据更新成功: {list(results.keys())}")
                
    except Exception as e:
        logger.error(f"[后台刷新] 贵金属数据刷新失败: {e}")
    finally:
        cache_service.unlock("precious_metals")


def _parse_metal_data(raw: str, code: str, name: str) -> Optional[dict]:
    """解析贵金属数据
    
    腾讯贵金属 hf_ 格式:
    字段0: 当前价格
    字段1: 涨跌额
    字段2: 昨结算/参考价（不是涨跌幅！）
    字段3: 开盘价
    字段4: 最高价
    字段5: 最低价
    字段6: 更新时间
    字段7: 参考价(昨收)
    
    涨跌幅计算: (当前价格 - 昨收) / 昨收 × 100
    """
    try:
        # 提取数据部分 v_hf_GC="4844.32,0.75,4848.80,4849.70,4917.70,4785.90,04:59:59,4808.30,..."
        match = re.search(rf'{code}="([^"]*)"', raw)
        if not match:
            return None
        fields = match.group(1).split(',')
        if len(fields) < 8:
            return None
        
        price = _safe_float(fields[0])        # 当前价格
        change = _safe_float(fields[1])       # 涨跌额
        # 注意：字段2不是涨跌幅，是昨结算价！真实涨跌幅需要自己计算
        open_price = _safe_float(fields[3])   # 开盘价
        high = _safe_float(fields[4])          # 最高价
        low = _safe_float(fields[5])           # 最低价
        ref_price = _safe_float(fields[7])    # 参考价(昨收)
        
        # 计算真实涨跌幅：从昨收计算，而非错误地取字段2
        if ref_price and ref_price > 0:
            pct = round((price - ref_price) / ref_price * 100, 2)
        else:
            pct = 0.0
        
        return {
            "name": name,
            "price": price,
            "change": change,
            "pct": pct,
            "open": open_price,
            "high": high,
            "low": low,
            "ref_price": ref_price,  # 添加昨收价格，方便调试
        }
    except Exception as e:
        logger.error(f"解析贵金属数据失败: {e}")
        return None


def _safe_float(value: str) -> float:
    """安全转换浮点数"""
    try:
        if not value or value == '-' or value == '':
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def get_cached_metals() -> dict:
    """获取缓存的贵金属数据"""
    return _latest_metals


@router.get("")
async def get_metals():
    """API: 获取贵金属数据"""
    return await fetch_metals()
