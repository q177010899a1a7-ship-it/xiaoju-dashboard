import React, { useState } from 'react';

interface ConfigPanelProps {
  config: DashboardConfig;
  onConfigChange: (config: DashboardConfig) => void;
  onClose?: () => void;
}

export interface DashboardConfig {
  refreshInterval: number;
  feishuWebhook: string;
  wecomWebhook: string;
  visibleModules: string[];
  openaiApiKey?: string;
  pushEnabled?: boolean;
}

const DEFAULT_CONFIG: DashboardConfig = {
  refreshInterval: 1800,
  feishuWebhook: '',
  wecomWebhook: '',
  openaiApiKey: '',
  pushEnabled: false,
  visibleModules: ['stock', 'us_stock', 'metals', 'commodity', 'hot', 'news', 'github', 'calendar', 'horoscope', 'report'],
};

export const ConfigPanel: React.FC<ConfigPanelProps> = ({ 
  config = DEFAULT_CONFIG, 
  onConfigChange,
  onClose,
}) => {
  const [localConfig, setLocalConfig] = useState<DashboardConfig>(config);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    onConfigChange(localConfig);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleReset = () => {
    setLocalConfig(DEFAULT_CONFIG);
    onConfigChange(DEFAULT_CONFIG);
  };

  const updateConfig = (key: keyof DashboardConfig, value: any) => {
    setLocalConfig(prev => ({ ...prev, [key]: value }));
  };

  const toggleModule = (moduleId: string) => {
    const modules = localConfig.visibleModules.includes(moduleId)
      ? localConfig.visibleModules.filter(m => m !== moduleId)
      : [...localConfig.visibleModules, moduleId];
    updateConfig('visibleModules', modules);
  };

  const allModules = [
    { id: 'stock', name: '📊 A股行情' },
    { id: 'us_stock', name: '🗽 美股行情' },
    { id: 'metals', name: '🥇 贵金属' },
    { id: 'commodity', name: '🛢️ 大宗商品' },
    { id: 'hot', name: '🔥 微博热搜' },
    { id: 'news', name: '📰 科技资讯' },
    { id: 'github', name: '⚙️ GitHub热门' },
    { id: 'calendar', name: '📅 今日黄历' },
    { id: 'horoscope', name: '⭐ 星座运势' },
    { id: 'report', name: '📰 小居早报' },
  ];

  return (
    <div className="space-y-6">
      {/* 刷新设置 */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-3">🔄 刷新设置</h3>
        <div className="space-y-2">
          <label className="flex items-center gap-2">
            <span className="text-sm text-gray-600 w-24">刷新间隔</span>
            <select
              value={localConfig.refreshInterval}
              onChange={(e) => updateConfig('refreshInterval', Number(e.target.value))}
              className="flex-1 border border-gray-300 rounded px-3 py-1.5 text-sm"
            >
              <option value={300}>5分钟</option>
              <option value={600}>10分钟</option>
              <option value={900}>15分钟</option>
              <option value={1800}>30分钟</option>
              <option value={3600}>1小时</option>
            </select>
          </label>
        </div>
      </div>

      {/* Webhook 设置 */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-3">📨 推送设置</h3>
        <div className="space-y-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">飞书 Webhook</label>
            <input
              type="text"
              value={localConfig.feishuWebhook}
              onChange={(e) => updateConfig('feishuWebhook', e.target.value)}
              placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
              className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">企业微信 Webhook</label>
            <input
              type="text"
              value={localConfig.wecomWebhook}
              onChange={(e) => updateConfig('wecomWebhook', e.target.value)}
              placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
              className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm"
            />
          </div>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={localConfig.pushEnabled}
              onChange={(e) => updateConfig('pushEnabled', e.target.checked)}
              className="rounded"
            />
            <span className="text-sm text-gray-600">启用自动推送</span>
          </label>
        </div>
      </div>

      {/* AI API Key 设置 */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-3">🤖 AI 报告设置</h3>
        <div className="space-y-2">
          <div>
            <label className="block text-xs text-gray-500 mb-1">OpenAI API Key（可选，用于AI生成报告）</label>
            <input
              type="password"
              value={localConfig.openaiApiKey || ''}
              onChange={(e) => updateConfig('openaiApiKey', e.target.value)}
              placeholder="sk-..."
              className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm"
            />
          </div>
          <p className="text-xs text-gray-400">
            如不配置API Key，系统将使用模板生成规则报告
          </p>
        </div>
      </div>

      {/* 模块可见性 */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-3">📦 显示模块</h3>
        <div className="grid grid-cols-2 gap-2">
          {allModules.map(module => (
            <label 
              key={module.id}
              className="flex items-center gap-2 p-2 rounded hover:bg-gray-50 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={localConfig.visibleModules.includes(module.id)}
                onChange={() => toggleModule(module.id)}
                className="rounded"
              />
              <span className="text-sm text-gray-700">{module.name}</span>
            </label>
          ))}
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex gap-3 pt-3 border-t border-gray-200">
        <button
          onClick={handleSave}
          className="flex-1 bg-blue-500 text-white rounded px-4 py-2 text-sm hover:bg-blue-600 transition-colors"
        >
          {saved ? '✓ 已保存' : '保存配置'}
        </button>
        <button
          onClick={handleReset}
          className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded transition-colors"
        >
          重置
        </button>
      </div>
    </div>
  );
};
