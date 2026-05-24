import React, { useState, useEffect, useCallback } from 'react';

interface AihotItem {
  id: string;
  time: string;
  title: string;
  title_en: string | null;
  url: string;
  source: string;
  summary: string;
  category: string;
  cat_label: string;
  cat_icon: string;
  cat_color: string;
  ai_selected: boolean;
}

interface AihotDay { date: string; items: AihotItem[] }
interface AihotTimelineData { days: AihotDay[]; total: number }

type ViewMode = 'timeline' | 'daily' | 'category';
type CatFilter = 'all' | 'ai-models' | 'ai-products' | 'industry' | 'paper' | 'tip';

const CAT_COLORS: Record<string, string> = {
  blue: 'tag-blue', green: 'tag-green', orange: 'tag-orange',
  purple: 'tag-purple', yellow: 'tag-yellow', gray: 'tag-gray',
};
const CAT_ICONS: Record<string, string> = {
  'ai-models': '🤖', 'ai-products': '🆕', 'industry': '📈', 'paper': '📚', 'tip': '💡',
};

// ——— 时间线视图 ———
const TimelineView: React.FC<{ data: AihotTimelineData; onReload: () => void }> = ({ data, onReload }) => {
  const [open, setOpen] = useState<Set<string>>(new Set());
  const toggle = (d: string) => setOpen(p => { const n = new Set(p); n.has(d) ? n.delete(d) : n.add(d); return n; });
  if (!data.days?.length) return <div className="text-center py-8 text-[var(--text-muted)] text-sm">暂无数据 <button onClick={onReload} className="text-[var(--accent-blue)] ml-1">重试</button></div>;
  return (
    <div className="space-y-3">
      {data.days.map(day => {
        const isOpen = open.has(day.date);
        const preview = day.items.slice(0, 3);
        return (
          <div key={day.date} className="border border-[var(--border-subtle)] rounded-[14px] overflow-hidden bg-white">
            <button onClick={() => toggle(day.date)} className="day-header w-full text-left">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-[var(--text-primary)]">{day.date}</span>
                <span className="tag tag-gray text-[10px]">{day.items.length}条</span>
              </div>
              <div className="flex items-center gap-2">
                {!isOpen && day.items.length > 3 && <span className="text-[10px] text-[var(--accent-blue)]">展开{day.items.length - 3}条</span>}
                <svg className={`w-3.5 h-3.5 text-[var(--text-muted)] transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
              </div>
            </button>
            {isOpen ? day.items.map((it, i) => <ItemRow key={it.id} item={it} idx={i} hasBorder={i > 0} />)
                    : preview.map((it, i) => <ItemRow key={it.id} item={it} idx={i} hasBorder={i < preview.length - 1} />)}
          </div>
        );
      })}
    </div>
  );
};

// ——— 单条新闻 ———
const ItemRow: React.FC<{ item: AihotItem; idx: number; hasBorder?: boolean }> = ({ item, idx, hasBorder }) => (
  <a href={item.url} target="_blank" rel="noopener noreferrer"
     className={`flex items-start gap-2.5 px-4 py-3 hover:bg-[var(--accent-blue-light)] transition-colors group ${hasBorder !== false ? 'border-t border-[var(--border-subtle)]' : ''}`}>
    <span className="text-[11px] text-[var(--text-muted)] mt-0.5 shrink-0 font-medium">{item.time}</span>
    <div className="flex-1 min-w-0">
      <div className="flex items-center gap-1.5 mb-1 flex-wrap">
        <span className="text-xs">{item.cat_icon}</span>
        <span className={`tag text-[10px] ${CAT_COLORS[item.cat_color] || 'tag-gray'}`}>{item.cat_label}</span>
        {item.ai_selected && <span className="tag tag-blue text-[10px]">精选</span>}
      </div>
      <h4 className="text-[13px] text-[var(--text-primary)] leading-snug line-clamp-2 group-hover:text-[var(--accent-blue)] transition-colors">{item.title}</h4>
      {item.summary && <p className="text-[11px] text-[var(--text-muted)] mt-1 line-clamp-2 leading-relaxed">{item.summary}</p>}
      <p className="text-[10px] text-[var(--text-muted)] mt-1 truncate">{item.source}</p>
    </div>
  </a>
);

// ——— 日报视图 ———
const DailyView: React.FC<{ apiBase: string }> = ({ apiBase }) => {
  const [data, setData] = useState<any>(null);
  const [load, setLoad] = useState(true);
  useEffect(() => { fetch(`${apiBase}/api/aihot/daily`).then(r => r.json()).then(d => { setData(d); setLoad(false); }).catch(() => setLoad(false)); }, [apiBase]);
  if (load) return <div className="text-center py-8"><div className="skeleton w-full h-4 mb-2"/><div className="skeleton w-3/4 h-4"/></div>;
  if (!data?.sections?.length) return <div className="text-center py-8 text-[var(--text-muted)] text-sm">暂无数据</div>;
  return (
    <div className="space-y-5">
      <div className="text-center">
        <p className="text-sm font-semibold text-[var(--text-primary)]">{data.date}</p>
        <p className="text-xs text-[var(--text-muted)] mt-0.5">共 {data.total} 条精选</p>
      </div>
      {data.sections.map((sec: any) => (
        <div key={sec.label}>
          <div className="flex items-center gap-1.5 mb-2.5">
            <span className="text-sm">{sec.icon}</span>
            <h4 className="text-[13px] font-semibold text-[var(--text-primary)]">{sec.label}</h4>
            <span className="tag tag-gray text-[10px]">{sec.items.length}条</span>
          </div>
          <div className="space-y-2">
            {sec.items.map((it: any, i: number) => (
              <a key={i} href={it.url} target="_blank" rel="noopener noreferrer"
                 className="block border border-[var(--border-subtle)] rounded-xl p-3 hover:border-[rgba(91,138,240,0.35)] hover:bg-[var(--accent-blue-light)] transition-all group">
                <h5 className="text-[13px] text-[var(--text-primary)] line-clamp-2 group-hover:text-[var(--accent-blue)] transition-colors leading-snug">{it.title}</h5>
                {it.summary && <p className="text-[11px] text-[var(--text-muted)] mt-1 line-clamp-2 leading-relaxed">{it.summary}</p>}
                <p className="text-[10px] text-[var(--text-muted)] mt-1.5 truncate">{it.source}</p>
              </a>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

// ——— 分类视图 ———
const CategoryView: React.FC<{ apiBase: string; filter: CatFilter }> = ({ apiBase, filter }) => {
  const [data, setData] = useState<any>(null);
  const [load, setLoad] = useState(true);
  useEffect(() => {
    setLoad(true);
    const p = new URLSearchParams({ since_days: '7' });
    if (filter !== 'all') p.set('category', filter);
    fetch(`${apiBase}/api/aihot/categories?${p}`).then(r => r.json()).then(d => { setData(d); setLoad(false); }).catch(() => setLoad(false));
  }, [apiBase, filter]);
  if (load) return <div className="text-center py-8"><div className="skeleton w-full h-4 mb-2"/><div className="skeleton w-3/4 h-4"/></div>;
  if (!data?.items?.length) return <div className="text-center py-8 text-[var(--text-muted)] text-sm">暂无数据</div>;
  return (
    <div className="space-y-2">
      <div className="text-xs text-[var(--text-muted)] mb-3">{data.cat_label || '全部分类'} · {data.total} 条</div>
      {data.items.map((it: AihotItem) => (
        <a key={it.id} href={it.url} target="_blank" rel="noopener noreferrer"
           className="flex items-start gap-2.5 border border-[var(--border-subtle)] rounded-xl p-3 hover:border-[rgba(91,138,240,0.35)] hover:bg-[var(--accent-blue-light)] transition-all group">
          <span className="text-[11px] text-[var(--text-muted)] mt-0.5 shrink-0 font-medium">{it.time}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 mb-1 flex-wrap">
              <span className="text-xs">{CAT_ICONS[it.category] || '📰'}</span>
              <span className={`tag text-[10px] ${CAT_COLORS[it.cat_color] || 'tag-gray'}`}>{it.cat_label}</span>
            </div>
            <h4 className="text-[13px] text-[var(--text-primary)] line-clamp-2 group-hover:text-[var(--accent-blue)] transition-colors leading-snug">{it.title}</h4>
            {it.summary && <p className="text-[11px] text-[var(--text-muted)] mt-1 line-clamp-2 leading-relaxed">{it.summary}</p>}
            <p className="text-[10px] text-[var(--text-muted)] mt-1.5 truncate">{it.source}</p>
          </div>
        </a>
      ))}
    </div>
  );
};

// ——— 主模块 ———
interface Props { apiBase?: string; onRefresh?: () => void; isRefreshing?: boolean }
const CATS: { id: CatFilter; label: string; icon: string }[] = [
  { id: 'all', label: '全部', icon: '📰' }, { id: 'ai-models', label: '模型', icon: '🤖' },
  { id: 'ai-products', label: '产品', icon: '🆕' }, { id: 'industry', label: '行业', icon: '📈' },
  { id: 'paper', label: '论文', icon: '📚' }, { id: 'tip', label: '技巧', icon: '💡' },
];

export const AIHotModule: React.FC<Props> = ({ apiBase = 'http://localhost:8080', onRefresh, isRefreshing }) => {
  const [vm, setVm] = useState<ViewMode>('timeline');
  const [filt, setFilt] = useState<CatFilter>('all');
  const [tl, setTl] = useState<AihotTimelineData | null>(null);

  const loadTl = useCallback(async () => {
    const r = await fetch(`${apiBase}/api/aihot/timeline?since_days=2`);
    const d = await r.json();
    setTl(d);
  }, [apiBase]);

  useEffect(() => { if (vm === 'timeline') loadTl(); }, [vm, loadTl]);

  return (
    <div className="space-y-3">
      {/* Tab栏 */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <button onClick={() => setVm('timeline')} className={`view-tab ${vm === 'timeline' ? 'active' : ''}`}>📋 时间线</button>
        <button onClick={() => setVm('daily')} className={`view-tab ${vm === 'daily' ? 'active' : ''}`}>📅 日报</button>
        <button onClick={() => setVm('category')} className={`view-tab ${vm === 'category' ? 'active' : ''}`}>🏷️ 分类</button>
        <button onClick={onRefresh} disabled={!!isRefreshing} className="ml-auto text-xs text-[var(--accent-blue)] hover:text-[#4a7ae0] disabled:opacity-40 transition-colors">{isRefreshing ? '刷新中' : '🔄 刷新'}</button>
      </div>

      {/* 分类筛选 */}
      {vm === 'category' && (
        <div className="flex gap-1.5 flex-wrap">
          {CATS.map(c => (
            <button key={c.id} onClick={() => setFilt(c.id)}
                    className={`tag text-[11px] cursor-pointer border transition-all ${filt === c.id ? 'tag-blue border-blue-300' : 'tag-outline'}`}>
              {c.icon} {c.label}
            </button>
          ))}
        </div>
      )}

      {/* 内容 */}
      <div className="max-h-[320px] overflow-y-auto pr-0.5">
        {vm === 'timeline' && (tl ? <TimelineView data={tl} onReload={loadTl} /> : <div className="text-center py-8 text-[var(--text-muted)] text-sm">加载中...</div>)}
        {vm === 'daily' && <DailyView apiBase={apiBase} />}
        {vm === 'category' && <CategoryView apiBase={apiBase} filter={filt} />}
      </div>
    </div>
  );
};