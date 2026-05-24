import React, { useState, useEffect, useCallback } from 'react';
import { Responsive, WidthProvider, Layout } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

import { ModuleContainer } from './ModuleContainer';
import { StockChart } from './StockChart';
import { USStockModule } from './USStockModule';
import { CommodityModule } from './CommodityModule';
import { HotSearchList } from './HotSearchList';
import { AIHotModule } from './AIHotModule';
import { GitHubModule } from './GitHubModule';
import { ChineseCalender } from './ChineseCalender';
import { Horoscope } from './Horoscope';
import { ReportModule } from './ReportModule';
import { ErrorBoundary } from './ErrorBoundary';
import { ConfigPanel, DashboardConfig } from './ConfigPanel';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import {
  StockData, MetalData, USIndexData, CommodityData,
  HotSearchData, GitHubData,
  Report, HoroscopeData, CalendarData, CryptoData
} from '../types';

import { CryptoModule } from './CryptoModule';

const ResponsiveGridLayout = WidthProvider(Responsive);

// 默认布局
const defaultLayouts = {
  lg: [
    { i: 'stock',    x: 0,  y: 0,  w: 4, h: 4, minW: 2, minH: 3 },
    { i: 'us_stock', x: 4,  y: 0,  w: 4, h: 4, minW: 2, minH: 3 },
    { i: 'metals',   x: 8,  y: 0,  w: 2, h: 4, minW: 2, minH: 3 },
    { i: 'commodity',x: 10, y: 0,  w: 2, h: 4, minW: 2, minH: 3 },
    { i: 'hot',      x: 0,  y: 4,  w: 4, h: 4, minW: 2, minH: 3 },
    { i: 'news',     x: 4,  y: 4,  w: 4, h: 4, minW: 2, minH: 3 },
    { i: 'github',   x: 8,  y: 4,  w: 4, h: 4, minW: 2, minH: 3 },
    { i: 'calendar', x: 0,  y: 8,  w: 4, h: 4, minW: 2, minH: 3 },
    { i: 'horoscope',x: 4,  y: 8,  w: 4, h: 4, minW: 2, minH: 3 },
    { i: 'report',   x: 8,  y: 8,  w: 4, h: 4, minW: 3, minH: 3 },
    { i: 'crypto',   x: 0,  y: 12, w: 3, h: 4, minW: 2, minH: 3 },
  ],
  md: [
    { i: 'stock',    x: 0, y: 0,  w: 5, h: 4 },
    { i: 'us_stock', x: 5, y: 0,  w: 5, h: 4 },
    { i: 'metals',   x: 0, y: 4,  w: 3, h: 4 },
    { i: 'commodity',x: 3, y: 4,  w: 3, h: 4 },
    { i: 'hot',      x: 6, y: 4,  w: 4, h: 4 },
    { i: 'news',     x: 0, y: 8,  w: 5, h: 4 },
    { i: 'github',   x: 5, y: 8,  w: 5, h: 4 },
    { i: 'calendar', x: 0, y: 12, w: 5, h: 4 },
    { i: 'horoscope',x: 5, y: 12, w: 5, h: 4 },
    { i: 'report',   x: 0, y: 16, w: 10, h: 4 },
    { i: 'crypto',   x: 0, y: 20, w: 5, h: 4 },
  ],
  sm: [
    { i: 'stock',    x: 0, y: 0,  w: 6, h: 4 },
    { i: 'us_stock', x: 0, y: 4,  w: 6, h: 4 },
    { i: 'metals',   x: 0, y: 8,  w: 3, h: 4 },
    { i: 'commodity',x: 3, y: 8,  w: 3, h: 4 },
    { i: 'hot',      x: 0, y: 12, w: 6, h: 4 },
    { i: 'news',     x: 0, y: 16, w: 6, h: 4 },
    { i: 'github',   x: 0, y: 20, w: 6, h: 4 },
    { i: 'calendar', x: 0, y: 24, w: 6, h: 4 },
    { i: 'horoscope',x: 0, y: 28, w: 6, h: 4 },
    { i: 'report',   x: 0, y: 32, w: 6, h: 4 },
    { i: 'crypto',   x: 0, y: 36, w: 6, h: 4 },
  ],
};

