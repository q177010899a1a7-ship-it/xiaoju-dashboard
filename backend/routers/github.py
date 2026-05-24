"""小居数据监控台 - GitHub热门路由"""
import aiohttp
import json as _json
from fastapi import APIRouter
from services.cache import cache_service
from services.logger import logger
import datetime

router = APIRouter()

# GitHub 真实IP（绕过DNS劫持）
_GITHUB_IP = "20.205.243.168"

# 翻译词典
TRANSLATIONS = {
    "framework": "框架", "library": "库", "toolkit": "工具集", "engine": "引擎",
    "core": "核心", "module": "模块", "package": "包", "cli": "命令行工具",
    "api": "接口", "sdk": "开发包", "ui": "界面", "components": "组件",
    "react": "React组件库", "vue": "Vue组件库", "angular": "Angular组件库",
    "node": "Node.js", "python": "Python", "javascript": "JavaScript",
    "typescript": "TypeScript", "rust": "Rust", "go": "Go语言", "java": "Java",
    "c++": "C++", "swift": "Swift", "kotlin": "Kotlin", "ruby": "Ruby", "php": "PHP",
    "bot": "机器人", "server": "服务器", "client": "客户端", "proxy": "代理",
    "gateway": "网关", "dashboard": "仪表盘", "monitor": "监控", "analytics": "分析",
    "database": "数据库", "cache": "缓存", "queue": "队列", "stream": "流处理",
    "storage": "存储", "file": "文件", "upload": "上传", "download": "下载",
    "rest": "REST", "graphql": "GraphQL", "grpc": "gRPC", "websocket": "WebSocket",
    "ai": "人工智能", "machine learning": "机器学习", "deep learning": "深度学习",
    "neural": "神经网络", "nlp": "自然语言处理", "cv": "计算机视觉",
    "llm": "大语言模型", "gpt": "GPT", "chatbot": "聊天机器人",
    "image": "图像", "text": "文本", "audio": "音频", "video": "视频",
    "speech": "语音", "translation": "翻译", "embedding": "嵌入向量",
    "docker": "Docker", "kubernetes": "K8s", "k8s": "K8s", "container": "容器",
    "ci/cd": "持续集成/部署", "cicd": "持续集成/部署", "deployment": "部署",
    "orchestration": "编排", "microservice": "微服务", "serverless": "无服务器",
    "cloud": "云", "aws": "AWS", "azure": "Azure", "gcp": "GCP",
    "generator": "生成器", "builder": "构建工具", "compiler": "编译器",
    "linter": "代码检查", "formatter": "格式化", "test": "测试", "debug": "调试",
    "profiler": "性能分析", "open source": "开源", "opensource": "开源",
    "awesome": "精选", "list": "清单", "collection": "集合", "resources": "资源",
    "tutorial": "教程", "example": "示例", "starter": "入门", "boilerplate": "脚手架",
    "template": "模板", "wrapper": "封装", "adapter": "适配器", "bridge": "桥接",
    "middleware": "中间件", "plugin": "插件", "extension": "扩展", "integration": "集成",
    "driver": "驱动", "protocol": "协议", "parser": "解析器", "serializer": "序列化",
    "validator": "验证器", "auth": "认证", "security": "安全", "encryption": "加密",
    "crypto": "加密", "payment": "支付", "lightweight": "轻量级", "simple": "简单",
    "fast": "快速", "efficient": "高效", "modern": "现代", "powerful": "强大",
    "easy": "易于使用", "minimal": "极简", "beautiful": "美观", "hackable": "可定制",
    "extensible": "可扩展", "scalable": "可扩展", "reliable": "可靠", "production": "生产级",
}

