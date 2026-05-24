import React from 'react';
import { CalendarData } from '../types';

interface ChineseCalenderProps {
  data: CalendarData;
}

export const ChineseCalender: React.FC<ChineseCalenderProps> = ({ data }) => {
  if (!data) {
    return <p className="text-gray-400">暂无数据</p>;
  }

  return (
    <div className="space-y-4">
      {/* 日期信息 */}
      <div className="text-center pb-3 border-b border-gray-200">
        <p className="text-lg font-semibold text-gray-800">{data.date}</p>
        <p className="text-sm text-gray-500">{data.weekday} · {data.lunar}</p>
      </div>

      {/* 宜忌 */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-green-50 rounded-lg p-3">
          <h4 className="text-green-700 font-medium text-sm mb-2">✓ 宜</h4>
          <div className="space-y-1">
            {data.yi?.map((item, idx) => (
              <p key={idx} className="text-xs text-green-600">{item}</p>
            ))}
          </div>
        </div>
        <div className="bg-red-50 rounded-lg p-3">
          <h4 className="text-red-700 font-medium text-sm mb-2">✗ 忌</h4>
          <div className="space-y-1">
            {data.ji?.map((item, idx) => (
              <p key={idx} className="text-xs text-red-600">{item}</p>
            ))}
          </div>
        </div>
      </div>

      {/* 今日提示 */}
      <div className="bg-blue-50 rounded-lg p-3">
        <h4 className="text-blue-700 font-medium text-sm mb-1">今日特吉</h4>
        <p className="text-xs text-blue-600">{data.jiri || '无特别提示'}</p>
      </div>

      {/* 星座 */}
      <div className="text-center">
        <p className="text-sm text-gray-500">今日星座</p>
        <p className="text-lg font-medium text-purple-600">{data.xingzuo || '未知'}</p>
      </div>
    </div>
  );
};
