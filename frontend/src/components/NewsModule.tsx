import React from 'react';
import { NewsData, NewsItem } from '../types';

interface NewsModuleProps {
  data: NewsData;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export const NewsModule: React.FC<NewsModuleProps> = ({
  data,
  onRefresh,
  isRefreshing,
}) => {
  if (!data || !data.news || data.news.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        <p>暂无数据</p>
      </div>
    );
  }

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  const getSourceColor = (source: string) => {
    switch (source) {
      case '36氪': return 'bg-orange-100 text-orange-700';
      case '钛媒体': return 'bg-blue-100 text-blue-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="space-y-3">
      {/* 来源标签 */}
      {data.sources && data.sources.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {data.sources.map((source, idx) => (
            <span key={idx} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
              {source}
            </span>
          ))}
        </div>
      )}

      {/* 新闻列表 */}
      <div className="space-y-2 max-h-[300px] overflow-y-auto">
        {data.news.slice(0, 15).map((item, idx) => (
          <div key={idx} className="border border-gray-100 rounded-lg p-3 hover:bg-gray-50 transition-colors">
            <a 
              href={item.link} 
              target="_blank" 
              rel="noopener noreferrer"
              className="block"
            >
              <h4 className="text-sm font-medium text-gray-800 line-clamp-2 hover:text-blue-600">
                {item.title}
              </h4>
              <div className="flex items-center gap-2 mt-1">
                <span className={`text-xs px-1.5 py-0.5 rounded ${getSourceColor(item.source)}`}>
                  {item.source}
                </span>
                <span className="text-xs text-gray-400">
                  {formatDate(item.published)}
                </span>
              </div>
              {item.description && (
                <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                  {item.description}
                </p>
              )}
            </a>
          </div>
        ))}
      </div>

      {/* 刷新按钮 */}
      {onRefresh && (
        <div className="flex justify-center pt-2 border-t">
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="text-xs text-blue-500 hover:text-blue-600 disabled:opacity-50"
          >
            {isRefreshing ? '刷新中...' : '🔄 刷新'}
          </button>
        </div>
      )}
    </div>
  );
};
