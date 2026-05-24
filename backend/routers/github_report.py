"""小居数据监控台 - GitHub每日热门分析报告（真实Trending数据源）"""
import httpx
import asyncio
import json
import re
import subprocess
import datetime
import urllib.request
from fastapi import APIRouter
from services.logger import logger

router = APIRouter()

_GITHUB_TRENDING_URL = "https://github.com/trending"
_SOCKS5_PROXY = "socks5h://127.0.0.1:20809"
_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# 飞书应用身份推送
_FEISHU_APP_ID = "cli_a94d32b716b8dccd"
_FEISHU_APP_SECRET = "sVbxWF7MNCepX2UMonmxidIIPYdJ4LMR"
_FEISHU_USER_OPEN_ID = "ou_a5779a94565733ace8dadf91a09287d1"
_FEISHU_API_BASE = "https://open.feishu.cn/open-apis"


async def _get_feishu_token() -> str | None:
    """获取飞书tenant_access_token"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{_FEISHU_API_BASE}/auth/v3/tenant_access_token/internal",
            json={"app_id": _FEISHU_APP_ID, "app_secret": _FEISHU_APP_SECRET}
        )
        data = resp.json()
        if data.get("code") == 0:
            return data["tenant_access_token"]
        logger.error(f"获取飞书token失败: {data}")
        return None


async def _send_feishu_message(text: str) -> dict:
    """通过飞书应用身份发送消息给用户"""
    token = await _get_feishu_token()
    if not token:
        return {"success": False, "error": "获取飞书access_token失败"}
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{_FEISHU_API_BASE}/im/v1/messages?receive_id_type=open_id",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "receive_id": _FEISHU_USER_OPEN_ID,
                "msg_type": "text",
                "content": json.dumps({"text": text})
            }
        )
        result = resp.json()
        if result.get("code") == 0:
            return {"success": True}
        logger.error(f"飞书消息发送失败: {result}")
        return {"success": False, "error": str(result)}


# ============ 整句翻译 ============
_TRANSLATIONS = {
    "framework": "框架", "library": "库", "toolkit": "工具集", "engine": "引擎",
    "core": "核心", "module": "模块", "package": "包", "cli": "命令行工具",
    "api": "接口", "sdk": "开发包", "ui": "界面", "components": "组件",
    "react": "React", "vue": "Vue", "angular": "Angular",
    "python": "Python", "javascript": "JavaScript", "typescript": "TypeScript",
    "rust": "Rust", "go": "Go", "java": "Java", "c++": "C++",
    "bot": "机器人", "server": "服务器", "client": "客户端", "proxy": "代理",
    "gateway": "网关", "dashboard": "仪表盘", "monitor": "监控", "analytics": "分析",
    "database": "数据库", "cache": "缓存", "queue": "队列", "stream": "流处理",
    "storage": "存储", "file": "文件",
    "rest": "REST", "graphql": "GraphQL", "grpc": "gRPC", "websocket": "WebSocket",
    "ai": "人工智能", "machine learning": "机器学习", "deep learning": "深度学习",
    "llm": "大语言模型", "gpt": "GPT", "chatbot": "聊天机器人",
    "docker": "Docker", "kubernetes": "K8s", "container": "容器",
    "ci/cd": "持续集成/部署", "deployment": "部署", "microservice": "微服务",
    "open source": "开源", "awesome": "精选",
    "plugin": "插件", "middleware": "中间件", "integration": "集成",
    "auth": "认证", "security": "安全", "encryption": "加密",
}

def translate_desc(desc: str) -> str:
    """整句翻译 + 关键词标注"""
    if not desc:
        return ""
    desc = desc.strip()[:500]

    try:
        import urllib.parse
        url = 'https://api.mymemory.translated.net/get?' + urllib.parse.urlencode({
            'q': desc, 'langpair': 'en|zh-CN'
        })
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data.get('responseStatus') == 200:
                translated = data['responseData']['translatedText'].strip()
                if translated and translated != desc:
                    return translated
    except Exception:
        pass

    # 降级：关键词标注
    result = desc
    for kw, cn in sorted(_TRANSLATIONS.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        result = pattern.sub(f"{kw}（{cn}）", result)
    return result


# ============ 抓取GitHub Trending（真实数据） ============
def _fetch_trending_html() -> str:
    """通过SOCKS5代理获取GitHub Trending页面HTML（urllib + fallback curl）"""
    # 优先：urllib + socks5h（不走shell，环境无关）
    try:
        proxy_handler = urllib.request.ProxyHandler({'socks5h': '127.0.0.1:20809'})
        opener = urllib.request.build_opener(proxy_handler)
        req = urllib.request.Request(
            _GITHUB_TRENDING_URL,
            headers={
                'User-Agent': _USER_AGENT,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
        )
        with opener.open(req, timeout=50) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        logger.warning(f"github_report urllib失败({e})，回退到curl")

    # Fallback：curl（subprocess）
    result = subprocess.run(
        ['curl', '-sL', '--max-time', '55',
         '--proxy', _SOCKS5_PROXY,
         '-A', _USER_AGENT,
         '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
         '-H', 'Accept-Language: en-US,en;q=0.9',
         _GITHUB_TRENDING_URL],
        capture_output=True, timeout=60
    )
    return result.stdout.decode('utf-8', errors='replace')


def _parse_trending(html: str) -> list:
    """解析GitHub Trending HTML，提取Top5"""
    raw_articles = re.findall(
        r'<article[^>]*class="Box-row"[^>]*>(.*?)</article>',
        html, re.DOTALL
    )

    results = []
    for raw in raw_articles:
        if len(results) >= 5:
            break

        # 获取仓库全名
        m = re.search(r'return_to=%2F([A-Za-z0-9_-]+%2F[A-Za-z0-9_.-]+?)(?:&|")', raw)
        if m:
            full_name = m.group(1).replace('%2F', '/')
        else:
            m2 = re.search(r'<h2[^>]*>.*?href="(/\S+?/)(\S+?)"', raw, re.DOTALL)
            if m2:
                full_name = m2.group(1).rstrip('/').lstrip('/') + m2.group(2)
            else:
                continue

        name = full_name.split('/')[-1] if '/' in full_name else full_name

        # 描述
        desc_m = re.search(r'<p[^>]*>\s*([A-Za-z][^<]{15,})\s*</p>', raw)
        description = desc_m.group(1).strip() if desc_m else ''

        # 编程语言
        lang_m = re.search(r'programmingLanguage"[^>]*>([^<]+)</span>', raw)
        language = lang_m.group(1).strip() if lang_m else ''

        # 总stars - 找第一个数字（格式: ">    23,130</a>"，数字前有换行+空格）
        all_nums = re.findall(r'>\s*(\d[\d,]+)\s*</a>', raw)
        stars = 0
        if all_nums:
            try:
                stars = int(all_nums[0].replace(',', ''))
            except:
                stars = 0

        # 今日新增stars
        today_m = re.search(r'([0-9,]+)\s*stars today', raw)
        stars_today = today_m.group(1) if today_m else ''

        # URL
        url = f'https://github.com/{full_name}'

        results.append({
            'rank': len(results) + 1,
            'name': name,
            'full_name': full_name,
            'description': description,
            'description_cn': translate_desc(description),
            'language': language,
            'stars': stars,
            'stars_today': stars_today,
            'url': url,
        })

    return results


# ============ 深度分析 ============
def _analyze_project(project: dict, rank: int) -> dict:
    """对单个项目进行深度分析"""
    name = project["name"]
    full_name = project["full_name"]
    desc_en = project["description"]
    desc_cn = project["description_cn"]
    stars = project["stars"]
    stars_today = project["stars_today"]
    language = project["language"]
    url = project["url"]

    desc_lower = desc_en.lower()

    # 适用场景识别
    scenarios = []
    value_points = []

    if any(k in desc_lower for k in ["ai", "llm", "gpt", "machine learning", "deep learning", "neural", "nlp", "chatbot", "agent", "genai"]):
        scenarios.append("🤖 AI开发")
        value_points.append("可参考其AI应用架构，设计跨境电商智能选品、客服机器人等场景")
    if "agent" in desc_lower or "agentic" in desc_lower:
        scenarios.append("🧠 Agent开发")
        value_points.append("直接参考Agent设计模式，构建选品Agent或运营自动化Agent")
    if any(k in desc_lower for k in ["bot", "telegram", "discord", "slack"]):
        scenarios.append("💬 社交/客服机器人")
        value_points.append("快速搭建多平台客服机器人，降低跨境售后成本")
    if any(k in desc_lower for k in ["scraper", "crawl", "spider", "fetch", "parse"]):
        scenarios.append("🕷️ 数据采集")
        value_points.append("获取竞品数据、市场数据，提升选品效率")
    if any(k in desc_lower for k in ["api", "sdk", "wrapper", "client"]) and "🔌 API集成" not in scenarios:
        scenarios.append("🔌 API集成")
        value_points.append("对接亚马逊、Shopify等平台API，构建自动化管理系统")
    if any(k in desc_lower for k in ["dashboard", "monitor", "analytics", "bi", "visualization"]):
        scenarios.append("📊 数据可视化")
        value_points.append("参考其前端架构或直接集成，完善运营监控大屏")
    if any(k in desc_lower for k in ["docker", "kubernetes", "deploy", "ci/cd", "pipeline"]):
        scenarios.append("🚀 DevOps/部署")
        value_points.append("优化CI/CD流程，实现代码提交即部署的自动化发布体系")
    if any(k in desc_lower for k in ["auth", "login", "oauth", "jwt", "security"]):
        scenarios.append("🔐 认证安全")
        value_points.append("提升系统安全水位，防止账户盗用和数据泄露")
    if any(k in desc_lower for k in ["ecommerce", "shop", "store", "cart", "payment", "stripe", "shopify", "amazon"]):
        scenarios.append("🛒 电商建站")
        value_points.append("快速搭建电商后台、商品管理系统")
    if any(k in desc_lower for k in ["video", "photo", "media", "image", "gallery"]):
        scenarios.append("📸 媒体管理")
        value_points.append("用于商品图片/视频管理和处理，提升Listing制作效率")
    if any(k in desc_lower for k in ["open source", "awesome", "list", "resources", "curated"]):
        scenarios.append("📚 学习资源")
        value_points.append("系统学习某领域最佳实践，快速补齐技术短板")
    if any(k in desc_lower for k in ["cli", "command", "tool", "generator", "scaffold"]):
        scenarios.append("🛠️ 工具开发")
        value_points.append("开发内部CLI工具，提升研发效率")

    if not scenarios:
        scenarios.append("🔧 通用工具")
        value_points.append("深入了解其具体用途后再评估潜在价值")

    # 技术栈
    tech_map = {
        "Python": "Python", "JavaScript": "JS", "TypeScript": "TS",
        "Go": "Go", "Rust": "Rust", "Java": "Java", "C++": "C++",
        "Ruby": "Ruby", "PHP": "PHP", "Kotlin": "Kotlin", "Swift": "Swift",
        "Shell": "Shell", "C": "C"
    }
    tech_stack = [tech_map.get(language, language)]

    # 热门度
    stars_num = stars
    if stars_num > 50000:
        popularity = "🔥 顶流项目"
    elif stars_num > 10000:
        popularity = "⭐ 热门项目"
    elif stars_num > 1000:
        popularity = "📈 上升期项目"
    else:
        popularity = "🆕 新兴项目"

    return {
        "rank": rank,
        "name": name,
        "full_name": full_name,
        "url": url,
        "description_en": desc_en,
        "description_cn": desc_cn,
        "stars": stars,
        "stars_today": stars_today,
        "language": language,
        "scenarios": scenarios,
        "value_points": value_points,
        "tech_stack": tech_stack,
        "popularity": popularity,
    }


def _format_report(analyses: list, date_str: str) -> str:
    """格式化飞书消息 - 优化版：易读性优先"""
    if not analyses:
        return f"📊 GitHub热门日报 | {date_str}\n\n⚠️ 今日暂无热门数据，请稍后重试"

    # ===== 顶部3秒概览 =====
    overview_lines = ["📊 **GitHub 每日热门速览**", f"🗓️ {date_str} | by 小居", ""]
    overview_lines.append("┌────┬─────────────────┬──────┬────────┬──────────────────┐")
    overview_lines.append("│ #  │ 项目                        │语言  │ Stars  │ 价值定位             │")
    overview_lines.append("├────┼─────────────────┼──────┼────────┼──────────────────┤")
    for a in analyses:
        rank = f"#{a['rank']}"
        name = a['name'][:18]
        lang = (a['language'] or '—')[:6]
        stars_k = f"{a['stars']/1000:.1f}k" if a['stars'] > 999 else str(a['stars'] or '?')
        value_tag = a['scenarios'][0] if a['scenarios'] else '🔧'
        overview_lines.append(f"│ {rank:<3} │ {name:<19} │ {lang:<6} │ {stars_k:<6} │ {value_tag} │")
    overview_lines.append("└────┴─────────────────┴──────┴────────┴──────────────────┘")
    overview_lines.append("")
    overview_lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    overview_lines.append("")

    # ===== 每个项目详情 =====
    sections = []
    for a in analyses:
        stars_display = f"{a['stars']:,}" if a['stars'] else '?'
        today_display = a['stars_today'] if a['stars_today'] else ""
        lang_badge = f"[{a['language']}]" if a['language'] else ""

        # 价值点精炼：去重 + 限制3条
        raw_values = a.get('value_points', [])
        unique_values = []
        seen_core = set()
        for v in raw_values:
            core = v[:15].lower()
            if core not in seen_core:
                seen_core.add(core)
                unique_values.append(v)
        value_lines = unique_values[:3]

        # 为什么值得关注
        stars_num = a['stars'] or 0
        if stars_num > 50000:
            focus = "🏆 顶流项目，全球开发者都在用。重点看它的架构设计和工程实践。"
        elif stars_num > 10000:
            focus = "⭐ 热门项目，有一定生态积累。可重点学习其核心实现思路。"
        elif stars_num > 1000:
            focus = "📈 上升期项目，值得关注。看它解决了什么具体问题。"
        else:
            focus = "🆕 新兴项目，保持好奇。了解它瞄准的痛点是否真实。"

        section = f"""🔢 **#{a['rank']} {a['full_name']}** {lang_badge}
   ⭐ {stars_display} {f'📈+{today_display}今日' if today_display else '📈今日?'}  |  {a.get('popularity', '')}
   📌 {a['description_cn'] or a['description_en'] or '（暂无描述）'}

   🎯 {''.join(a['scenarios'])}

   💡 **值得关注的点**:
   {' '.join(f'▸ {v}' for v in value_lines) if value_lines else f'▸ {focus}'}

   🔗 {a['url']}"""

        sections.append(section)

    footer = """
