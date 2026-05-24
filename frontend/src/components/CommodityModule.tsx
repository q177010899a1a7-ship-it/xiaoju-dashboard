import React from 'react';
import { CommodityData } from '../types';

interface CommodityModuleProps {
  data: Record<string, CommodityData>;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  lastUpdate?: string;
}

export const CommodityModule: React.FC<CommodityModuleProps> = ({
  data,
  onRefresh,
  isRefreshing,
  lastUpdate,
}) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        <p>暂无数据</p>
      </div>
    );
  }

  const commodities = Object.values(data);

  // 按品种分组
  const metals2 = commodities.filter(c =>
    ['CU0', 'AL0', 'ZN0', 'NI0'].includes(c.symbol)
  );
  const preciousMetals = commodities.filter(c =>
    ['AU0', 'AG0'].includes(c.symbol)
  );
  const rubber = commodities.filter(c =>
    ['RU0'].includes(c.symbol)
  );
  const agriculture = commodities.filter(c =>
    ['SR0', 'RM0', 'M0', 'Y0', 'P0', 'L0'].includes(c.symbol)
  );

  const renderCard = (item: CommodityData) => {
    const isUp = (item.pct ?? 0) >= 0;
    const colorClass = isUp ? 'text-red-500' : 'text-green-500';
    const arrow = isUp ? '↑' : '↓';

    // 格式化价格
    const formatPrice = (price: number) => {
      if (price == null || isNaN(price)) return '--';
      if (price >= 10000) return (price / 1000).toFixed(2) + 'K';
      return price.toFixed(2);
    };

    return (
      <div key={item.symbol} className="bg-gray-50 rounded p-2 flex-1 min-w-0">
        <p className="text-xs text-gray-600 truncate">{item.name}</p>
        <p className="text-sm font-bold text-gray-800">{formatPrice(item.price ?? 0)}</p>
        <p className="text-xs text-gray-400">{item.unit}</p>
        <p className={`text-xs ${colorClass}`}>
          {arrow} {Math.abs(item.pct ?? 0).toFixed(2)}%
        </p>
      </div>
    );
  };

  const renderSection = (title: string, items: CommodityData[]) => {
    if (!items || items.length === 0) return null;
    return (
      <div className="mb-3">
        <h4 className="text-xs font-medium text-gray-500 mb-1">{title}</h4>
        <div className="grid grid-cols-2 gap-2">
          {items.map(renderCard)}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-1 overflow-auto max-h-full">
      {renderSection('🛢️ 有色金属', metals2)}
      {renderSection('🥇 贵金属', preciousMetals)}
      {renderSection('🔔 橡胶', rubber)}
      {renderSection('🌾 农产品', agriculture)}

      {/* 刷新信息 */}
      {lastUpdate && (
        <p className="text-xs text-gray-400 text-center pt-2 border-t">更新时间: {lastUpdate}</p>
      )}
    </div>
  );
};
