import React from 'react';
import { USIndexData } from '../types';

interface USStockModuleProps {
  data: Record<string, USIndexData>;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  lastUpdate?: string;
}

export const USStockModule: React.FC<USStockModuleProps> = ({
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

  // 分离指数和股票
  const indices = Object.values(data).filter(d => d.type === 'index');
  const stocks = Object.values(data).filter(d => d.type === 'stock');

  const formatPrice = (price: number) => {
    if (price == null || isNaN(price)) return '--';
    if (price >= 10000) return (price / 1000).toFixed(2) + 'K';
    return price.toFixed(2);
  };

  const formatVolume = (vol: number) => {
    if (vol >= 1e9) return (vol / 1e9).toFixed(2) + 'B';
    if (vol >= 1e6) return (vol / 1e6).toFixed(2) + 'M';
    if (vol >= 1e3) return (vol / 1e3).toFixed(2) + 'K';
    return vol.toString();
  };

  return (
    <div className="space-y-4">
      {/* 三大指数 */}
      <div>
        <h4 className="text-sm font-medium text-gray-500 mb-2">📈 美股指数</h4>
        <div className="grid grid-cols-3 gap-2">
          {indices.map(item => {
            const isUp = item.pct >= 0;
            return (
              <div key={item.symbol} className="bg-gray-50 rounded-lg p-2 text-center">
                <p className="text-xs text-gray-500 truncate">{item.name}</p>
                <p className="text-sm font-bold">{formatPrice(item.price)}</p>
                <p className={`text-xs ${isUp ? 'text-red-500' : 'text-green-500'}`}>
                  {isUp ? '↑' : '↓'} {Math.abs(item.pct).toFixed(2)}%
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* 热门股票 */}
      <div>
        <h4 className="text-sm font-medium text-gray-500 mb-2">🏢 热门股票</h4>
        <div className="space-y-1 max-h-[200px] overflow-y-auto">
          {stocks.slice(0, 10).map(item => {
            const isUp = item.pct >= 0;
            return (
              <div key={item.symbol} className="flex justify-between items-center py-1.5 px-2 rounded hover:bg-gray-50">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{item.name}</p>
                  <p className="text-xs text-gray-400">{item.symbol}</p>
                </div>
                <div className="text-right ml-2">
                  <p className="text-sm font-medium">${item.price?.toFixed(2) ?? '--'}</p>
                  <p className={`text-xs ${isUp ? 'text-red-500' : 'text-green-500'}`}>
                    {isUp ? '↑' : '↓'} {Math.abs(item.pct).toFixed(2)}%
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 刷新信息 */}
      {lastUpdate && (
        <p className="text-xs text-gray-400 text-center pt-2 border-t">更新时间: {lastUpdate}</p>
      )}
    </div>
  );
};
