# 🏠 小居数据监控台

小居专属数据监控与推送系统，支持A股行情、美股数据、大宗商品、热搜、新闻资讯、GitHub热门、黄历、星座运势等多样化功能。

## ✨ 功能特性

### Phase 1 - 基础模块
- 📊 **A股行情** - 实时大盘指数监控（上证、深证、创业板、科创板）
- 🥇 **贵金属** - 黄金、白银、铂金等实时价格（美元/盎司）

### Phase 2 - 扩展数据模块
- 🗽 **美股行情** - 纳斯达克、道琼斯、标普500三大指数 + 10支热门股票（苹果、微软、英伟达等）
- 🛢️ **大宗商品** - WTI原油、布伦特原油、铜、铝、大豆、玉米等
- 🔥 **热搜监控** - 微博热搜、抖音热搜（推特/X需要API权限）
- 📰 **科技资讯** - 36氪、钛媒体RSS聚合
- ⚙️ **GitHub热门** - 按星标排序的热门项目

### Phase 3 - 生活工具与推送
- 📅 **今日黄历** - 宜忌查询
- ⭐ **星座运势** - 每日星座运势（含幸运色、守护星等）
- 📰 **小居早报/晚报** - 自动生成每日简报（支持AI生成）
- 📨 **推送服务** - 支持飞书、企业微信Webhook推送
- ⚙️ **配置面板** - 可视化配置刷新频率、Webhook、AI Key等

## 🔧 技术栈

- **前端**: React 18 + Vite + TypeScript + TailwindCSS + Recharts
- **后端**: Python FastAPI + APScheduler + SQLite
- **缓存**: SQLite + 内存缓存
- **部署**: Docker + docker-compose

## 🚀 快速部署

### 环境要求

- Docker >= 20.10
- Docker Compose >= 2.0

### 启动服务

```bash
# 克隆项目
cd xiaoju-dashboard

# 启动服务（前端+后端）
docker-compose up -d --build

# 查看日志
docker-compose logs -f
```

### 访问地址

- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 📡 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/stock` | GET | 获取A股数据 |
| `/api/us-stock` | GET | 获取美股数据（指数+热门股票） |
| `/api/metals` | GET | 获取贵金属数据 |
| `/api/commodity` | GET | 获取大宗商品数据 |
| `/api/hot` | GET | 获取微博热搜 |
| `/api/hot/all` | GET | 获取所有热搜（微博+抖音+推特） |
| `/api/news` | GET | 获取科技资讯 |
| `/api/github` | GET | 获取GitHub热门项目 |
| `/api/life/calendar` | GET | 获取黄历 |
| `/api/life/horoscope` | GET | 获取星座运势 |
| `/api/report` | GET | 获取日报 |
| `/api/push` | POST | 推送消息 |
| `/api/config/` | GET | 获取配置 |
| `/api/config/save` | POST | 保存配置 |
| `/api/config/systemStatus` | GET | 系统状态 |
| `/health` | GET | 健康检查 |

## ⚙️ 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `LOG_LEVEL` | 日志级别 | INFO |
| `REFRESH_INTERVAL` | 数据刷新间隔（秒） | 1800 |
| `FEISHU_WEBHOOK` | 飞书机器人Webhook | - |
| `WECOM_WEBHOOK` | 企业微信机器人Webhook | - |
| `OPENAI_API_KEY` | OpenAI API Key（可选，用于AI生成报告） | - |

## 📊 数据刷新策略

| 数据类型 | 刷新频率 | 说明 |
|----------|----------|------|
| A股、贵金属 | 每30分钟 | 与交易时间同步 |
| 美股、大宗商品 | 每10分钟 | 24小时动态更新 |
| 热搜（微博/抖音） | 每15分钟 | 实时热点追踪 |
| 科技资讯 | 每30分钟 | RSS聚合 |
| GitHub热门 | 每1小时 | 按星标排序 |

## 🗂️ 项目结构

```
xiaoju-dashboard/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── routers/             # API 路由
│   │   ├── stock.py         # A股
│   │   ├── us_stock.py      # 美股
│   │   ├── commodity.py     # 大宗商品
│   │   ├── precious_metals.py # 贵金属
│   │   ├── hot_search.py    # 热搜（微博/抖音/推特）
│   │   ├── news.py          # 新闻资讯
│   │   ├── github.py        # GitHub热门
│   │   ├── life_tools.py    # 黄历/星座
│   │   ├── report.py        # 报告生成
│   │   ├── push.py         # 推送服务
│   │   └── config_router.py # 配置管理API
│   ├── services/            # 服务
│   │   ├── scheduler.py     # 定时任务
│   │   ├── cache.py         # 缓存
│   │   └── logger.py        # 日志
│   ├── utils/               # 工具
│   │   └── rate.py          # 汇率
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/       # 组件
│   │   │   ├── Dashboard.tsx
│   │   │   ├── ModuleContainer.tsx
│   │   │   ├── StockChart.tsx
│   │   │   ├── USStockModule.tsx
│   │   │   ├── CommodityModule.tsx
│   │   │   ├── HotSearchList.tsx
│   │   │   ├── NewsModule.tsx
│   │   │   ├── GitHubModule.tsx
│   │   │   ├── ChineseCalender.tsx
│   │   │   ├── Horoscope.tsx
│   │   │   ├── ReportModule.tsx
│   │   │   └── ConfigPanel.tsx
│   │   ├── hooks/
│   │   │   └── useAutoRefresh.ts
│   │   └── types/
│   │       └── index.ts
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── README.md
```

## 🎨 前端特性

- **拖拽布局**: 使用 react-grid-layout 支持模块拖拽排序
- **响应式设计**: 支持 PC（1920×1080、1366×768、1440×900）+ 平板横屏
- **浅色主题**: 涨红跌绿配色方案
- **自动刷新**: 可配置刷新间隔

## 📝 开发笔记

### 免费API使用情况

| 数据源 | API | 费用 |
|--------|-----|------|
| A股数据 | 新浪财经 | 免费 |
| 美股数据 | Yahoo Finance | 免费 |
| 大宗商品 | Yahoo Finance | 免费 |
| 贵金属 | 新浪财经 | 免费 |
| 微博热搜 | 微博开放API | 免费 |
| 抖音热搜 | 抖音开放API | 免费 |
| 推特热搜 | Twitter API | 需要API Key |
| 科技资讯 | 36氪/钛媒体RSS | 免费 |
| GitHub | GitHub REST API | 免费（限速） |
| 汇率 | exchangerate-api | 免费 |
| 星座运势 | ohmanda.com | 免费 |

## License

MIT License
