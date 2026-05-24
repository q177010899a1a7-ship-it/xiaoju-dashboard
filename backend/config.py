"""小居数据监控台 - 配置管理"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 数据目录
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# 日志配置
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 缓存配置
CACHE_TTL = 300  # 5分钟
CACHE_DIR = DATA_DIR / "cache.db"

# 刷新间隔（秒）
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "1800"))  # 默认30分钟

# 新浪财经 API
SINA_STOCK_URL = "https://hq.sinajs.cn/list={symbols}"
SINA_METAL_URL = "https://hq.sinajs.cn/list={symbols}"

# Yahoo Finance
YAHOO_FINANCE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

# 微博热搜
WEIBO_HOT_URL = "https://weibo.com/ajax/side/hotSearch"

# 抖音热搜
DOUYIN_HOT_URL = "https://www.iesdouyin.com/web/api/v2/hotsearch/broad_cast/"

# 汇率 API
EXCHANGE_RATE_URL = "https://api.exchangerate-api.com/v4/latest/USD"

# 飞书 Webhook
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK", "")

# 企业微信 Webhook
WECOM_WEBHOOK = os.getenv("WECOM_WEBHOOK", "")

# OpenAI API Key (用于AI报告生成)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# A股指数代码
CN_STOCK_CODES = {
    "sh000001": "上证指数",
    "sz399001": "深证成指",
    "sz399006": "创业板指",
    "sh000688": "科创50",
}

# 贵金属代码（腾讯财经接口 hf_）
# 注意：铂金(hf_PL)和钯金在腾讯财经暂无可用代码，目前仅支持黄金和白银
METAL_CODES = {
    "hf_GC": "黄金(美元/盎司)",
    "hf_SI": "白银(美元/盎司)",
    # "hf_PL": "铂金(美元/盎司)",  # 暂无可用数据
    # "hf_PD": "钯金(美元/盎司)",   # 暂无可用数据
}

# 美股指数代码
US_INDEX_CODES = {
    "^IXIC": "纳斯达克综合",
    "^DJI": "道琼斯工业",
    "^GSPC": "标普500",
}

# 美股热门股票代码
US_STOCK_CODES = {
    "AAPL": "苹果",
    "MSFT": "微软",
    "GOOGL": "谷歌",
    "AMZN": "亚马逊",
    "TSLA": "特斯拉",
    "NVDA": "英伟达",
    "META": "Meta",
    "BRK-B": "伯克希尔哈撒韦",
    "JPM": "摩根大通",
    "V": "Visa",
}

# 大宗商品代码（使用新浪财经接口，格式如 CU0, AL0, AU0 等）
COMMODITY_CODES = {
    # 有色金属
    "CU0": {"name": "沪铜", "unit": "元/吨"},
    "AL0": {"name": "沪铝", "unit": "元/吨"},
    "ZN0": {"name": "沪锌", "unit": "元/吨"},
    "NI0": {"name": "沪镍", "unit": "元/吨"},
    # 贵金属（国内期货）
    "AU0": {"name": "黄金", "unit": "元/克"},
    "AG0": {"name": "白银", "unit": "元/千克"},
    # 橡胶
    "RU0": {"name": "橡胶", "unit": "元/吨"},
    # 农产品
    "SR0": {"name": "白糖", "unit": "元/吨"},
    "RM0": {"name": "菜粕", "unit": "元/吨"},
    "M0":  {"name": "豆粕", "unit": "元/吨"},
    "Y0":  {"name": "豆油", "unit": "元/吨"},
    "P0":  {"name": "棕榈油", "unit": "元/吨"},
    "L0":  {"name": "塑料", "unit": "元/吨"},
}

# 新闻RSS源（扩充至10+信源）
NEWS_RSS_SOURCES = {
    # 科技媒体
    "36kr": "https://36kr.com/feed",
    "tmtpost": "https://www.tmtpost.com/rss",
    "ithome": "https://www.ithome.com/rss/",
    "lieyunwang": "https://www.lieyunpro.com/feed",
    "techcrunch": "https://techcrunch.com/feed/",
    # 财经媒体
    "wallstreetcn": "https://wallstreetcn.com/rss",
    "caijing": "https://www.caijing.com.cn/rss.xml",
    "第一时间": "https://yidianzixun.com/rss.xml",
    # 国际综合
    "reuters": "https://feeds.reuters.com/reuters/businessNews",
    "bbc": "https://feeds.bbci.co.uk/news/business/rss.xml",
    # AI/技术专题
    "venturebeat_ai": "https://venturebeat.com/category/ai/feed/",
    "mit_tech": "https://www.technologyreview.com/feed/",
}

# 星座运势API
HOROSCOPE_API_URL = "https://ohmanda.com/api/horoscope/{sign}"
