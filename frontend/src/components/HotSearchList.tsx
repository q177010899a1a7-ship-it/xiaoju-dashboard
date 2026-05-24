import React from 'react';
import { HotSearchData, HotItem } from '../types';

interface HotSearchListProps {
  data: HotSearchData;
}

export const HotSearchList: React.FC<HotSearchListProps> = ({ data }) => {
  const renderList = (items: HotItem[], source: string) => {
    if (!items || items.length === 0) {
      return <p className="text-gray-400 text-sm">暂无数据</p>;
    }

    return (
      <div className="space-y-1">
        {items.slice(0, 10).map((item, idx) => (
          <div 
            key={idx} 
            className="flex items-center gap-3 py-2 px-2 rounded hover:bg-gray-50 transition-colors cursor-pointer"
          >
            <span className={`
              w-6 h-6 flex items-center justify-center rounded text-xs font-bold shrink-0
              ${idx < 3 ? 'bg-red-500 text-white' : 'bg-gray-200 text-gray-600'}
            `}>
              {idx + 1}
            </span>
            <span className="flex-1 text-gray-800 text-sm truncate">{item.title}</span>
            {item.label_name && (
              <span className="text-xs px-2 py-0.5 bg-orange-100 text-orange-600 rounded shrink-0">
                {item.label_name}
              </span>
            )}
            {item.hot_value && source === 'douyin' && (
              <span className="text-xs text-gray-400 shrink-0">
                {item.hot_value}
              </span>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {data.weibo && data.weibo.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-500 mb-2 flex items-center gap-2">
            <span>🔴</span> 微博热搜
          </h4>
          {renderList(data.weibo, 'weibo')}
        </div>
      )}
      
      {data.douyin && data.douyin.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-500 mb-2 flex items-center gap-2">
            <span>🎵</span> 抖音热搜
          </h4>
          {renderList(data.douyin, 'douyin')}
        </div>
      )}
      
      {data.twitter && data.twitter.length > 0 && !data.twitter[0]?.note && (
        <div>
          <h4 className="text-sm font-medium text-gray-500 mb-2 flex items-center gap-2">
            <span>🐦</span> Twitter/X热搜
          </h4>
          {renderList(data.twitter, 'twitter')}
        </div>
      )}
      
      {data.twitter && data.twitter[0]?.note && (
        <div className="bg-yellow-50 rounded-lg p-3">
          <p className="text-xs text-yellow-600">{data.twitter[0].note}</p>
        </div>
      )}
      
      {!data.weibo && !data.douyin && !data.twitter && (
        <p className="text-gray-400 text-sm text-center py-4">暂无热搜数据</p>
      )}
    </div>
  );
};
