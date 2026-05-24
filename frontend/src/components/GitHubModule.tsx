import React, { useState, useEffect, useCallback } from 'react';
import { GitHubData } from '../types';

interface GitHubModuleProps {
  data: GitHubData;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  apiBase?: string;
}

type TimeRange = 'daily' | 'weekly' | 'monthly';

const FAVORITES_KEY = 'github_favorites_v2';

const getFavorites = (): Record<string, boolean> => {
  try {
    const stored = localStorage.getItem(FAVORITES_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch {
    return {};
  }
};

const saveFavorite = (key: string, value: boolean) => {
  const favorites = getFavorites();
  favorites[key] = value;
  localStorage.setItem(FAVORITES_KEY, JSON.stringify(favorites));
};

const getLanguageColor = (lang: string) => {
  const colors: Record<string, string> = {
    'Python': '#3572A5',
    'JavaScript': '#f1e05a',
    'TypeScript': '#2b7489',
    'Java': '#b07219',
    'Go': '#00ADD8',
    'Rust': '#dea584',
    'C++': '#f34b7d',
    'C': '#555555',
    'Ruby': '#701516',
    'PHP': '#4F5D95',
    'Swift': '#F05138',
    'Kotlin': '#A97BFF',
    'Vue': '#41b883',
    'C#': '#178600',
  };
  return colors[lang] || '#8b8b8b';
};

export const GitHubModule: React.FC<GitHubModuleProps> = ({
  data: initialData,
  onRefresh,
  isRefreshing,
  apiBase = 'http://localhost:8080',
}) => {
  const [timeRange, setTimeRange] = useState<TimeRange>('weekly');
  const [data, setData] = useState<GitHubData>(initialData || { projects: [], total: 0 });
  const [favorites, setFavorites] = useState<Record<string, boolean>>({});
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setFavorites(getFavorites());
  }, []);

  // 用props数据初始化（仅首次）
  useEffect(() => {
    if (initialData && initialData.projects && initialData.projects.length > 0 && data.projects.length === 0) {
      setData(initialData);
    }
  }, []); // 只在挂载时执行一次

  const fetchData = useCallback(async (since: TimeRange) => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/github?since=${since}&_t=${Date.now()}`, {
        headers: { 'Cache-Control': 'no-cache' }
      });
      const json = await res.json();
      setData(json);
    } catch (e) {
      console.error('Failed to fetch GitHub data:', e);
    } finally {
      setLoading(false);
    }
  }, [apiBase]);

  const handleTimeRangeChange = (range: TimeRange) => {
    setTimeRange(range);
    setShowFavoritesOnly(false);
    setShowReport(false);
    fetchData(range);
  };

  const toggleFavorite = (e: React.MouseEvent, projectKey: string) => {
    e.preventDefault();
    e.stopPropagation();
    const newFavorites = { ...favorites };
    newFavorites[projectKey] = !newFavorites[projectKey];
    setFavorites(newFavorites);
    saveFavorite(projectKey, newFavorites[projectKey]);
  };

  const loadReport = async () => {
    setLoading(true);
    setShowReport(true);
    try {
      const res = await fetch(`${apiBase}/api/github/report?_t=${Date.now()}`, {
        headers: { 'Cache-Control': 'no-cache' }
      });
      const json = await res.json();
      setReport(json);
    } catch (e) {
      console.error('Failed to fetch report:', e);
    } finally {
      setLoading(false);
    }
  };

  const formatStars = (stars: number) => {
    if (stars >= 1000) return (stars / 1000).toFixed(1) + 'K';
    return stars.toString();
  };

  // 收藏过滤
  const filteredProjects = showFavoritesOnly
    ? data.projects.filter(p => favorites[`${p.owner}/${p.name}`])
    : data.projects;

  // 渲染项目列表
  const renderProjectList = () => {
    if (!filteredProjects || filteredProjects.length === 0) {
      return (
        <div className="text-center text-gray-400 py-8">
          {showFavoritesOnly ? '暂无收藏' : '暂无数据'}
        </div>
      );
    }

    return filteredProjects.map((project, idx) => {
      const projectKey = `${project.owner}/${project.name}`;
      const isFav = favorites[projectKey] || false;

      return (
        <div
          key={idx}
          className="border border-gray-100 rounded-lg p-3 hover:bg-gray-50 hover:border-blue-200 transition-colors"
        >
          <div className="flex items-start gap-3">
            <span className={`
              w-6 h-6 flex items-center justify-center rounded text-xs font-bold shrink-0
              ${idx < 3 ? 'bg-yellow-400 text-white' : 'bg-gray-200 text-gray-600'}
            `}>
              {idx + 1}
            </span>

            <div className="flex-1 min-w-0">
              {/* 项目名 + 收藏图标 */}
              <div className="flex items-center justify-between gap-2">
                <a
                  href={project.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-medium text-blue-600 hover:text-blue-800 truncate"
                >
                  {project.name}
                </a>
                <button
                  onClick={(e) => toggleFavorite(e, projectKey)}
                  className={`shrink-0 text-lg transition-transform hover:scale-125 ${
                    isFav ? 'text-red-500' : 'text-gray-300'
                  }`}
                  title={isFav ? '取消收藏' : '收藏'}
                >
                  {isFav ? '❤️' : '🤍'}
                </button>
              </div>

              <p className="text-xs text-gray-400 truncate">
                by {project.owner}
              </p>

              {/* 描述（英文 + 中文翻译，自适应行数） */}
              {project.description && (
                <div className="mt-1">
                  <p className="text-xs text-gray-600 break-words whitespace-pre-wrap">
                    {project.description}
                  </p>
                  {project.description_cn && project.description_cn !== project.description && (
                    <p className="text-xs text-gray-400 mt-0.5 break-words whitespace-pre-wrap">
                      （{project.description_cn}）
                    </p>
                  )}
                </div>
              )}

              {/* 统计信息 */}
              <div className="flex items-center gap-3 mt-2">
                <span className="flex items-center gap-1 text-xs text-gray-600">
                  <span>⭐</span>
                  {formatStars(project.stars)}
                </span>

                {project.forks !== undefined && (
                  <span className="flex items-center gap-1 text-xs text-gray-600">
                    <span>🍴</span>
                    {formatStars(project.forks)}
                  </span>
                )}

                {project.language && (
                  <span className="flex items-center gap-1 text-xs text-gray-600">
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: getLanguageColor(project.language) }}
                    />
                    {project.language}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      );
    });
  };

  // 渲染月度报告
  const renderReport = () => {
    if (!report || !report.projects) {
      return <div className="text-center text-gray-400 py-8">暂无报告数据</div>;
    }

    return (
      <div className="space-y-3">
        <div className="text-center pb-2 border-b border-gray-100">
          <h4 className="font-medium text-gray-700">📊 本月热门Top10分析简报</h4>
          <p className="text-xs text-gray-400 mt-1">
            生成时间: {report.generated_at ? new Date(report.generated_at).toLocaleString('zh-CN') : '未知'}
          </p>
        </div>

        {report.projects.map((proj: any) => (
          <div key={proj.rank} className="border border-gray-100 rounded-lg p-3 bg-gray-50">
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex items-center gap-2 min-w-0">
                <span className={`
                  w-5 h-5 flex items-center justify-center rounded text-xs font-bold shrink-0
                  ${proj.rank <= 3 ? 'bg-yellow-400 text-white' : 'bg-blue-400 text-white'}
                `}>
                  {proj.rank}
                </span>
                <a
                  href={proj.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-medium text-blue-600 hover:text-blue-800 truncate"
                >
                  {proj.owner}/{proj.name}
                </a>
              </div>
              <span className="text-xs text-gray-500 shrink-0">
                ⭐ {formatStars(proj.stars)}
              </span>
            </div>
            <p className="text-xs text-gray-600 leading-relaxed whitespace-pre-wrap">{proj.summary}</p>
          </div>
        ))}
      </div>
    );
  };

  if (showReport) {
    return (
      <div className="flex flex-col h-full">
        {/* 头部控制栏 */}
        <div className="flex items-center justify-between pb-2 border-b border-gray-100 shrink-0">
          <button
            onClick={() => setShowReport(false)}
            className="text-xs text-blue-500 hover:text-blue-600"
          >
            ← 返回列表
          </button>
          <button
            onClick={loadReport}
            disabled={loading}
            className="text-xs text-blue-500 hover:text-blue-600 disabled:opacity-50"
          >
            {loading ? '加载中...' : '🔄 刷新报告'}
          </button>
        </div>

        {/* 报告内容 - 可滚动 */}
        <div className="flex-1 overflow-y-auto mt-3">
          {loading ? (
            <div className="text-center text-gray-400 py-8">加载中...</div>
          ) : (
            renderReport()
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* 头部信息 + 控制栏 */}
      <div className="flex items-center justify-between flex-wrap gap-2 mb-2 shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">
            {showFavoritesOnly ? '❤️ 收藏' : '共'} {data.total?.toLocaleString() || 0} 个仓库
          </span>
          <span className="text-xs text-gray-300">|</span>
          <span className="text-xs text-gray-400">
            {timeRange === 'daily' ? '今日' : timeRange === 'weekly' ? '本周' : '本月'}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* 收藏筛选 */}
          <button
            onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}
            className={`text-xs px-2 py-1 rounded transition-colors ${
              showFavoritesOnly
                ? 'bg-red-100 text-red-600'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            title="只看收藏"
          >
            {showFavoritesOnly ? '❤️' : '🤍'}
          </button>

          {/* 时间筛选 */}
          <div className="flex items-center bg-gray-100 rounded-md overflow-hidden">
            {(['daily', 'weekly', 'monthly'] as TimeRange[]).map((range) => (
              <button
                key={range}
                onClick={() => handleTimeRangeChange(range)}
                className={`text-xs px-2 py-1 transition-colors ${
                  timeRange === range
                    ? 'bg-blue-500 text-white'
                    : 'text-gray-600 hover:bg-gray-200'
                }`}
              >
                {range === 'daily' ? '日' : range === 'weekly' ? '周' : '月'}
              </button>
            ))}
          </div>

          {/* 月度报告 */}
          <button
            onClick={loadReport}
            disabled={loading}
            className="text-xs text-blue-500 hover:text-blue-600 disabled:opacity-50"
            title="查看月度分析简报"
          >
            📊
          </button>

          {/* 刷新 */}
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isRefreshing || loading}
              className="text-xs text-blue-500 hover:text-blue-600 disabled:opacity-50"
            >
              {isRefreshing || loading ? '...' : '🔄'}
            </button>
          )}
        </div>
      </div>

      {/* 项目列表 - 可滚动 */}
      <div className="flex-1 overflow-y-auto space-y-2">
        {loading ? (
          <div className="text-center text-gray-400 py-8">加载中...</div>
        ) : (
          renderProjectList()
        )}
      </div>
    </div>
  );
};
