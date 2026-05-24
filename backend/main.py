"""小居数据监控台 - FastAPI 主入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import config
from services.logger import logger
from services.scheduler import start_scheduler, stop_scheduler
import os

# 路由导入
from routers import stock, us_stock, commodity, precious_metals, hot_search, news, life_tools, report, push, crypto
from routers import github, github_report, config_router, aihot

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "../frontend/dist")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("小居数据监控台启动...")
    
    # 启动定时任务
    start_scheduler()
    
    # 初始数据：异步加载（后台运行，不阻塞启动）
    import asyncio
    asyncio.create_task(_load_initial_data())
    
    logger.info("小居数据监控台启动完成")
    
    yield
    
    # 关闭
    stop_scheduler()
    logger.info("小居数据监控台关闭")


async def _load_initial_data():
    """后台加载初始数据（启动后立即运行）"""
    import asyncio
    try:
        # 并行加载各模块初始数据
        await asyncio.gather(
            stock.fetch_cn_stocks(),
            precious_metals.fetch_metals(),
            hot_search.fetch_weibo_hot(),
            hot_search.fetch_douyin_hot(),
            us_stock.fetch_us_stocks(),
            commodity.fetch_commodities(),
            return_exceptions=True
        )
        logger.info("初始数据加载完成")
    except Exception as e:
        logger.error(f"初始数据加载失败: {e}")

app = FastAPI(
    title="小居数据监控台",
    description="小居专属数据监控与推送系统",
    version="1.1.0",
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(stock.router, prefix="/api/stock", tags=["股票"])
app.include_router(us_stock.router, prefix="/api/us-stock", tags=["美股"])
app.include_router(commodity.router, prefix="/api/commodity", tags=["大宗商品"])
app.include_router(precious_metals.router, prefix="/api/metals", tags=["贵金属"])
app.include_router(hot_search.router, prefix="/api/hot", tags=["热搜"])
app.include_router(news.router, prefix="/api/news", tags=["新闻"])
app.include_router(github.router, prefix="/api/github", tags=["GitHub"])
app.include_router(github_report.router, prefix="/api/github-report", tags=["GitHub日报"])
app.include_router(life_tools.router, prefix="/api/life", tags=["生活工具"])
app.include_router(report.router, prefix="/api/report", tags=["报告"])
app.include_router(push.router, prefix="/api/push", tags=["推送"])
app.include_router(config_router.router, prefix="/api/config", tags=["配置"])
app.include_router(crypto.router, prefix="/api/crypto", tags=["虚拟货币"])
app.include_router(aihot.router, prefix="/api/aihot", tags=["AI HOT"])

@app.get("/")
async def root():
    """根路径 - 返回前端页面"""
    index_path = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "name": "小居数据监控台",
        "version": "1.1.0",
        "status": "running"
    }

# 挂载静态文件（API路径优先）
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}

@app.get("/api/status")
async def status():
    """系统状态"""
    return await config_router.api_get_system_status()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
