"""小居数据监控台 - 新闻资讯路由（强化版）"""
import httpx
import re
import feedparser
from fastapi import APIRouter
import config
from services.cache import cache_service
from services.logger import logger

router = APIRouter()

def _clean_html(html: str) -> str:
    clean = re.sub(r'<[^>]+>', '', html)
    return clean.strip()


# 各源fetch函数（支持follow_redirects）
FETCHERS = {
    "36kr":          {"url": "https://36kr.com/feed",                    "source": "36氪",       "lang": "cn",  "limit": 10},
    "tmtpost":       {"url": "https://www.tmtpost.com/rss",               "source": "钛媒体",      "lang": "cn",  "limit": 10},
    "ithome":        {"url": "https://www.ithome.com/rss/",                "source": "IT之家",      "lang": "cn",  "limit": 15},
    "techcrunch":    {"url": "https://techcrunch.com/feed/",               "source": "TechCrunch",  "lang": "en",  "limit": 8},
    "venturebeat_ai":{"url": "https://venturebeat.com/category/ai/feed/",  "source": "VentureBeat", "lang": "en",  "limit": 8},
    "mit_tech":     {"url": "https://www.technologyreview.com/feed/",    "source": "MIT Tech",    "lang": "en",  "limit": 8},
}


async def _fetch_rss(name: str, info: dict) -> list:
    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
            resp = await client.get(info["url"], headers={"User-Agent": "Mozilla/5.0"})
            resp.encoding = "utf-8"
            feed = feedparser.parse(resp.text)
            results = []
            for entry in feed.entries[: info["limit"]]:
                results.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "description": _clean_html(entry.get("description", ""))[:150],
                    "published": entry.get("published", ""),
                    "source": info["source"],
                    "lang": info["lang"],
                })
            return results
    except Exception as e:
        logger.warning(f"获取{name}新闻失败: {e}")
        return []


async def fetch_all_news() -> dict:
    """获取所有新闻源（stale-while-revalidate）"""
    # 1. 立即返回缓存
    cached = cache_service.get("all_news")
    if cached:
        return cached
    
    # 2. 后台异步刷新
    import asyncio
    asyncio.create_task(_background_fetch_all_news())
    
    # 3. 返回空（首次访问）
    return {"news": [], "sources": []}


async def _background_fetch_all_news():
    """后台刷新新闻"""
    results = {"news": [], "sources": []}
    for name, info in FETCHERS.items():
        news = await _fetch_rss(name, info)
        if news:
            results["news"].extend(news)
            results["sources"].append(info["source"])
    
    results["news"].sort(key=lambda x: x.get("published", ""), reverse=True)
    if results["news"]:
        cache_service.set("all_news", results, ttl=3600)
        logger.info(f"[后台刷新] 新闻成功: 共{len(results['news'])}条")


# ———— 智能分类关键词 ————
CAT_KEYWORDS = {
    "ai_tech": {
        "label": "AI & 前沿科技",
        "kws": ["ai","人工智能","大模型","gpt","chatgpt","openai","llm","copilot","agent",
                "aigc","sora","深度学习","机器学习","神经网络","nlp","大语言模型",
                "claude","gemini","模型","算力","芯片","gpu","nvidia","英伟达",
                "机器人","robot","具身智能","自动驾驶","robotics","langchain"],
        "icon": "🤖"
    },
    "internet": {
        "label": "互联网 & 产品",
        "kws": ["互联网","腾讯","阿里","字节","百度","字节跳动","阿里巴巴","腾讯",
                "京东","拼多多","美团","抖音","微信","小红书","b站","bilibili",
                "微博","知乎","快手","滴滴","滴滴出行","支付宝","淘宝","天猫","电商"],
        "icon": "🌐"
    },
    "smart_hardware": {
        "label": "智能硬件",
        "kws": ["手机","笔记本","电脑","平板","耳机","智能手表","苹果","华为","小米",
                "三星","荣耀","oppo","vivo","联想","华硕","游戏本","轻薄本","显卡",
                "cpu","处理器","屏幕","折叠屏","oled","固态电池"],
        "icon": "📱"
    },
    "new_energy": {
        "label": "新能源 & 汽车",
        "kws": ["新能源","电动汽车","电动车","特斯拉","比亚迪","蔚来","理想","小鹏",
                "小米汽车","华为汽车","吉利","长安","宁德时代","锂电池","自动驾驶",
                "智驾","电车","续航","充电桩"],
        "icon": "🚗"
    },
    "finance": {
        "label": "财经 & 商业",
        "kws": ["股价","市值","营收","利润","融资","上市","财报","业绩","ipo","投资",
                "金融","银行","基金","股市","证券","债券","人民币","美元","汇率",
                "关税","贸易","经济","宏观","a股","美股","港股"],
        "icon": "💹"
    },
    "international": {
        "label": "国际要闻",
        "kws": ["美国","中国","欧洲","日本","韩国","俄罗斯","英国","法国","德国",
                "国际","全球","外交","峰会","制裁","欧盟","北约","联合国",
                "中美","中欧","G20","APEC","tpp","一带一路"],
        "icon": "🌍"
    },
    "startup": {
        "label": "创业 & 创投",
        "kws": ["融资","收购","并购","上市","独角兽","投资","天使","vc","pe",
                "创业","创始人","ceo","估值","亿美元","数千万","数亿"],
        "icon": "🚀"
    },
}

def _classify(news_list: list) -> dict:
    """将新闻分类到各主题"""
    categorized = {k: [] for k in CAT_KEYWORDS}
    # 剩余未分类
    rest = []
    for n in news_list:
        title = n.get("title", "").lower()
        desc = n.get("description", "").lower()
        text = title + " " + desc
        matched = False
        for cat_id, cat in CAT_KEYWORDS.items():
            if any(kw in text for kw in cat["kws"]):
                categorized[cat_id].append(n)
                matched = True
                break
        if not matched:
            rest.append(n)
    return {k: v for k, v in categorized.items() if v}, rest


@router.get("")
async def get_news():
    return await fetch_all_news()


@router.get("/categorized")
async def get_categorized():
    """返回分类后的新闻"""
    data = await fetch_all_news()
    cats, rest = _classify(data["news"])
    return {
        "categories": cats,
        "uncategorized": rest,
        "sources": data["sources"],
        "total": len(data["news"])
    }


@router.get("/36kr")
async def get_36kr():
    cached = cache_service.get("36kr_news")
    if cached:
        return cached
    news = await _fetch_rss("36kr", FETCHERS["36kr"])
    cache_service.set("36kr_news", news, ttl=1800)
    return {"news": news, "source": "36氪"}


@router.get("/tmtpost")
async def get_tmtpost():
    cached = cache_service.get("tmtpost_news")
    if cached:
        return cached
    news = await _fetch_rss("tmtpost", FETCHERS["tmtpost"])
    cache_service.set("tmtpost_news", news, ttl=1800)
    return {"news": news, "source": "钛媒体"}


@router.get("/ithome")
async def get_ithome():
    cached = cache_service.get("ithome_news")
    if cached:
        return cached
    news = await _fetch_rss("ithome", FETCHERS["ithome"])
    cache_service.set("ithome_news", news, ttl=1800)
    return {"news": news, "source": "IT之家"}
