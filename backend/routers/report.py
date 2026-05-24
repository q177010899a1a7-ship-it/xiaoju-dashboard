"""小居数据监控台 - 分析报告生成路由（优化版）"""
from datetime import datetime
import random
import httpx
import feedparser
import re
from fastapi import APIRouter
from services.logger import logger

router = APIRouter()


def _clean_html(html: str) -> str:
    """清理HTML标签"""
    clean = re.sub(r'<[^>]+>', '', html)
    return clean.strip()


async def _fetch_news_fresh() -> dict:
    """直接拉取多源新闻（全中文媒体），不走缓存，确保早晚报资讯内容丰富"""
    results = {"news": [], "sources": []}

    # 全中文媒体源矩阵（AI科技 + 泛科技 + 创业创投）
    fetchers = {
        # 核心AI科技媒体
        "36kr":          {"url": "https://36kr.com/feed",                "source": "36氪",        "limit": 10},
        "tmtpost":       {"url": "https://www.tmtpost.com/rss",           "source": "钛媒体",       "limit": 10},
        "ithome":        {"url": "https://www.ithome.com/rss/",          "source": "IT之家",       "limit": 10},
        "huxiu":         {"url": "https://www.huxiu.com/rss/feed.xml",   "source": "虎嗅",         "limit": 10},
        "qubit":         {"url": "https://qubit.cn/rss",                 "source": "量子位",       "limit": 10},
        "jiqizhixin":    {"url": "https://www.jiqizhixin.com/rss",       "source": "机器之心",     "limit": 8},
        "aiera":         {"url": "https://www.ai-era.com/rss",            "source": "新智元",       "limit": 8},
        "geekpark":      {"url": "https://www.geekpark.net/rss",          "source": "极客公园",     "limit": 8},
        "cyzone":        {"url": "https://www.cyzone.cn/rss",            "source": "创业邦",       "limit": 8},
        "pingwest":      {"url": "https://www.pingwest.com/rss",          "source": "品玩",         "limit": 8},
        # 补充：其他优质中文源（备用）
        "lieyun":        {"url": "https://www.lieyunpro.com/feed",       "source": "猎云网",       "limit": 8},
        "fromgeek":      {"url": "https://www.fromgeek.com/rss",          "source": "极客网",       "limit": 8},
    }

    for name, info in fetchers.items():
        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
                resp = await client.get(info["url"], headers={"User-Agent": "Mozilla/5.0"})
                resp.encoding = "utf-8"
                feed = feedparser.parse(resp.text)
                for entry in feed.entries[: info["limit"]]:
                    results["news"].append({
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "description": _clean_html(entry.get("description", ""))[:150],
                        "published": entry.get("published", ""),
                        "source": info["source"],
                    })
                if feed.entries:
                    results["sources"].append(info["source"])
        except Exception as e:
            logger.warning(f"获取{name}新闻失败: {e}")

    results["news"].sort(key=lambda x: x.get("published", ""), reverse=True)
    return results

WEEKDAY_CN = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


def _format_stock_summary(stocks: dict) -> str:
    """格式化股市数据"""
    if not stocks:
        return "暂无数据"

    lines = []
    for code, data in stocks.items():
        pct = data.get("pct", 0)
        change = data.get("change", 0)
        price = data.get("price", 0)

        emoji = "📈" if pct >= 0 else "📉"
        sign = "+" if pct >= 0 else ""

        amount_wan = data.get("amount", 0)
        if amount_wan > 10000:
            amount_yi = amount_wan / 10000
            amount_str = f"{amount_yi:.2f}亿"
        else:
            amount_str = f"{amount_wan:.0f}万"

        lines.append(
            f"{emoji} **{data.get('name', code)}** {price:.2f}\n"
            f"   {sign}{pct:.2f}% {sign}{change:.2f} | 成交 {amount_str}"
        )

    return "\n".join(lines)


def _format_hot_list(hot_items: list, max_count: int = 5) -> str:
    """格式化热搜列表"""
    if not hot_items:
        return "暂无数据"

    lines = []
    for i, item in enumerate(hot_items[:max_count]):
        # uapis返回的字段是title
        word = item.get("title", item.get("word", ""))
        hot_val = item.get("hot_value", "")
        if hot_val:
            lines.append(f"{i+1}. {word}（{hot_val}）")
        else:
            lines.append(f"{i+1}. {word}")
    return "\n".join(lines)


def _get_weekday(now: datetime) -> str:
    """获取中文星期"""
    return WEEKDAY_CN[now.weekday()]


