import React from 'react';
import { Report } from '../types';

interface ReportModuleProps {
  report: Report;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export const ReportModule: React.FC<ReportModuleProps> = ({
  report,
  onRefresh,
  isRefreshing,
}) => {
  if (!report) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        <p>暂无报告</p>
      </div>
    );
  }

  // 后端返回的是 content 字符串，前端需要解析显示
  const hasContent = !!(report as any).content;
  const hasSections = !!(report as Report).sections && (report as Report).sections.length > 0;

  return (
    <div className="space-y-4">
      {/* 报告头部 */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">{report.title || '小居早报'}</h3>
          <p className="text-xs text-gray-400">{report.date || ''}</p>
        </div>
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
            title="刷新报告"
          >
            <svg
              className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        )}
      </div>

      {/* 报告内容 - 支持 content 字符串格式 */}
      <div className="space-y-3">
        {hasContent ? (
          // content 字符串格式（当前后端返回格式）
          <div className="text-sm text-gray-600 whitespace-pre-line overflow-y-auto max-h-[500px]">
            {(report as any).content}
          </div>
        ) : hasSections ? (
          // sections 数组格式（备用）
          (report as Report).sections?.map((section, idx) => (
            <div key={idx} className="border border-gray-200 rounded-lg p-3">
              <h4 className="font-medium text-gray-700 mb-2 text-sm">{section.title}</h4>
              <div className="text-sm text-gray-600 whitespace-pre-line">
                {section.content}
              </div>
            </div>
          ))
        ) : (
          <div className="text-gray-400 text-sm">报告内容加载中...</div>
        )}
      </div>

      {/* 摘要 */}
      {report.summary && (
        <p className="text-xs text-gray-400 text-center pt-2 border-t border-gray-200">
          {report.summary}
        </p>
      )}
    </div>
  );
};
