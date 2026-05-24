import React from 'react';
import { CryptoData, CryptoItem } from '../types';

interface CryptoModuleProps {
  data: CryptoData | null;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

const CRYPTO_ICONS: Record<string, string> = {
  BTC: '₿',
  ETH: 'Ξ',
  SOL: '◎',
  BNB: '🔶',
  XRP: '✕',
  ADA: '₳',
  DOGE: 'Ð',
  DOT: '●',
  AVAX: '▲',
  LINK: '🔗',
  ETHW: '⋆',
  SUI: '◎',
  APT: '●',
  ARB: '▲',
  OP: '◎',
};

const CRYPTO_COLOR: Record<string, string> = {
  BTC: 'text-orange-500',
  ETH: 'text-purple-500',
  SOL: 'text-gradient-start',
  BNB: 'text-yellow-500',
  XRP: 'text-gray-500',
  ADA: 'text-blue-400',
  DOGE: 'text-yellow-400',
  DOT: 'text-pink-500',
  AVAX: 'text-red-500',
  LINK: 'text-blue-500',
};

export const CryptoModule: React.FC<CryptoModuleProps> = ({
  data,
  onRefresh,
  isRefreshing,
}) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        <p>暂无数据</p>
      </div>
    );
  }

  const formatPrice = (price: number) => {
    if (price >= 1000) return price.toLocaleString('en-US', { maximumFractionDigits: 0 });
    if (price >= 1) return price.toFixed(2);
    if (price >= 0.01) return price.toFixed(4);
    return price.toFixed(6);
  };

  const formatVolume = (vol: number) => {
    if (vol >= 1e9) return (vol / 1e9).toFixed(1) + 'B';
    if (vol >= 1e6) return (vol / 1e6).toFixed(1) + 'M';
    if (vol >= 1e3) return (vol / 1e3).toFixed(1) + 'K';
    return vol.toFixed(0);
  };

  // 按24h涨跌排序
  const sorted = Object.values(data).sort((a, b) => b.change_24h - a.change_24h);

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-2 gap-1 text-[11px] font-medium text-gray-500 px-1 border-b border-gray-100 pb-1">
        <span>币种</span>
        <span className="text-right">价格 / 24h涨跌</span>
      </div>
      <div className="space-y-1 max-h-[280px] overflow-y-auto">
        {sorted.map((item: CryptoItem) => {
          const isUp = item.change_24h >= 0;
          const colorClass = isUp ? 'text-red-500' : 'text-green-500';
          const arrow = isUp ? '▲' : '▼';
          const icon = CRYPTO_ICONS[item.symbol] || '●';

          return (
            <div
              key={item.symbol}
              className="flex items-center justify-between px-2 py-1.5 rounded hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-1.5">
                <span className="text-sm">{icon}</span>
                <div>
                  <span className="font-medium text-gray-700 text-xs">{item.symbol}</span>
                  <span className="text-[10px] text-gray-400 ml-1">
                    {formatVolume(item.volume_24h)}Vol
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs font-medium text-gray-800">
                  ${formatPrice(item.price)}
                </div>
                <div className={`text-[10px] ${colorClass}`}>
                  {arrow} {Math.abs(item.change_24h).toFixed(2)}%
                </div>
              </div>
            </div>
          );
        })}
      </div>

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
