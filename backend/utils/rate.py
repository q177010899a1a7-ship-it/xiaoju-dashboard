"""小居数据监控台 - 汇率工具"""
import httpx
from services.cache import cache_service
from services.logger import logger

async def get_exchange_rate() -> dict:
    """获取汇率"""
    cached = cache_service.get("exchange_rate")
    if cached:
        return cached
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.exchangerate-api.com/v4/latest/USD"
            )
            data = resp.json()
            
            rates = data.get("rates", {})
            result = {
                "USD_CNY": rates.get("CNY", 7.24),
                "EUR_CNY": rates.get("CNY", 7.24) / rates.get("EUR", 0.92) if rates.get("EUR") else 0,
                "JPY_CNY": rates.get("CNY", 7.24) / rates.get("JPY", 149.5) if rates.get("JPY") else 0,
                "GBP_CNY": rates.get("CNY", 7.24) / rates.get("GBP", 0.79) if rates.get("GBP") else 0,
            }
            
            cache_service.set("exchange_rate", result, ttl=3600)
            return result
    except Exception as e:
        logger.error(f"获取汇率失败: {e}")
        return {"USD_CNY": 7.24}

def convert_currency(amount: float, from_currency: str, to_currency: str, rates: dict = None) -> float:
    """货币换算"""
    if not rates:
        return amount
    
    key = f"{from_currency}_{to_currency}"
    if key in rates:
        return amount * rates[key]
    
    # 尝试反向
    reverse_key = f"{to_currency}_{from_currency}"
    if reverse_key in rates:
        return amount / rates[reverse_key]
    
    # 通过USD转换
    if "USD" in key:
        return amount * rates.get(key, amount)
    
    return amount
