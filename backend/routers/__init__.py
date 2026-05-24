"""小居数据监控台 - 路由模块"""
# 本文件用于批量导出路由，不做实际路由注册
# 路由注册在 main.py 中通过 app.include_router() 完成

from . import stock
from . import us_stock
from . import commodity
from . import precious_metals
from . import hot_search
from . import news
from . import github
from . import github_report
from . import life_tools
from . import report
from . import push
from . import crypto
from . import config_router

__all__ = [
    "stock",
    "us_stock",
    "commodity",
    "precious_metals",
    "hot_search",
    "news",
    "github",
    "life_tools",
    "report",
    "push",
    "config_router",
]
