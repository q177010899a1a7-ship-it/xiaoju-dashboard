"""小居数据监控台 - 虚拟货币路由"""
import httpx
from fastapi import APIRouter
from typing import Dict, Any
from services.cache import cache_service
from services.logger import logger

router = APIRouter()

GATE_API = "https://api.gateio.ws/api/v4/spot/tickers"

CRYPTO_NAMES = {
    "BTC": "比特币 BTC",
    "ETH": "以太坊 ETH",
    "SOL": "Solana SOL",
    "BNB": "BNB",
    "XRP": "瑞波币 XRP",
    "ADA": "卡尔达诺 ADA",
    "DOGE": "狗狗币 DOGE",
    "DOT": "波卡 DOT",
    "AVAX": "雪崩 AVAX",
    "LINK": "Chainlink LINK",
    "ETHW": "以太经典 ETHW",
    "SUI": "Sui SUI",
    "APT": "Aptos APT",
    "ARB": "Arbitrum ARB",
    "OP": "Optimism OP",
}


async def _do_fetch_crypto() -> Dict[str, Any]:
    """真正抓取虚拟货币数据"""
    targets = {f"{s}_USDT" for s in CRYPTO_NAMES.keys()}
    results = {}
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(GATE_API)
            data = resp.json()
            for item in data:
                pair = item.get("currency_pair", "")
                if pair not in targets:
                    continue
                symbol = pair.replace("_USDT", "")
                results[symbol] = {
                    "symbol": symbol,
                    "name": CRYPTO_NAMES.get(symbol, symbol),
                    "price": float(item.get("last", 0)),
                    "change_24h": float(item.get("change_percentage", 0)),
                    "high_24h": float(item.get("high_24h", 0)),
                    "low_24h": float(item.get("low_24h", 0)),
                    "volume_24h": float(item.get("quote_volume", 0)),
                }
        return results
    except Exception as e:
        logger.error(f"获取虚拟货币价格失败: {e}")
        return results


async def fetch_crypto_prices() -> Dict[str, Any]:
    """获取主流虚拟货币价格 (stale-while-revalidate)"""
    cached = cache_service.get("crypto_prices")
    if cached:
        return cached

    import asyncio
    asyncio.create_task(_background_fetch_crypto())
    return {}


async def _background_fetch_crypto():
    results = await _do_fetch_crypto()
    if results:
        cache_service.set("crypto_prices", results, ttl=3600)
        logger.info(f"[后台刷新] 虚拟货币价格成功: {len(results)}个币种")


@router.get("")
async def get_crypto_prices():
    return await fetch_crypto_prices()