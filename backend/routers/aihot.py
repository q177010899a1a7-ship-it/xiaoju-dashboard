"""小居数据监控台 - AI HOT 新闻路由"""
import httpx
from fastapi import APIRouter
from datetime import datetime, timedelta
import pytz
from services.cache import cache_service
from services.logger import logger

router = APIRouter()

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 "
    "Safari/537.36 aihot-skill/0.2.0"
)
BASE_URL = "https://aihot.virxact.com"

CATEGORY_MAP = {
    "ai-models": {"label": "模型发布/更新", "icon": "🤖", "color": "blue"},
    "ai-products": {"label": "产品发布/更新", "icon": "🆕", "color": "green"},
    "industry": {"label": "行业动态", "icon": "📈", "color": "orange"},
    "paper": {"label": "论文研究", "icon": "📚", "color": "purple"},
    "tip": {"label": "技巧与观点", "icon": "💡", "color": "yellow"},
}


def _fmt_time(iso: str) -> str:
    """将 ISO 时间转为 HH:mm 格式（北京时间）"""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        # 转北京时间
        bj = pytz.timezone("Asia/Shanghai")
        dt = dt.astimezone(bj)
        return dt.strftime("%H:%m")
    except Exception:
        return ""


def _fmt_date(iso: str) -> str:
    """将 ISO 时间转为日期标记（北京时间）"""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        bj = pytz.timezone("Asia/Shanghai")
        dt = dt.astimezone(bj)
        return dt.strftime("%m月%d日")
    except Exception:
        return ""


async def _fetch_aihot(path: str, params: dict = None) -> dict:
    """通用 fetch 封装"""
    url = f"{BASE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, params=params or {}, headers={"User-Agent": UA})
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning(f"aihot API 请求失败 {url}: {e}")
        return {}


@router.get("/daily")
async def get_aihot_daily():
    """AI HOT 今日日报（按分类分版块）"""
    cached = cache_service.get("aihot_daily")
    if cached:
        return cached

    data = await _fetch_aihot("/api/public/daily")
    if not data:
        return {"error": "获取失败", "date": "", "sections": []}

    # 整理 sections
    sections = []
    for sec in data.get("sections", []):
        cat_info = CATEGORY_MAP.get(sec.get("category", ""), {})
        items = []
        for item in sec.get("items", []):
            items.append({
                "title": item.get("title", ""),
                "summary": item.get("summary", ""),
                "url": item.get("sourceUrl", ""),
                "source": item.get("sourceName", ""),
            })
        if items:
            sections.append({
                "label": sec.get("label", cat_info.get("label", "")),
                "icon": cat_info.get("icon", "📰"),
                "color": cat_info.get("color", "gray"),
                "items": items,
            })

    result = {
        "date": data.get("date", ""),
        "generatedAt": data.get("generatedAt", ""),
        "sections": sections,
        "total": sum(len(s["items"]) for s in sections),
    }
    cache_service.set("aihot_daily", result, ttl=3600)
    return result


@router.get("/timeline")
async def get_aihot_timeline(since_days: int = 1):
    """AI HOT 时间线（按日期分组，最接近 aihot.virxact.com 首页布局）

    - since_days: 拉取最近几天（默认1，最大7）
    """
    if since_days < 1:
        since_days = 1
    if since_days > 7:
        since_days = 7

    cache_key = f"aihot_timeline_{since_days}"
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    # 计算 since 时间（北京时间）
    bj = pytz.timezone("Asia/Shanghai")
    now_bj = datetime.now(bj)
    since_dt = now_bj - timedelta(days=since_days)
    since_iso = since_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    data = await _fetch_aihot("/api/public/items", {
        "mode": "selected",
        "since": since_iso,
        "take": 100,
    })

    if not data or "items" not in data:
        return {"days": [], "error": "获取失败"}

    # 按"月日"分组
    day_groups: dict = {}
    for item in data.get("items", []):
        pub = item.get("publishedAt", "")
        day_key = _fmt_date(pub)
        if not day_key:
            day_key = "其他"
        if day_key not in day_groups:
            day_groups[day_key] = []
        cat = item.get("category", "")
        cat_info = CATEGORY_MAP.get(cat, {})
        day_groups[day_key].append({
            "id": item.get("id", ""),
            "time": _fmt_time(pub),
            "title": item.get("title", ""),
            "title_en": item.get("title_en"),
            "url": item.get("url", ""),
            "source": item.get("source", ""),
            "summary": item.get("summary") or item.get("description", ""),
            "category": cat,
            "cat_label": cat_info.get("label", cat),
            "cat_icon": cat_info.get("icon", "📰"),
            "cat_color": cat_info.get("color", "gray"),
            "ai_selected": item.get("aiSelected", False),
        })

    # 转成有序列表（最新日期在前）
    sorted_days = []
    for day_key in sorted(day_groups.keys(), reverse=True):
        sorted_days.append({
            "date": day_key,
            "items": day_groups[day_key],
        })

    result = {"days": sorted_days, "total": len(data.get("items", []))}
    cache_service.set(cache_key, result, ttl=1800)
    return result


@router.get("/categories")
async def get_aihot_by_category(
    category: str = "",
    since_days: int = 3,
):
    """按分类拉取条目（支持筛选分类）"""
    if since_days < 1:
        since_days = 1
    if since_days > 7:
        since_days = 7

    bj = pytz.timezone("Asia/Shanghai")
    now_bj = datetime.now(bj)
    since_dt = now_bj - timedelta(days=since_days)
    since_iso = since_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    params = {"mode": "selected", "since": since_iso, "take": 100}
    if category:
        params["category"] = category

    data = await _fetch_aihot("/api/public/items", params)
    if not data or "items" not in data:
        return {"category": category, "items": [], "error": "获取失败"}

    items = []
    for item in data.get("items", []):
        cat = item.get("category", "")
        cat_info = CATEGORY_MAP.get(cat, {})
        items.append({
            "id": item.get("id", ""),
            "time": _fmt_time(item.get("publishedAt", "")),
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "source": item.get("source", ""),
            "summary": item.get("summary") or "",
            "category": cat,
            "cat_label": cat_info.get("label", cat),
            "cat_icon": cat_info.get("icon", "📰"),
        })

    return {
        "category": category,
        "cat_label": CATEGORY_MAP.get(category, {}).get("label", category),
        "items": items,
        "total": len(items),
    }


@router.get("/categories/list")
async def list_categories():
    """可用分类列表"""
    return {"categories": CATEGORY_MAP}