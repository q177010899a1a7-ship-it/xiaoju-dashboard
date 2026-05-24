import React, { useState } from 'react';

interface ModuleContainerProps {
  title: string;
  icon?: string;
  children: React.ReactNode;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  lastUpdate?: string;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  subtitle?: string;
}

export const ModuleContainer: React.FC<ModuleContainerProps> = ({
  title,
  icon = '📊',
  children,
  onRefresh,
  isRefreshing,
  lastUpdate,
  collapsible = true,
  defaultCollapsed = false,
  subtitle,
}) => {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);

  return (
    <div className="module-card h-full flex flex-col">
      {/* Header */}
      <div className="module-card-header">
        <div className="flex items-center gap-2.5">
          <span className="text-lg leading-none">{icon}</span>
          <div>
            <h3 className="text-sm font-semibold text-[var(--text-primary)] leading-tight">{title}</h3>
            {subtitle && <p className="text-xs text-[var(--text-muted)] mt-0.5">{subtitle}</p>}
          </div>
          {isRefreshing && (
            <span className="text-[10px] text-[var(--accent-blue)] font-medium animate-pulse">刷新中</span>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          {lastUpdate && (
            <span className="countdown-badge">{lastUpdate}</span>
          )}
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              className="btn-icon w-7 h-7"
              title="刷新"
            >
              <svg
                className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          )}
          {collapsible && (
            <button
              onClick={() => setCollapsed(!collapsed)}
              className="btn-icon w-7 h-7"
              title={collapsed ? '展开' : '收起'}
            >
              <svg
                className={`w-3.5 h-3.5 transition-transform duration-200 ${collapsed ? '' : 'rotate-180'}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      {!collapsed && (
        <div className="module-card-body flex-1 overflow-auto">
          {children}
        </div>
      )}
    </div>
  );
};