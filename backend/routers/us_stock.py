"""小居数据监控台 - 美股数据路由（国内可用接口）"""
import httpx
import re
from fastapi import APIRouter
import config
from services.cache import cache_service
from services.logger import logger

router = APIRouter()

# 腾讯财经美股接口 - 国内可访问
TENCENT_US_URL = "https://qt.gtimg.cn/q={}"

# 新浪财经美股接口 - 国内可访问
SINA_US_URL = "https://hq.sinajs.cn/list={}"


async def _fetch_us_stocks_raw() -> dict:
    """真正抓取美股数据（内部用）"""
    results = {}
    tencent_codes = ["usIXIC", "usDJI", "usINX", "usAAPL", "usMSFT", "usGOOG", "usAMZN", "usTSLA", "usNVDA", "usMETA", "usJPM", "usV", "usBRKB"]

    stock_map = {
        "usIXIC": ("纳斯达克综合", "^IXIC", "index"),
        "usDJI": ("道琼斯工业", "^DJI", "index"),
        "usINX": ("标普500", "^GSPC", "index"),
        "usAAPL": ("苹果", "AAPL", "stock"),
        "usMSFT": ("微软", "MSFT", "stock"),
        "usGOOG": ("谷歌", "GOOGL", "stock"),
        "usAMZN": ("亚马逊", "AMZN", "stock"),
        "usTSLA": ("特斯拉", "TSLA", "stock"),
        "usNVDA": ("英伟达", "NVDA", "stock"),
        "usMETA": ("Meta", "META", "stock"),
        "usJPM": ("摩根大通", "JPM", "stock"),
        "usV": ("Visa", "V", "stock"),
        "usBRKB": ("伯克希尔-B", "BRK-B", "stock"),
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                TENCENT_US_URL.format(",".join(tencent_codes)),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://finance.qq.com",
                }
            )
            text = resp.text

            for code, (name, symbol, stype) in stock_map.items():
                try:
                    pattern = rf'{code}="([^"]+)"'
                    match = re.search(pattern, text)
                    if not match:
                        results[code] = {"name": name, "symbol": symbol, "type": stype, "error": "数据未找到"}
                        continue

                    raw = match.group(1)
                    fields = raw.split('~')
                    if len(fields) < 10:
                        results[code] = {"name": name, "symbol": symbol, "type": stype, "error": f"数据格式异常: {raw[:50]}"}
                        continue

                    try:
                        price = float(fields[3])
                        change = float(fields[31]) if len(fields) > 31 and fields[31] else 0.0
                        pct = float(fields[32]) if len(fields) > 32 and fields[32] else 0.0
                        high = float(fields[33]) if len(fields) > 33 and fields[33] else 0.0
                        low = float(fields[34]) if len(fields) > 34 and fields[34] else 0.0
                        open_price = float(fields[5]) if fields[5] else 0.0
                        prev_close = price - change
                        volume = float(fields[7]) if fields[7] else 0.0
                    except (ValueError, IndexError) as e:
                        results[code] = {"name": name, "symbol": symbol, "type": stype, "error": f"解析失败: {e}"}
                        continue

                    results[code] = {
                        "name": name, "symbol": symbol, "type": stype,
                        "price": price, "change": change, "pct": pct,
                        "high": high, "low": low, "open": open_price,
                        "previousClose": prev_close, "volume": volume,
                    }
                except Exception as e:
                    logger.error(f"解析美股 {code} 失败: {e}")
                    results[code] = {"name": name, "symbol": symbol, "type": stype, "error": str(e)}

    except Exception as e:
        logger.error(f"获取美股数据失败: {e}")

    return results


async def fetch_us_stocks() -> dict:
    """获取美股数据（stale-while-revalidate）"""
    # 1. 立即返回缓存
    cached = cache_service.get("us_stocks")

    # 2. 检查是否需要后台刷新
    need_fetch = False
    refresh_time = cache_service.get_refresh_time("us_stocks")
    if refresh_time is None:
        need_fetch = True
    else:
        from datetime import datetime
        minutes_since_refresh = (datetime.now() - datetime.fromtimestamp(refresh_time)).total_seconds() / 60
        if minutes_since_refresh > 55:
            need_fetch = True

    # 3. 后台异步刷新
    if need_fetch and not cache_service.is_locked("us_stocks"):
        cache_service.lock("us_stocks")
        import asyncio
        asyncio.create_task(_background_refresh_us_stocks())

    return cached if cached else {}


async def _background_refresh_us_stocks():
    """后台刷新美股数据"""
    try:
        results = await _fetch_us_stocks_raw()
        if results:
            cache_service.set("us_stocks", results, ttl=3600)
            logger.info(f"[后台刷新] 美股数据更新成功: {len(results)}条")
    except Exception as e:
        logger.error(f"[后台刷新] 美股数据刷新失败: {e}")
    finally:
        cache_service.unlock("us_stocks")


@router.get("")
async def get_us():
    """API: 获取美股数据"""
    return await fetch_us_stocks()


@router.get("/chart")
async def get_us_chart(symbol: str = "AAPL", range: str = "24h"):
    """API: 获取美股图表数据（暂用占位数据）"""
    return {"symbol": symbol, "data": [], "note": "图表数据暂不可用，请使用实际行情网站查看"}