async def generate_morning_report() -> dict:
    """生成早报"""
    from routers import stock, precious_metals, hot_search, news, life_tools
    from routers.us_stock import fetch_us_stocks
    from routers.commodity import fetch_commodities

    now = datetime.now()
    weekday = _get_weekday(now)
    calendar_data = life_tools.get_chinese_calendar()

    # 股票数据
    stocks = {}
    try:
        stocks = await stock.fetch_cn_stocks()
    except Exception as e:
        logger.warning(f"获取A股数据失败: {e}")

    # 贵金属
    metals = {}
    try:
        metals = await precious_metals.fetch_metals()
    except Exception as e:
        logger.warning(f"获取贵金属数据失败: {e}")

    # 美股
    us_stocks = {}
    try:
        us_stocks = await fetch_us_stocks()
    except Exception as e:
        logger.warning(f"获取美股数据失败: {e}")

    # 大宗商品
    commodities = {}
    try:
        commodities = await fetch_commodities()
    except Exception as e:
        logger.warning(f"获取大宗商品数据失败: {e}")

    # 热搜（从进程内缓存）
    hot = hot_search._cache or {}
    weibo_hot = hot.get("weibo", [])
    douyin_hot = hot.get("douyin", [])

    # 新闻（不走缓存，直接拉取确保最新）
    news_data = {}
    try:
        news_data = await _fetch_news_fresh()
    except Exception as e:
        logger.warning(f"获取新闻数据失败: {e}")

    all_news = news_data.get("news", [])

    # ———— 强化版新闻分类 ————
    CAT_KEYWORDS = {
        "ai_tech": ["ai","人工智能","大模型","gpt","chatgpt","openai","llm","copilot","agent","aigc","sora","深度学习","机器学习","神经网络","nlp","大语言模型","claude","gemini","算力","芯片","gpu","nvidia","英伟达","机器人","robot","具身智能","langchain","自动驾驶","robotics"],
        "internet": ["互联网","腾讯","阿里","字节","百度","字节跳动","阿里巴巴","京东","拼多多","美团","抖音","微信","小红书","b站","bilibili","微博","知乎","快手","滴滴","支付宝","淘宝","天猫","电商","腾讯文档","钉钉"],
        "smart_hardware": ["手机","笔记本","电脑","平板","耳机","智能手表","苹果","华为","小米","三星","荣耀","oppo","vivo","联想","华硕","显卡","cpu","处理器","屏幕","折叠屏","oled","固态电池","游戏本","轻薄本","荣耀"],
        "new_energy": ["新能源","电动汽车","电动车","特斯拉","比亚迪","蔚来","理想","小鹏","小米汽车","华为汽车","吉利","长安","宁德时代","锂电池","智驾","电车","续航","充电桩","新车"],
        "finance": ["股价","市值","营收","利润","融资","上市","财报","业绩","ipo","投资","金融","银行","基金","股市","证券","债券","人民币","美元","汇率","关税","贸易","经济","宏观","a股","美股","港股","证券"],
        "international": ["美国","中国","欧洲","日本","韩国","俄罗斯","英国","法国","德国","国际","全球","外交","峰会","制裁","欧盟","北约","联合国","中美","中欧","g20","一带一路","巴西","印度"],
        "startup": ["融资","收购","并购","上市","独角兽","天使","vc","pe","创业","创始人","估值","亿美元","数千万","数亿","pre-a","a轮","b轮","c轮"],
    }
    def _cat_match(text, kws):
        t = text.lower()
        return any(kw in t for kw in kws)

    finance_news = [n for n in all_news if _cat_match(n.get("title","")+" "+n.get("description",""), CAT_KEYWORDS["finance"])]
    tech_news = [n for n in all_news if _cat_match(n.get("title","")+" "+n.get("description",""), CAT_KEYWORDS["ai_tech"]+CAT_KEYWORDS["internet"]+CAT_KEYWORDS["smart_hardware"])]
    world_news = [n for n in all_news if _cat_match(n.get("title","")+" "+n.get("description",""), CAT_KEYWORDS["international"])]
    ai_news = [n for n in all_news if _cat_match(n.get("title","")+" "+n.get("description",""), CAT_KEYWORDS["ai_tech"])]
    startup_news = [n for n in all_news if _cat_match(n.get("title","")+" "+n.get("description",""), CAT_KEYWORDS["startup"])]

    # 星座运势 - 详细版
    taurus = life_tools.get_horoscope_details("金牛座")
    cancer = life_tools.get_horoscope_details("巨蟹座")

    # 生成综合点评
    all_pct = [data.get("pct", 0) for data in stocks.values() if isinstance(data, dict)]
    avg_pct = sum(all_pct) / len(all_pct) if all_pct else 0

    if avg_pct > 1:
        market_comment = "今日市场强势上扬，整体做多情绪浓厚，结构性机会丰富"
    elif avg_pct < -1:
        market_comment = "今日市场震荡下行，谨慎情绪升温，建议控制仓位观望为主"
    else:
        market_comment = f"今日市场小幅{('上涨' if avg_pct >= 0 else '下跌')}，指数波动幅度有限，结构性分化明显"

    # 最强/最弱指数
    sorted_stocks = sorted(stocks.items(), key=lambda x: x[1].get("pct", 0), reverse=True) if stocks else []
    strongest = sorted_stocks[0] if sorted_stocks else None
    weakest = sorted_stocks[-1] if len(sorted_stocks) > 1 else None

    # 热搜头条
    top_weibo = weibo_hot[0].get("title", "") if weibo_hot else ""
    top_douyin = douyin_hot[0].get("title", "") if douyin_hot else ""

    content = f"""**小居早报 | {now.strftime('%Y年%m月%d日')} {weekday}**

---

**📅 今日概况**
- 阳历：{now.strftime('%Y年%m月%d日')} {weekday}
- 农历：{calendar_data.get('lunar', '农历日期')}
- 星座提醒：金牛座 · 巨蟹座（当日重点关注星座）

---

**📋 今日黄历**
- 吉位：东、南（核心吉位）
- 凶位：{random.choice(['西', '北', '东北'])}
- 宜：出行、开业、搬家、祈福、纳财
- 忌：动土、安葬、嫁娶、破土
- 冲煞：冲鼠（壬子年生），煞北

---

**🌟 星座运势（重点关注）**

**♉ 金牛座（4月20日-5月20日）**
今日运势整体平稳，财运方面有不错的机会，尤其是正财收入表现突出。工作上稳扎稳打，与同事协作顺畅。感情方面，单身者有机会遇到心仪对象，已婚者家庭氛围和睦。健康注意消化系统，饮食宜清淡。

💰 财运：★★★★☆ 稳步上升，正财运势佳
💼 事业：★★★★☆ 稳中求进，人际关系和谐
💙 感情：★★★☆☆ 运势平缓，主动出击有惊喜
🏥 健康：★★★☆☆ 注意肠胃，避免油腻

---

**♋ 巨蟹座（6月21日-7月22日）**
今日运势较为顺利，尤其是家庭和人际关系方面有不错的表现。情绪稳定，直觉敏锐，在需要做决策的事情上往往能押对方向。财运有暗财机会，可能收到意外礼物或补助。健康方面注意休息，不要过度操劳。

💰 财运：★★★★☆ 暗财涌动，可能有额外收入
💼 事业：★★★☆☆ 平稳推进，注意沟通表达
💙 感情：★★★★★ 运势极佳，社交运强，人缘佳
🏥 健康：★★★☆☆ 需注意休息，避免过度疲劳

---

**📊 股市行情**

{_format_stock_summary(stocks)}

---

**🗽 美股行情**
{_format_us_summary(us_stocks)}

---

**🥇 贵金属**
{_format_metals_summary(metals)}

---

**📱 热门热搜汇总**

**1. 微博热搜 TOP5**
{_format_hot_list(weibo_hot, 5)}

**2. 抖音热搜 TOP5**
{_format_hot_list(douyin_hot, 5)}

---

**💹 财经资讯（{len(finance_news[:3])}条）**
{_format_news(finance_news[:3])}

---

**🤖 AI & 科技资讯（{len(ai_news[:3])}条）**
{_format_news(ai_news[:3])}

---

**🚀 创业 & 创投（{len(startup_news[:2])}条）**
{_format_news(startup_news[:2])}

---

**🌍 国际要闻（{len(world_news[:2])}条）**
{_format_news(world_news[:2])}

---

**💡 小居点评**
{market_comment}"""

    if strongest:
        content += f"\n\n📈 今日最强：{strongest[1].get('name', '')}，涨幅{strongest[1].get('pct', 0):+.2f}%"
    if weakest:
        content += f"\n📉 今日偏弱：{weakest[1].get('name', '')}，{'涨幅' if weakest[1].get('pct', 0) >= 0 else '跌幅'}{abs(weakest[1].get('pct', 0)):.2f}%"

    content += f"""

---

**#靓仔今日关注**
🔍 {top_weibo[:20]}... 等热搜持续发酵，可关注相关板块机会
📊 市场整体{'偏暖' if avg_pct >= 0 else '偏弱'}{'，可适当关注主线机会' if avg_pct >= 0 else '，保持谨慎为主'}"""

    return {
        "type": "morning",
        "title": f"小居早报 | {now.strftime('%Y年%m月%d日')} {weekday}",
        "date": now.strftime("%Y年%m月%d日 %H:%M"),
        "content": content,
        "summary": "早报生成完成"
    }


