import React from 'react';
import { StockData } from '../types';

interface StockChartProps {
  data: StockData[];
  title?: string;
}

export const StockChart: React.FC<StockChartProps> = ({ data, title }) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        暂无数据
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {title && <h4 className="text-sm font-medium text-gray-600 mb-2">{title}</h4>}
      
      {/* 数据表格 */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-500 border-b border-gray-200">
              <th className="text-left py-1 font-medium">名称</th>
              <th className="text-right py-1 font-medium">价格</th>
              <th className="text-right py-1 font-medium">涨跌</th>
              <th className="text-right py-1 font-medium">涨跌幅</th>
              <th className="text-right py-1 font-medium">成交额(万)</th>
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 6).map((item, idx) => {
              const isUp = (item.pct ?? 0) >= 0;
              const colorClass = isUp ? 'text-red-500' : 'text-green-500';
              const arrow = isUp ? '↑' : '↓';
              
              // 格式化成交额（万元 -> 亿）
              const formatAmount = (amount: number) => {
                if (!amount) return '--';
                if (amount >= 10000) return (amount / 10000).toFixed(2) + '亿';
                return amount.toFixed(0) + '万';
              };
              
              return (
                <tr key={idx} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                  <td className="py-1.5 text-gray-700 font-medium">{item.name}</td>
                  <td className="py-1.5 text-right font-medium text-gray-800">
                    {item.price != null ? item.price.toFixed(2) : '--'}
                  </td>
                  <td className={`py-1.5 text-right ${colorClass}`}>
                    {arrow} {Math.abs(item.change ?? 0).toFixed(2)}
                  </td>
                  <td className={`py-1.5 text-right ${colorClass}`}>
                    {arrow} {Math.abs(item.pct ?? 0).toFixed(2)}%
                  </td>
                  <td className="py-1.5 text-right text-gray-500">
                    {formatAmount(item.amount ?? 0)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