interface DashboardProps {
  apiBase?: string;
}

export const Dashboard: React.FC<DashboardProps> = ({ apiBase = 'http://localhost:8080' }) => {
  const [stocks, setStocks] = useState<StockData[]>([]);
  const [usStocks, setUsStocks] = useState<Record<string, USIndexData>>({});
  const [metals, setMetals] = useState<Record<string, MetalData>>({});
  const [commodities, setCommodities] = useState<Record<string, CommodityData>>({});
  const [hotSearch, setHotSearch] = useState<HotSearchData>({});
  const [github, setGithub] = useState<GitHubData | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [horoscope, setHoroscope] = useState<HoroscopeData | null>(null);
  const [calendar, setCalendar] = useState<CalendarData | null>(null);
  const [crypto, setCrypto] = useState<CryptoData | null>(null);

  const [layouts, setLayouts] = useState(defaultLayouts);
  const [showConfig, setShowConfig] = useState(false);
  const [config, setConfig] = useState<DashboardConfig>({
    refreshInterval: 1800,
    feishuWebhook: '',
    wecomWebhook: '',
    visibleModules: ['stock', 'us_stock', 'metals', 'commodity', 'hot', 'news', 'github', 'calendar', 'horoscope', 'report', 'crypto'],
  });

  const fetchData = useCallback(async () => {
    try {
      const [
        stockRes, usStockRes, metalRes, commodityRes,
        hotRes, githubRes, reportRes,
        horoscopeRes, calendarRes, cryptoRes
      ] = await Promise.all([
        fetch(`${apiBase}/api/stock`).then(r => r.json()).catch(() => ({})),
        fetch(`${apiBase}/api/us-stock`).then(r => r.json()).catch(() => ({})),
        fetch(`${apiBase}/api/metals`).then(r => r.json()).catch(() => ({})),
        fetch(`${apiBase}/api/commodity`).then(r => r.json()).catch(() => ({})),
        fetch(`${apiBase}/api/hot`).then(r => r.json()).catch(() => ({})),
        fetch(`${apiBase}/api/github?since=weekly`).then(r => r.json()).catch(() => null),
        fetch(`${apiBase}/api/report?type=morning`).then(r => r.json()).catch(() => null),
        fetch(`${apiBase}/api/life/horoscope`).then(r => r.json()).catch(() => null),
        fetch(`${apiBase}/api/life/calendar`).then(r => r.json()).catch(() => null),
        fetch(`${apiBase}/api/crypto`).then(r => r.json()).catch(() => null),
      ]);

      if (stockRes && typeof stockRes === 'object') setStocks(Object.values(stockRes) as StockData[]);
      if (usStockRes && typeof usStockRes === 'object') setUsStocks(usStockRes);
      if (metalRes && typeof metalRes === 'object') setMetals(metalRes);
      if (commodityRes && typeof commodityRes === 'object') setCommodities(commodityRes);
      if (hotRes && typeof hotRes === 'object') setHotSearch(hotRes);
      if (githubRes && typeof githubRes === 'object') setGithub(githubRes);
      if (reportRes && typeof reportRes === 'object') setReport(reportRes);
      if (horoscopeRes && typeof horoscopeRes === 'object') setHoroscope(horoscopeRes);
      if (calendarRes && typeof calendarRes === 'object') setCalendar(calendarRes);
      if (cryptoRes && typeof cryptoRes === 'object') setCrypto(cryptoRes);
    } catch (e) {
      console.error('数据获取失败:', e);
    }
  }, [apiBase]);

  const refreshIntervalSec = config.refreshInterval;
  const { lastRefresh, isRefreshing, refresh } = useAutoRefresh({
    interval: config.refreshInterval * 1000,
    onRefresh: fetchData,
  });

  const [countdown, setCountdown] = useState(refreshIntervalSec);
  const resetCountdown = useCallback(() => setCountdown(refreshIntervalSec), [refreshIntervalSec]);

  useEffect(() => { resetCountdown(); }, [lastRefresh, resetCountdown]);
  useEffect(() => {
    const t = setInterval(() => setCountdown(p => Math.max(0, p - 1)), 1000);
    return () => clearInterval(t);
  }, []);

  const [isTopBarRefreshing, setIsTopBarRefreshing] = useState(false);
  const handleManualRefresh = useCallback(async () => {
    if (isTopBarRefreshing) return;
    setIsTopBarRefreshing(true);
    try { await fetchData(); resetCountdown(); } finally { setIsTopBarRefreshing(false); }
  }, [fetchData, isTopBarRefreshing, resetCountdown]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleLayoutChange = (layout: Layout[], allLayouts: any) => setLayouts(allLayouts);

  const renderModules = () => {
    const mods: React.ReactNode[] = [];

    if (config.visibleModules.includes('stock')) mods.push(
      <div key="stock"><ModuleContainer title="A股行情" icon="📊" subtitle="实时行情" onRefresh={refresh} isRefreshing={isRefreshing} lastUpdate={lastRefresh.toLocaleTimeString()}><StockChart data={stocks} /></ModuleContainer></div>
    );
    if (config.visibleModules.includes('us_stock')) mods.push(
      <div key="us_stock"><ModuleContainer title="美股行情" icon="🗽" subtitle="纳斯达克 · 标普 · 道琼斯" onRefresh={refresh} isRefreshing={isRefreshing} lastUpdate={lastRefresh.toLocaleTimeString()}><USStockModule data={usStocks} /></ModuleContainer></div>
    );
    if (config.visibleModules.includes('metals')) mods.push(
      <div key="metals"><ModuleContainer title="贵金属" icon="🥇" subtitle="黄金 · 白银 · 铂金" onRefresh={refresh} isRefreshing={isRefreshing} lastUpdate={lastRefresh.toLocaleTimeString()}>{Object.keys(metals).length > 0 ? <div className="space-y-3">{Object.entries(metals).map(([code, d]) => { const up = d.pct >= 0; return (<div key={code} className="flex justify-between items-center py-2 border-b border-[var(--border-subtle)] last:border-0"><span className="text-sm text-[var(--text-primary)] font-medium">{d.name}</span><div className="text-right"><span className="text-sm font-bold text-[var(--text-primary)]">${d.price?.toFixed(2)}</span><span className={`ml-2 text-sm font-semibold ${up ? 'price-up' : 'price-down'}`}>{up ? '↑' : '↓'} {Math.abs(d.pct)?.toFixed(2)}%</span></div></div>); })}</div> : <p className="text-[var(--text-muted)]">暂无数据</p>}</ModuleContainer></div>
    );
    if (config.visibleModules.includes('commodity')) mods.push(
      <div key="commodity"><ModuleContainer title="大宗商品" icon="🛢️" subtitle="原油 · 天然气 · 农产品" onRefresh={refresh} isRefreshing={isRefreshing} lastUpdate={lastRefresh.toLocaleTimeString()}><CommodityModule data={commodities} /></ModuleContainer></div>
    );
    if (config.visibleModules.includes('hot')) mods.push(
      <div key="hot"><ModuleContainer title="微博热搜" icon="🔥" subtitle="实时热点" onRefresh={refresh} isRefreshing={isRefreshing} lastUpdate={lastRefresh.toLocaleTimeString()}><HotSearchList data={hotSearch} /></ModuleContainer></div>
    );
    if (config.visibleModules.includes('news')) mods.push(
      <div key="news"><ModuleContainer title="AI 资讯" icon="🤖" subtitle="AI HOT · 精选资讯流" onRefresh={refresh} isRefreshing={isRefreshing} lastUpdate={lastRefresh.toLocaleTimeString()}><AIHotModule apiBase={apiBase} onRefresh={refresh} isRefreshing={isRefreshing} /></ModuleContainer></div>
    );
    if (config.visibleModules.includes('github')) mods.push(
      <div key="github"><ModuleContainer title="GitHub 热门" icon="⚙️" subtitle="开源项目趋势" onRefresh={refresh} isRefreshing={isRefreshing} lastUpdate={lastRefresh.toLocaleTimeString()}><GitHubModule data={github || { projects: [], total: 0 } as GitHubData} apiBase={apiBase} /></ModuleContainer></div>
    );
    if (config.visibleModules.includes('calendar')) mods.push(
      <div key="calendar"><ModuleContainer title="今日黄历" icon="📅" subtitle="宜忌吉凶" defaultCollapsed={false}><ChineseCalender data={calendar as CalendarData} /></ModuleContainer></div>
    );
    if (config.visibleModules.includes('horoscope')) mods.push(
      <div key="horoscope"><ModuleContainer title="星座运势" icon="⭐" subtitle="每日星语" defaultCollapsed={false}><Horoscope apiBase={apiBase} /></ModuleContainer></div>
    );
    if (config.visibleModules.includes('report')) mods.push(
      <div key="report"><ModuleContainer title="小居早报" icon="📰" subtitle="每日精选摘要" onRefresh={refresh} isRefreshing={isRefreshing} lastUpdate={report?.date}><ReportModule report={report as Report} onRefresh={refresh} isRefreshing={isRefreshing} /></ModuleContainer></div>
    );
    if (config.visibleModules.includes('crypto')) mods.push(
      <div key="crypto"><ModuleContainer title="虚拟货币" icon="₿" subtitle="加密货币行情" onRefresh={refresh} isRefreshing={isRefreshing} lastUpdate={lastRefresh.toLocaleTimeString()}><CryptoModule data={crypto} /></ModuleContainer></div>
    );

    return mods;
  };

  // 格式化时间
  const fmtTime = (s: number) => {
    const m = Math.floor(s / 60), sec = s % 60;
    return m > 0 ? `${m}分${sec}秒` : `${sec}秒`;
  };

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-base)' }}>

      {/* ===== 顶部导航栏 ===== */}
      <div className="top-bar sticky top-0 z-50 px-6 py-3.5">
        <div className="flex items-center justify-between">
          {/* 左：品牌 */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl flex items-center justify-center text-lg"
                 style={{ background: 'linear-gradient(135deg, #5b8af0 0%, #8b7cf8 100%)', boxShadow: '0 2px 8px rgba(91,138,240,0.3)' }}>
              🏠
            </div>
            <div>
              <h1 className="text-base font-bold text-[var(--text-primary)] leading-none">小居数据监控台</h1>
              <p className="text-[10px] text-[var(--text-muted)] mt-0.5 tracking-wide">XIAOJU CONTROL CENTER</p>
            </div>
          </div>

          {/* 右：控制 */}
          <div className="flex items-center gap-3">
            {/* 状态标签 */}
            <div className="hidden sm:flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-green)] animate-pulse" />
              <span className="text-xs text-[var(--text-muted)]">实时监控中</span>
            </div>

            {/* 刷新倒计时 */}
            <div className="countdown-badge">
              <svg className="w-3 h-3 text-[var(--text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{isRefreshing ? '刷新中...' : `${fmtTime(countdown)}后刷新`}</span>
            </div>

            {/* 手动刷新 */}
            <button
              onClick={handleManualRefresh}
              disabled={isTopBarRefreshing}
              className="btn-icon"
              title="立即刷新"
            >
              <svg className={`w-4 h-4 ${isTopBarRefreshing ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>

            {/* 配置 */}
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="btn-icon"
              title="设置"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* ===== 配置面板 ===== */}
      {showConfig && (
        <div className="mx-6 mt-4">
          <ConfigPanel config={config} onConfigChange={setConfig} onClose={() => setShowConfig(false)} />
        </div>
      )}

      {/* ===== 模块网格 ===== */}
      <div className="px-4 pb-6">
        <ErrorBoundary>
          <ResponsiveGridLayout
            className="mt-4"
            layouts={layouts}
            breakpoints={{ lg: 1200, md: 996, sm: 768 }}
            cols={{ lg: 12, md: 10, sm: 6 }}
            rowHeight={90}
            onLayoutChange={handleLayoutChange}
            draggableHandle=".module-card-header"
            margin={[16, 16]}
            containerPadding={[0, 0]}
          >
            {renderModules()}
          </ResponsiveGridLayout>
        </ErrorBoundary>
      </div>
    </div>
  );
};