def _format_us_summary(us_stocks: dict) -> str:
    """格式化美股数据"""
    if not us_stocks:
        return "暂无数据"
    lines = []
    for code, data in us_stocks.items():
        if not isinstance(data, dict):
            continue
        pct = data.get("pct", 0)
        emoji = "📈" if pct >= 0 else "📉"
        sign = "+" if pct >= 0 else ""
        price = data.get("price", 0)
        lines.append(f"{emoji} **{data.get('name', code)}** {price:.2f} | {sign}{pct:.2f}%")
    return "\n".join(lines)


def _format_metals_summary(metals: dict) -> str:
    """格式化贵金属数据"""
    if not metals:
        return "暂无数据"
    lines = []
    for code, data in metals.items():
        if not isinstance(data, dict):
            continue
        pct = data.get("pct", 0)
        emoji = "📈" if pct >= 0 else "📉"
        sign = "+" if pct >= 0 else ""
        price = data.get("price", 0)
        name = data.get("name", code)
        unit = data.get("unit", "")
        lines.append(f"{emoji} **{name}**：{price:.2f}{unit} | {sign}{pct:.2f}%")
    return "\n".join(lines)


def _format_news(news_list: list) -> str:
    """格式化新闻列表"""
    if not news_list:
        return "暂无数据"
    lines = []
    for i, item in enumerate(news_list):
        title = item.get("title", "")
        source = item.get("source", "")
        pub_time = item.get("published", "")[:10] if item.get("published") else ""
        if pub_time:
            lines.append(f"{i+1}. {title}（{source} {pub_time}）")
        else:
            lines.append(f"{i+1}. {title}（{source}）")
    return "\n".join(lines)


