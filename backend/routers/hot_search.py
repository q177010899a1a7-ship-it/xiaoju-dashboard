"""小居数据监控台 - 热搜数据路由（使用 uapis.cn）"""
import httpx
from fastapi import APIRouter
from services.logger import logger

router = APIRouter()

UAPIS_BASE = "https://uapis.cn/api/v1/misc/hotboard"
UAPIS_KEY = "uapi-loimw-z0g-ICpegbbzlHDlm957ld-lNcy-COnDxO"

# 进程内缓存（避免异步问题）
_cache: dict = {}
_cache_time: dict = {}


def _format_hot_value(val: str) -> str:
    try:
        v = float(val)
        if v >= 100000000:
            return f"{v/100000000:.1f}亿"
        elif v >= 10000:
            return f"{v/10000:.1f}万"
        return str(int(v))
    except:
        return val


# 各平台 TTL（秒），每小时整点刷新
_TTL = 3600


def _is_cache_fresh(platform: str) -> bool:
    """检查缓存是否新鲜（距上次刷新未超过55分钟）"""
    import time
    if platform not in _cache:
        return False
    if platform not in _cache_time:
        return False
    return (time.time() - _cache_time[platform]) < (_TTL - 300)


async def _fetch_platform(platform: str) -> list:
    """获取单个平台热搜（stale-while-revalidate）"""
    # 1. 立即返回缓存
    if _is_cache_fresh(platform):
        return _cache.get(platform, [])
    
    # 2. 有缓存但过期，后台异步刷新
    if platform in _cache and not _is_cache_fresh(platform):
        import asyncio
        asyncio.create_task(_background_fetch_platform(platform))
        return _cache.get(platform, [])
    
    # 3. 完全无缓存，同步获取
    return await _do_fetch_platform(platform)


async def _do_fetch_platform(platform: str) -> list:
    """真正抓取单个平台热搜"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            resp = await client.get(
                UAPIS_BASE,
                params={"type": platform},
                headers={"Authorization": f"Bearer {UAPIS_KEY}"}
            )
            raw = resp.json()
            items = raw.get("list", [])
            if not items and not raw.get("type"):
                logger.warning(f"uapis {platform} response invalid: {str(raw)[:100]}")
                return _cache.get(platform, [])

            items = raw.get("list", [])
            results = []
            for item in items[:20]:
                results.append({
                    "rank": item.get("index", 0),
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "hot_value": _format_hot_value(str(item.get("hot_value", 0))),
                    "raw_hot": item.get("hot_value", 0),
                    "platform": platform,
                })

            import time
            _cache[platform] = results
            _cache_time[platform] = time.time()
            logger.info(f"获取{platform}热搜成功: {len(results)}条")
            return results

    except Exception as e:
        logger.error(f"获取{platform}热搜失败: {e}")
        return _cache.get(platform, [])


async def _background_fetch_platform(platform: str):
    """后台刷新热搜"""
    try:
        await _do_fetch_platform(platform)
    except Exception as e:
        logger.error(f"[后台刷新] {platform}热搜失败: {e}")


@router.get("")
async def get_all_hot():
    """API: 获取所有热搜"""
    import asyncio
    weibo_task = _fetch_platform("weibo")
    douyin_task = _fetch_platform("douyin")

    results = await asyncio.gather(weibo_task, douyin_task, return_exceptions=True)

    weibo = results[0] if not isinstance(results[0], Exception) else []
    douyin = results[1] if not isinstance(results[1], Exception) else []

    return {
        "weibo": weibo,
        "douyin": douyin,
    }


@router.get("/weibo")
async def get_weibo():
    return {"weibo": await _fetch_platform("weibo")}


@router.get("/douyin")
async def get_douyin():
    return {"douyin": await _fetch_platform("douyin")}


def get_cached_hot() -> dict:
    """兼容旧代码"""
    return _cache


# ========== 兼容旧调度器 ==========
async def fetch_weibo_hot():
    """兼容旧调度器调用"""
    return await _fetch_platform("weibo")

async def fetch_douyin_hot():
    """兼容旧调度器调用"""
    return await _fetch_platform("douyin")

async def fetch_twitter_hot():
    """兼容旧调度器调用（暂无数据源）"""
    return []
