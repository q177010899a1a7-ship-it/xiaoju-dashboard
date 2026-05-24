// 类型定义

export interface StockData {
  name: string;
  price: number;
  change: number;
  pct: number;
  volume: number;
  amount: number;
  high: number;
  low: number;
  open: number;
  close: number;
  time: string;
}

export interface MetalData {
  name: string;
  price: number;
  pct: number;
  change: number;
  open: number;
  high: number;
  low: number;
}

export interface USIndexData {
  name: string;
  symbol: string;
  type: 'index' | 'stock';
  price: number;
  previousClose: number;
  change: number;
  pct: number;
  high: number;
  low: number;
  open: number;
  volume: number;
  error?: string;
}

export interface CommodityData {
  name: string;
  symbol: string;
  price: number;
  previousClose: number;
  change: number;
  pct: number;
  high: number;
  low: number;
  open: number;
  unit: string;
  error?: string;
}

export interface ChartDataPoint {
  timestamp: number;
  price: number;
}

export interface HotItem {
  rank: number;
  title?: string;     // uapis 返回字段
  word?: string;       // 备用字段
  num?: number;
  hot_value?: string | number;  // uapis 返回格式化字符串如"105.7万"
  label_name?: string;
  raw_label?: string;
  label?: string;
  note?: string;
}

export interface HotSearchData {
  weibo?: HotItem[];
  douyin?: HotItem[];
  twitter?: HotItem[];
}

export interface NewsItem {
  title: string;
  link: string;
  description: string;
  published: string;
  source: string;
}

export interface NewsData {
  news: NewsItem[];
  sources: string[];
}

export interface GitHubProject {
  name: string;
  full_name: string;
  description: string;
  description_cn?: string;  // 中文翻译描述
  stars: number;
  forks: number;
  language: string;
  url: string;
  owner: string;
  avatar: string;
  created_at?: string;      // 创建时间
}

export interface GitHubData {
  projects: GitHubProject[];
  total: number;
  error?: string;
}

export interface ReportSection {
  title: string;
  content: string;
}

export interface Report {
  type: string;
  title: string;
  date: string;
  sections: ReportSection[];
  summary: string;
}

export interface HoroscopeData {
  sign: string;
  date: string;
  element?: string;
  planet?: string;
  lucky?: string[];
  today?: string;
  horoscope?: string;
  api_source?: string;
}

export interface CalendarData {
  date: string;
  weekday: string;
  lunar: string;
  yi: string[];
  ji: string[];
  jiri: string;
  xingzuo: string;
}

export interface ModuleConfig {
  id: string;
  title: string;
  visible: boolean;
  collapsed: boolean;
  order: number;
}

export interface DashboardLayout {
  modules: ModuleConfig[];
}

export interface DashboardConfig {
  refreshInterval: number;
  feishuWebhook: string;
  wecomWebhook: string;
  visibleModules: string[];
  openaiApiKey?: string;
  pushEnabled?: boolean;
}

export interface PushMessage {
  platform: 'feishu' | 'wecom';
  content: string;
  webhook?: string;
}

export interface SystemStatus {
  version: string;
  uptime: string;
  refresh_interval: number;
  cache: Record<string, boolean>;
  config: Record<string, boolean>;
}

export interface CryptoItem {
  symbol: string;
  name: string;
  price: number;
  change_24h: number;
  high_24h: number;
  low_24h: number;
  volume_24h: number;
}

export interface CryptoData {
  [symbol: string]: CryptoItem;
}
