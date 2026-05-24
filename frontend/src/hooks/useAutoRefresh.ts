import { useState, useEffect, useCallback, useRef } from 'react';

interface UseAutoRefreshOptions {
  interval?: number; // 刷新间隔（毫秒）
  enabled?: boolean;
  onRefresh: () => Promise<void>;
  // 持久化缓存的 key
  storageKey?: string;
  // 从本地存储加载初始数据
  loadFromStorage?: () => void;
}

export function useAutoRefresh({
  interval = 1800000, // 默认30分钟
  enabled = true,
  onRefresh,
  storageKey,
  loadFromStorage,
}: UseAutoRefreshOptions) {
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [nextRefresh, setNextRefresh] = useState<Date>(new Date(Date.now() + interval));
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isStaleData, setIsStaleData] = useState(false); // 是否显示历史数据
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const refresh = useCallback(async (showStale = false) => {
    if (isRefreshing) return;

    setIsRefreshing(true);
    if (showStale) setIsStaleData(true);
    try {
      await onRefresh();
      setLastRefresh(new Date());
      setNextRefresh(new Date(Date.now() + interval));
      setIsStaleData(false); // 刷新成功后清除历史数据标记
    } catch (error) {
      console.error('Refresh failed:', error);
    } finally {
      setIsRefreshing(false);
    }
  }, [onRefresh, isRefreshing, interval]);

  // 从 localStorage 恢复历史数据（同步，立即显示）
  useEffect(() => {
    if (storageKey && loadFromStorage) {
      loadFromStorage();
      // 检查是否是历史数据（距上次刷新超过5分钟）
      const stored = localStorage.getItem(storageKey + '_time');
      if (stored) {
        const last = new Date(parseInt(stored, 10));
        const now = Date.now();
        if (now - last.getTime() > 5 * 60 * 1000) {
          setIsStaleData(true);
        }
      }
    }
  }, [storageKey, loadFromStorage]);

  useEffect(() => {
    if (!enabled) return;

    // 立即后台刷新一次（不阻塞，展示历史数据）
    refresh(true);

    // 设置定时器
    timerRef.current = setInterval(() => refresh(false), interval);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [enabled, interval, refresh]);

  const timeUntilNext = Math.max(0, nextRefresh.getTime() - Date.now());
  const minutes = Math.floor(timeUntilNext / 60000);
  const seconds = Math.floor((timeUntilNext % 60000) / 1000);

  return {
    lastRefresh,
    nextRefresh,
    isRefreshing,
    isStaleData,
    timeUntilNext: `${minutes}:${seconds.toString().padStart(2, '0')}`,
    refresh: () => refresh(false),
  };
}