async def generate_evening_report() -> dict:
    """生成晚报"""
    from routers import stock, precious_metals, hot_search, news, life_tools
    from routers.us_stock import fetch_us_stocks
    from routers.commodity import fetch_commodities

    now = datetime.now()
    weekday = _get_weekday(now)
    calendar_data = life_tools.get_chinese_calendar()

    stocks = {}
    try:
        stocks = await stock.fetch_cn_stocks()
    except Exception as e:
        logger.warning(f"获取A股数据失败: {e}")

    metals = {}
    try:
        metals = await precious_metals.fetch_metals()
    except Exception as e:
        logger.warning(f"获取贵金属数据失败: {e}")

    us_stocks = {}
    try:
        us_stocks = await fetch_us_stocks()
    except Exception as e:
        logger.warning(f"获取美股数据失败: {e}")

    hot = hot_search._cache or {}
    weibo_hot = hot.get("weibo", [])
    douyin_hot = hot.get("douyin", [])

    news_data = {}
    try:
        news_data = await _fetch_news_fresh()
    except Exception as e:
        logger.warning(f"获取新闻数据失败: {e}")

    all_news = news_data.get("news", [])

    finance_news = [n for n in all_news if any(k in n.get("title", "").lower()
               for k in ["财经", "金融", "经济", "银行", "股市", "投资", "股价", "基金", "债券"])]
    tech_news = [n for n in all_news if any(k in n.get("title", "").lower()
               for k in ["科技", "ai", "人工智能", "互联网", "芯片", "技术", "模型", "软件"])]
    ai_news = tech_news
    startup_news = tech_news
    world_news = [n for n in all_news if any(k in n.get("title", "").lower()
               for k in ["国际", "美国", "欧洲", "全球", "外交", "制裁", "峰会"])]

    # 星座运势
    taurus = life_tools.get_horoscope_details("金牛座")
    cancer = life_tools.get_horoscope_details("巨蟹座")

    # 盘面回顾
    all_pct = [data.get("pct", 0) for data in stocks.values() if isinstance(data, dict)]
    avg_pct = sum(all_pct) / len(all_pct) if all_pct else 0

    if avg_pct > 1:
        review = "今日市场整体表现强势，三大指数全线飘红，市场做多情绪高涨"
    elif avg_pct < -1:
        review = "今日市场承压下行，主要指数集体收跌，市场观望情绪浓厚"
    else:
        review = f"今日市场小幅收{'涨' if avg_pct >= 0 else '跌'}，成交量有所变化，结构性特征明显"

    sorted_stocks = sorted(stocks.items(), key=lambda x: x[1].get("pct", 0), reverse=True) if stocks else []
    strongest = sorted_stocks[0] if sorted_stocks else None

    top_weibo = weibo_hot[0].get("title", "") if weibo_hot else ""
    top_douyin = douyin_hot[0].get("title", "") if douyin_hot else ""

    content = f"""**小居晚报 | {now.strftime('%Y年%m月%d日')} {weekday}**

---

**📅 今日复盘**
- 日期：{now.strftime('%Y年%m月%d日')} {weekday}
- 农历：{calendar_data.get('lunar', '农历日期')}
- 星座提醒：金牛座 · 巨蟹座

---

**📋 今日黄历**
- 吉位：东、南（核心吉位）
- 凶位：{random.choice(['西', '北', '东北'])}
- 宜：出行、开业、搬家、祈福、纳财
- 忌：动土、安葬、嫁娶、破土
- 冲煞：冲鼠（壬子年生），煞北

---

**🌟 星座运势（今日回顾）**

**♉ 金牛座（4月20日-5月20日）**
今日运势整体平稳，财运方面有不错的机会，尤其是正财收入表现突出。工作上稳扎稳打，与同事协作顺畅。感情方面，单身者有机会遇到心仪对象，已婚者家庭氛围和睦。健康注意消化系统，饮食宜清淡。

💰 财运：★★★★☆ 稳步上升，正财运势佳
💼 事业：★★★★☆ 稳中求进，人际关系和谐
💙 感情：★★★☆☆ 运势平缓，主动出击有惊喜
🏥 健康：★★★☆☆ 注意肠胃，避免油腻

---

**♋ 巨蟹座（6月21日-7月22日）**
今日运势较为顺利，尤其是家庭和人际关系方面有不错的表现。情绪稳定，直觉敏锐，在需要做决策的事情上往往能押对方向。财运有暗财机会，可能收到意外礼物或补助。健康方面注意休息，不要过度操劳。

💰 财运：★★★★☆ 暗财涌动，可能有额外收入
💼 事业：★★★☆☆ 平稳推进，注意沟通表达
💙 感情：★★★★★ 运势极佳，社交运强，人缘佳
🏥 健康：★★★☆☆ 需注意休息，避免过度疲劳

---

**📊 今日盘面回顾**

{_format_stock_summary(stocks)}

---

**🗽 美股行情**
{_format_us_summary(us_stocks)}

---

**🥇 贵金属**
{_format_metals_summary(metals)}

---

**📱 今日热搜 TOP5**

**微博热搜**
{_format_hot_list(weibo_hot, 5)}

**抖音热搜**
{_format_hot_list(douyin_hot, 5)}

---

**💹 财经资讯回顾（{len(finance_news[:3])}条）**
{_format_news(finance_news[:3])}

---

**🤖 AI & 科技资讯回顾（{len(ai_news[:3])}条）**
{_format_news(ai_news[:3])}

---

**🚀 创业 & 创投回顾（{len(startup_news[:2])}条）**
{_format_news(startup_news[:2])}

---

**🌍 国际要闻回顾（{len(world_news[:2])}条）**
{_format_news(world_news[:2])}

---

**💡 今日收盘总结**
{review}"""

    if strongest:
        content += f"\n\n🏆 今日最强：{strongest[1].get('name', '')}，涨幅{strongest[1].get('pct', 0):+.2f}%"

    content += f"""

---

**🌙 明日展望**
明日市场大概率延续当前格局，建议关注今晚美股走势及外围市场情绪，仓位管理为主，切勿追高。

---

**#靓仔晚间关注**
🔥 今日微博热搜榜首：{top_weibo[:20]}... 可关注相关板块后续发酵
📊 今日市场{'整体偏暖' if avg_pct >= 0 else '整体偏弱'}，明日关注量能变化"""

    return {
        "type": "evening",
        "title": f"小居晚报 | {now.strftime('%Y年%m月%d日')} {weekday}",
        "date": now.strftime("%Y年%m月%d日 %H:%M"),
        "content": content,
        "summary": "晚报生成完成"
    }


@router.get("")
async def get_report(type: str = "morning"):
    """API: 获取报告"""
    if type == "evening":
        return await generate_evening_report()
    else:
        return await generate_morning_report()


@router.get("/morning")
async def get_morning_report():
    return await generate_morning_report()


@router.get("/evening")
async def get_evening_report():
    return await generate_evening_report()