━━━━━━━━━━━━━━━━━━━━━━
🌙 每日21:00自动推送 | 持续追踪前沿项目
💡 点击项目名可直接访问仓库"""

    return "\n".join(overview_lines + sections) + footer


# ============ 推送 ============
async def push_github_report() -> dict:
    """生成并推送GitHub日报到飞书"""
    import config as cfg

    date_str = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M")

    html = _fetch_trending_html()
    if not html or len(html) < 10000:
        logger.warning(f"GitHub日报：获取HTML失败，长度={len(html) if html else 0}")
        return {"success": False, "error": "获取页面失败"}

    projects = _parse_trending(html)
    if not projects:
        logger.warning("GitHub日报：解析无结果")
        return {"success": False, "error": "解析失败"}

    analyses = [_analyze_project(p, i+1) for i, p in enumerate(projects)]
    report_text = _format_report(analyses, date_str)

    result = await _send_feishu_message(report_text)
    if result.get("success"):
        logger.info(f"GitHub日报推送成功，{len(analyses)}个项目")
        return {"success": True, "projects_count": len(analyses)}
    else:
        logger.error(f"GitHub日报推送失败: {result.get('error')}")
        return result


# ============ API ============
@router.post("/push")
async def api_push_github_report():
    """API: 手动触发GitHub日报推送"""
    return await push_github_report()

@router.get("/report")
async def api_get_github_report():
    """API: 获取GitHub日报内容（不推送）"""
    html = _fetch_trending_html()
    if not html or len(html) < 10000:
        return {"projects": [], "total": 0, "error": "fetch_failed"}

    projects = _parse_trending(html)
    if not projects:
        return {"projects": [], "total": 0, "error": "parse_failed"}

    analyses = [_analyze_project(p, i+1) for i, p in enumerate(projects)]
    date_str = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M")
    return {
        "projects": analyses,
        "total": len(analyses),
        "formatted": _format_report(analyses, date_str),
        "date": date_str,
    }
