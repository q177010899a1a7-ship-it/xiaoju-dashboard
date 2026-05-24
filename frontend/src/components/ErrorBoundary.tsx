import React, { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Dashboard Error:', error, errorInfo);
    // 将错误信息记录到 window，方便调试
    (window as any).__DASHBOARD_ERROR__ = { error: error.message, info: errorInfo.componentStack };
  }

  render() {
    if (this.state.hasError) {
      const err = this.state.error;
      return this.props.fallback || (
        <div style={{
          padding: '40px',
          textAlign: 'center',
          color: '#666',
          fontFamily: 'system-ui, sans-serif'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
          <div style={{ fontSize: '18px', marginBottom: '8px' }}>部分模块加载异常</div>
          <div style={{ fontSize: '13px', color: '#999', wordBreak: 'break-all', maxWidth: 400, margin: '0 auto' }}>
            {err ? err.message : '未知错误'}
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
