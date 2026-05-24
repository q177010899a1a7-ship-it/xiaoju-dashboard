"""小居数据监控台 - 生活工具路由（黄历、星座）"""
from datetime import datetime
import httpx
from fastapi import APIRouter
import config
from services.cache import cache_service
from services.logger import logger

router = APIRouter()

def get_chinese_calendar() -> dict:
    """获取黄历信息"""
    from lunarcalendar import Converter

    now = datetime.now()

    # 计算农历
    try:
        lunar = Converter.Solar2Lunar(now)
        lunar_str = f"农历{lunar.month}月{lunar.day}日"
    except Exception:
        lunar_str = "农历日期"

    # 宜忌吉日（简化版本，可后续接API增强）
    yi_list = ["出行", "开市", "祭祀", "纳财", "嫁娶"]
    ji_list = ["动土", "破土", "安葬"]

    # 吉日：周末较好，工作日一般
    if now.weekday() >= 5:
        jiri = "天恩日"
        yi_list = ["出行", "开业", "搬家", "祈福", "纳财"]
        ji_list = ["动土", "安葬", "嫁娶", "破土"]
    else:
        jiri = "青龙日"

    calendar_data = {
        "date": now.strftime("%Y年%m月%d日"),
        "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()],
        "lunar": lunar_str,
        "yi": yi_list,
        "ji": ji_list,
        "jiri": jiri,
        "xingzuo": get_constellation(now.month, now.day),
    }

    return calendar_data


def get_constellation(month: int, day: int) -> str:
    """根据日期获取星座"""
    constellations = [
        ("01-19", "摩羯座"), ("01-20", "水瓶座"), ("02-18", "水瓶座"),
        ("02-19", "双鱼座"), ("03-20", "双鱼座"), ("03-21", "白羊座"),
        ("04-19", "白羊座"), ("04-20", "金牛座"), ("05-20", "金牛座"),
        ("05-21", "双子座"), ("06-20", "双子座"), ("06-21", "巨蟹座"),
        ("07-22", "巨蟹座"), ("07-23", "狮子座"), ("08-22", "狮子座"),
        ("08-23", "处女座"), ("09-22", "处女座"), ("09-23", "天秤座"),
        ("10-22", "天秤座"), ("10-23", "天蝎座"), ("11-21", "天蝎座"),
        ("11-22", "射手座"), ("12-21", "射手座"), ("12-22", "摩羯座"),
    ]
    
    date_str = f"{month:02d}-{day:02d}"
    for boundary, sign in constellations:
        if date_str <= boundary:
            return sign
    return "摩羯座"


def get_horoscope_details(sign: str) -> dict:
    """获取星座详细信息"""
    horoscopes = {
        "白羊座": {"element": "火", "planet": "火星", "lucky": ["红色", "白色", "金色"], "today": "适合开展新项目"},
        "金牛座": {"element": "土", "planet": "金星", "lucky": ["绿色", "金色", "橙色"], "today": "财务运势较好"},
        "双子座": {"element": "风", "planet": "水星", "lucky": ["黄色", "银色", "蓝色"], "today": "沟通运佳"},
        "巨蟹座": {"element": "水", "planet": "月亮", "lucky": ["白色", "银色", "绿色"], "today": "家庭运不错"},
        "狮子座": {"element": "火", "planet": "太阳", "lucky": ["金色", "黄色", "紫色"], "today": "表现力强"},
        "处女座": {"element": "土", "planet": "水星", "lucky": ["灰色", "米色", "绿色"], "today": "注意细节"},
        "天秤座": {"element": "风", "planet": "金星", "lucky": ["粉色", "浅蓝色", "银色"], "today": "社交运好"},
        "天蝎座": {"element": "水", "planet": "冥王星", "lucky": ["深红色", "黑色", "深蓝色"], "today": "洞察力强"},
        "射手座": {"element": "火", "planet": "木星", "lucky": ["紫色", "蓝色", "绿色"], "today": "适合旅行"},
        "摩羯座": {"element": "土", "planet": "土星", "lucky": ["灰色", "棕色", "黑色"], "today": "事业运上升"},
        "水瓶座": {"element": "风", "planet": "天王星", "lucky": ["蓝色", "银色", "黄色"], "today": "创意十足"},
        "双鱼座": {"element": "水", "planet": "海王星", "lucky": ["白色", "蓝色", "绿色"], "today": "直觉敏锐"},
    }
    
    return horoscopes.get(sign, {"element": "水", "planet": "月亮", "lucky": ["白色"], "today": "今日运势平稳"})


# 进程内缓存（一天一次）
_horoscope_cache: dict = {}


_SIGN_EN = {
    "白羊座": "aries", "金牛座": "taurus", "双子座": "gemini",
    "巨蟹座": "cancer", "狮子座": "leo", "处女座": "virgo",
    "天秤座": "libra", "天蝎座": "scorpio", "射手座": "sagittarius",
    "摩羯座": "capricorn", "水瓶座": "aquarius", "双鱼座": "pisces",
}


async def _translate_to_chinese(text: str) -> str:
    """直接解析英文运势原文，生成中文摘要（不依赖外部翻译API）"""
    if not text:
        return ""
    return text  # 返回英文原文，前端直接解析英文关键词生成中文


async def fetch_horoscope_from_api(sign: str) -> dict:
    """从免费API获取星座运势，带缓存"""
    today = datetime.now().strftime("%Y-%m-%d")
    cache_key = f"{sign}:{today}"
    if cache_key in _horoscope_cache:
        return _horoscope_cache[cache_key]

    # 中文星座名转英文（ohmanda 不支持中文 URL）
    sign_en = _SIGN_EN.get(sign, sign.lower().replace("座", ""))
    url = f"https://ohmanda.com/api/horoscope/{sign_en}/"

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
            text = resp.text
            if not text or len(text) < 10:
                return None
            import json as _json
            data = _json.loads(text)

            if data.get("horoscope"):
                en_text = data.get("horoscope", "")
                # 翻译为中文
                zh_text = await _translate_to_chinese(en_text)
                result = {
                    "sign": sign,
                    "date": datetime.now().strftime("%Y年%m月%d日"),
                    "horoscope": zh_text,
                    "api_source": "ohmanda",
                }
                _horoscope_cache[cache_key] = result
                return result
    except Exception as e:
        logger.error(f"获取星座运势API失败: {e}")

    return None


@router.get("/calendar")
def get_calendar():
    """API: 获取黄历"""
    return get_chinese_calendar()


@router.get("/horoscope")
async def get_horoscope(sign: str = None):
    """API: 获取星座运势"""
    if sign is None:
        now = datetime.now()
        sign = get_constellation(now.month, now.day)
    
    api_result = await fetch_horoscope_from_api(sign)
    
    if api_result:
        details = get_horoscope_details(sign)
        return {
            **details,
            **api_result,
        }
    else:
        details = get_horoscope_details(sign)
        return {
            "sign": sign,
            "date": datetime.now().strftime("%Y年%m月%d日"),
            **details
        }
