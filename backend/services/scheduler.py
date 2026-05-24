"""小居数据监控台 - 定时任务服务"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import config
from services.logger import logger
from services.cache import cache_service

scheduler = AsyncIOScheduler()

async def refresh_stock_data():
    """刷新A股数据任务"""
    from routers import stock
    try:
        await stock.fetch_cn_stocks()
        logger.info("A股数据刷新完成")
    except Exception as e:
        logger.error(f"A股数据刷新失败: {e}")

async def refresh_us_stock_data():
    """刷新美股数据任务"""
    from routers import us_stock
    try:
        await us_stock.fetch_us_stocks()
        logger.info("美股数据刷新完成")
    except Exception as e:
        logger.error(f"美股数据刷新失败: {e}")

async def refresh_commodity_data():
    """刷新大宗商品数据任务"""
    from routers import commodity
    try:
        await commodity.fetch_commodities()
        logger.info("大宗商品数据刷新完成")
    except Exception as e:
        logger.error(f"大宗商品数据刷新失败: {e}")

async def refresh_metal_data():
    """刷新贵金属数据任务"""
    from routers import precious_metals
    try:
        await precious_metals.fetch_metals()
        logger.info("贵金属数据刷新完成")
    except Exception as e:
        logger.error(f"贵金属数据刷新失败: {e}")

async def refresh_hot_search():
    """刷新热搜数据任务"""
    from routers import hot_search
    try:
        await hot_search.fetch_weibo_hot()
        await hot_search.fetch_douyin_hot()
        await hot_search.fetch_twitter_hot()
        logger.info("热搜数据刷新完成")
    except Exception as e:
        logger.error(f"热搜数据刷新失败: {e}")

async def refresh_news():
    """刷新新闻数据任务"""
    from routers import news
    try:
        await news.fetch_all_news()
        logger.info("新闻数据刷新完成")
    except Exception as e:
        logger.error(f"新闻数据刷新失败: {e}")

async def refresh_github():
    """刷新GitHub热门数据任务"""
    from routers import github
    try:
        await github.fetch_github_trending(use_cache=False)
        logger.info("GitHub热门数据刷新完成")
    except Exception as e:
        logger.error(f"GitHub热门数据刷新失败: {e}")

async def cleanup_cache():
    """清理过期缓存"""
    cache_service.clear_expired()
    logger.info("缓存清理完成")

def start_scheduler():
    """启动定时任务（每小时整点刷新一次）"""
    from apscheduler.triggers.cron import CronTrigger
    
    # A股：每小时的第5分钟刷新
    scheduler.add_job(
        refresh_stock_data,
        trigger=CronTrigger(minute=5, second=0),
        id="refresh_stock",
        name="刷新A股数据",
        replace_existing=True
    )
    
    # 美股：每小时的第10分钟刷新
    scheduler.add_job(
        refresh_us_stock_data,
        trigger=CronTrigger(minute=10, second=0),
        id="refresh_us_stock",
        name="刷新美股数据",
        replace_existing=True
    )
    
    # 大宗商品：每小时的第15分钟刷新
    scheduler.add_job(
        refresh_commodity_data,
        trigger=CronTrigger(minute=15, second=0),
        id="refresh_commodity",
        name="刷新大宗商品数据",
        replace_existing=True
    )
    
    # 贵金属：每小时的第20分钟刷新
    scheduler.add_job(
        refresh_metal_data,
        trigger=CronTrigger(minute=20, second=0),
        id="refresh_metals",
        name="刷新贵金属数据",
        replace_existing=True
    )
    
    # 热搜：每小时的第25分钟刷新
    scheduler.add_job(
        refresh_hot_search,
        trigger=CronTrigger(minute=25, second=0),
        id="refresh_hot",
        name="刷新热搜数据",
        replace_existing=True
    )
    
    # 新闻：每小时的第30分钟刷新
    scheduler.add_job(
        refresh_news,
        trigger=CronTrigger(minute=30, second=0),
        id="refresh_news",
        name="刷新新闻数据",
        replace_existing=True
    )
    
    # GitHub：每小时的第35分钟刷新
    scheduler.add_job(
        refresh_github,
        trigger=CronTrigger(minute=35, second=0),
        id="refresh_github",
        name="刷新GitHub热门",
        replace_existing=True
    )
    
    # 清理缓存：每小时的第0分钟
    scheduler.add_job(
        cleanup_cache,
        trigger=CronTrigger(minute=0, second=0),
        id="cleanup_cache",
        name="清理过期缓存",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("定时任务已启动，每小时整点刷新各模块数据")

def stop_scheduler():
    """停止定时任务"""
    scheduler.shutdown(wait=False)
    logger.info("定时任务已停止")