def translate_description(desc: str) -> str:
    """将英文描述翻译为中文（整句翻译 + 关键词标注）"""
    if not desc:
        return ""
    desc = desc.strip()
    if len(desc) > 500:
        desc = desc[:500]
    
    # 优先尝试整句翻译
    try:
        import urllib.request
        import urllib.parse
        import json
        
        url = 'https://api.mymemory.translated.net/get?' + urllib.parse.urlencode({
            'q': desc,
            'langpair': 'en|zh-CN'
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
    
    # 降级：使用词典关键词标注
    desc_lower = desc.lower()
    result = desc
    sorted_keywords = sorted(TRANSLATIONS.keys(), key=len, reverse=True)
    for kw in sorted_keywords:
        if kw.lower() in desc_lower:
            import re
            pattern = re.compile(re.escape(kw), re.IGNORECASE)
            result = pattern.sub(f"{kw}（{TRANSLATIONS[kw]}）", result)
    return result

def generate_project_summary(project: dict, rank: int) -> str:
    """为单个项目生成150字左右的分析简报"""
    name = project.get("name", "")
    desc = project.get("description", "") or "暂无描述"
    lang = project.get("language", "") or "未知"
    stars = project.get("stars", 0)
    forks = project.get("forks", 0)
    owner = project.get("owner", "")
    
    desc_cn = translate_description(desc)
    if stars > 50000:
        scale = "超级热门"
    elif stars > 10000:
        scale = "非常热门"
    elif stars > 5000:
        scale = "热门"
    elif stars > 1000:
        scale = "较热门"
    else:
        scale = "新兴"
    
    lang_map = {"Python": "Python", "JavaScript": "JavaScript", "TypeScript": "TypeScript",
                "Go": "Go", "Rust": "Rust", "Java": "Java", "C++": "C++", "C": "C",
                "Ruby": "Ruby", "PHP": "PHP", "Swift": "Swift", "Kotlin": "Kotlin"}
    lang_display = lang_map.get(lang, lang)
    
    summary = f"【{rank}. {owner}/{name}】{desc_cn}。该项目属于{scale}项目，使用{lang_display}开发，星标数{stars:,}，Fork数{forks:,}。"
    if len(summary) < 120:
        summary += " 作为当前热门项目，值得关注。"
    elif len(summary) > 200:
        summary = summary[:197] + "..."
    return summary

async def _aio_fetch(path_and_query: str) -> dict:
    """使用aiohttp直连IP获取GitHub数据（绕过DNS劫持）"""
    async with aiohttp.ClientSession(trust_env=False) as session:
        try:
            url = f"https://{_GITHUB_IP}/{path_and_query}"
            logger.info(f"_aio_fetch URL: {url[:100]}")
            async with session.get(
                url,
                headers={
                    "Host": "api.github.com",
                    "User-Agent": "Mozilla/5.0 (XiaoJu-Dashboard/1.0)",
                    "Accept": "application/vnd.github.v3+json",
                },
                ssl=False,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                text = await resp.text()
                logger.info(f"_aio_fetch resp.status={resp.status} body_len={len(text)}")
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 403:
                    logger.warning("GitHub API rate limited")
                    return {"total_count": 0, "items": [], "error": "rate_limit"}
                else:
                    logger.warning(f"GitHub API returned {resp.status}: {text[:200]}")
                    return {"total_count": 0, "items": []}
        except Exception as e:
            logger.error(f"aiohttp fetch failed: {e}")
            return {"total_count": 0, "items": []}

async def fetch_github_trending(since: str = "daily", use_cache: bool = True) -> dict:
    """获取GitHub热门项目"""
    cache_key = f"github_trending_{since}"
    cached = cache_service.get(cache_key)
    if use_cache and cached:
        return cached
    
    logger.info(f"fetch_github_trending({since}): fetching fresh data")
    
    results = {"projects": [], "total": 0, "since": since}
    
    if since == "daily":
        # 查昨天至今的推送（避免当日数据过少）
        date_str = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    elif since == "weekly":
        date_str = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    else:
        date_str = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    
    try:
        # 用原始字符，aiohttp会自动正确编码
        data = await _aio_fetch(
            f"search/repositories?q=pushed:>{date_str}+stars:>500&sort=stars&per_page=30&order=desc"
        )
        
        items = data.get("items", [])[:15]
        for repo in items:
            desc = repo.get("description", "") or ""
            results["projects"].append({
                "name": repo.get("name", ""),
                "full_name": repo.get("full_name", ""),
                "description": desc,
                "description_cn": translate_description(desc),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "language": repo.get("language", ""),
                "url": repo.get("html_url", ""),
                "owner": repo.get("owner", {}).get("login", ""),
                "avatar": repo.get("owner", {}).get("avatar_url", ""),
                "created_at": repo.get("created_at", ""),
            })
        results["total"] = len(results["projects"])
        
    except Exception as e:
        logger.error(f"获取GitHub热门失败: {e}")
        results["error"] = str(e)
    
    ttl_map = {"daily": 1800, "weekly": 3600, "monthly": 21600}
    if use_cache:
        if results.get("projects") and len(results["projects"]) > 0:
            cache_service.set(cache_key, results, ttl=ttl_map.get(since, 1800))
            logger.info(f"GitHub {since}: cached {len(results['projects'])} projects")
        else:
            cache_service.set(cache_key, results, ttl=300)
            logger.warning(f"GitHub {since}: no data, cached for 5min")
    else:
        logger.info(f"GitHub {since}: use_cache=False, skipped cache write")
    return results

async def fetch_github_monthly_report() -> dict:
    """获取月度热门项目分析简报（直接从API获取，不依赖trending缓存）"""
    cache_key = "github_monthly_report"
    cached = cache_service.get(cache_key)
    if cached:
        return cached
    
    # 直接调用_aio_fetch获取月度数据，不走trending缓存
    date_str = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    data = await _aio_fetch(
        f"search/repositories?q=pushed:>{date_str}+stars:>500&sort=stars&per_page=30&order=desc"
    )
    
    projects_raw = data.get("items", [])[:10]
    if not projects_raw:
        return {
            "projects": [],
            "total": 0,
            "type": "monthly_report",
            "generated_at": datetime.datetime.now().isoformat(),
            "error": "no data"
        }
    
    summaries = []
    for i, repo in enumerate(projects_raw, 1):
        desc = repo.get("description", "") or ""
        project = {
            "name": repo.get("name", ""),
            "full_name": repo.get("full_name", ""),
            "description": desc,
            "description_cn": translate_description(desc),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "language": repo.get("language", ""),
            "url": repo.get("html_url", ""),
            "owner": repo.get("owner", {}).get("login", ""),
            "avatar": repo.get("owner", {}).get("avatar_url", ""),
        }
        summaries.append({
            "rank": i,
            "name": project["name"],
            "owner": project["owner"],
            "full_name": project["full_name"],
            "url": project["url"],
            "description": project["description"],
            "description_cn": project["description_cn"],
            "stars": project["stars"],
            "forks": project["forks"],
            "language": project["language"],
            "summary": generate_project_summary(project, i),
        })
    
    results = {
        "projects": summaries,
        "total": len(summaries),
        "type": "monthly_report",
        "generated_at": datetime.datetime.now().isoformat(),
    }
    cache_service.set(cache_key, results, ttl=3600)
    return results

@router.get("")
async def get_github(since: str = "daily"):
    """API: 获取GitHub热门"""
    if since not in ["daily", "weekly", "monthly"]:
        since = "daily"
    return await fetch_github_trending(since)

@router.get("/report")
async def get_github_report():
    """API: 获取月度GitHub热门项目分析简报"""
    return await fetch_github_monthly_report()

@router.get("/topic")
async def get_github_topic(topic: str = "python"):
    """API: 按主题获取GitHub项目"""
    cache_key = f"github_topic_{topic}"
    cached = cache_service.get(cache_key)
    if cached:
        return cached
    
    results = {"projects": [], "topic": topic}
    
    try:
        data = await _aio_fetch(
            f"search/repositories?q=topic:{topic}+stars:>100&sort=stars&per_page=10"
        )
        
        for repo in data.get("items", []):
            desc = repo.get("description", "") or ""
            results["projects"].append({
                "name": repo.get("name", ""),
                "full_name": repo.get("full_name", ""),
                "description": desc,
                "description_cn": translate_description(desc),
                "stars": repo.get("stargazers_count", 0),
                "language": repo.get("language", ""),
                "url": repo.get("html_url", ""),
            })
    except Exception as e:
        logger.error(f"获取GitHub主题项目失败: {e}")
        results["error"] = str(e)
    
    cache_service.set(cache_key, results, ttl=1800)
    return results
