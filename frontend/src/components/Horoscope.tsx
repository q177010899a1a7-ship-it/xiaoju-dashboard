import React, { useState, useEffect } from 'react';
import { HoroscopeData } from '../types';

const ALL_SIGNS = [
  { name: '白羊座', emoji: '♈', recommended: false },
  { name: '金牛座', emoji: '♉', recommended: true },
  { name: '双子座', emoji: '♊', recommended: false },
  { name: '巨蟹座', emoji: '♋', recommended: true },
  { name: '狮子座', emoji: '♌', recommended: false },
  { name: '处女座', emoji: '♍', recommended: false },
  { name: '天秤座', emoji: '♎', recommended: false },
  { name: '天蝎座', emoji: '♏', recommended: false },
  { name: '射手座', emoji: '♐', recommended: false },
  { name: '摩羯座', emoji: '♑', recommended: false },
  { name: '水瓶座', emoji: '♒', recommended: false },
  { name: '双鱼座', emoji: '♓', recommended: false },
];

const CACHE: Record<string, HoroscopeData> = {};

// ─────────────────────────────────────────
// 英文文本情感打分
// ─────────────────────────────────────────
function score(text: string): number {
  const t = text || '';
  const pos = (t.match(/good|great|amazing|wonderful|excellent|love|loving|support|creative|insight|success|positive|growth|strong|powerful|helpful|improved?|better|opportunity|advance|progress|achieve|happy|joy|peace|calm|balance|fruitful|reward|supporting|rise.?above|prioritize.?yourself|build.?yourself|feel.?better|improved?|clearer?|brighter?|greatest?|best|smooth|enjoy|pleasant|warm|better.?ahead|have.?fun|choose.?fun|beneficial|strengthened|restored|stabilized|settled/gi) || []).length;
  const neg = (t.match(/difficult|hard|hurdle|obstacle|challenge|setback|fail|problem|issue|conflict|struggle|stress|stressful|anxiety|anxious|worried|worry|fear|uncertain|unexpected|surprise|trip|trap|lose|lost|break|fall|rough|tough|busy|exhaust|burned.?out|panic|pressure|tension|hostile|negative|weak|struggling|delay|complication|curveball|intentiona|push.?button|bored|restless|collect.?dust|unmanageable|busy.?energy|drain|drained|heavy|burden|wear|weary|too.?much|too.?many|hidden|suppress|mask|pretend|put.?on|less.?time|devote.?more|reduce|skip|avoid|deny|refuse|reject|turn.?down|lonely|alone|miss|hard.?time|not.?yourself|out.?of.?way|get.?out.?of.?way/gi) || []).length;
  return Math.min(5, Math.max(1, Math.round(3 + (pos - neg) * 0.35)));
}

// ─────────────────────────────────────────
// 维度关键词（按维度分类，比通用词表更精准）
// ─────────────────────────────────────────
type Dim = 'love' | 'career' | 'wealth';
const DIMS: Record<Dim, {
  label: string;
  // 英文句子级别的关键词（出现则该句属于此维度）
  sentKw: string[];
  // 正向信号词
  posKw: string[];
  // 负向信号词
  negKw: string[];
  posSummaries: string[];
  negSummaries: string[];
  neutralSummaries: string[];
  // 无信号时的"空内容"替代句（结合原文情感独立生成）
  emptyPosSummaries: string[];
  emptyNegSummaries: string[];
}> = {
  love: {
    label: '爱情',
    sentKw: ['love', 'loving', 'romantic', 'relationship', 'partner', 'date', 'dating', 'heart', 'passion', 'affection', 'intimacy', 'marriage', 'soulmate', 'crush', 'attraction', 'feelings', 'emotional', 'together', 'connection', 'loved', 'loved ones', 'fun with friends', 'friends', 'social', 'people'],
    posKw: ['love', 'romantic', 'heart', 'together', 'connection', 'loved ones', 'have fun', 'choose fun', 'beneficial', 'support', 'feel better', 'warm', 'brighter', 'better'],
    negKw: ['argue', 'argument', 'conflict', 'fight', 'tension', 'cold distant', 'breakup', 'alone', 'lonely', 'betray', 'jealous', 'push button', 'intentional', 'difficult to turn down', 'not yourself', 'get out of your own way', 'turn down', 'miss', 'hard time'],
    posSummaries: ['感情甜蜜升温，单身者有望遇到心动对象', '感情运势极佳，恋爱/已婚者关系更加融洽甜蜜', '人缘魅力上升，社交场合容易获得好感'],
    negSummaries: ['感情上易与伴侣产生口角，沟通时需注意语气', '可能出现烂桃花或旧情困扰，保持清醒勿冲动', '情绪波动较大，容易因为小事影响感情判断'],
    neutralSummaries: ['感情运势中规中矩，顺其自然即可'],
    emptyPosSummaries: ['整体运势向好，感情生活也在改善升温中', '今日心情舒畅，感情上的小问题能自然化解'],
    emptyNegSummaries: ['整体运势压力较大，感情上需多注意沟通方式', '今日状态偏紧绷，感情相处需多些耐心和理解'],
  },
  career: {
    label: '事业',
    sentKw: ['work', 'career', 'project', 'opportunity', 'promotion', 'success', 'goal', 'boss', 'colleague', 'team', 'office', 'creative', 'creative insight', 'productive', 'solution', 'mission', 'busy', 'deadline', 'busy work', 'workweek', 'prepare', 'unprepare', 'yod'],
    posKw: ['creative insight', 'rise above', 'setback', 'solution', 'mission', 'progress', 'advance', 'supporting yourself', 'build yourself', 'prioritize yourself', 'have fun', 'brighter', 'better', 'strengthened', 'restored', 'clearer', 'smooth', 'opportunity', 'achieve', 'productive', 'successful'],
    negKw: ['busy work', 'busy energy', 'setback', 'obstacle', 'hurdle', 'deadline', 'unmanageable', 'burned out', 'struggle', 'pressure', 'stress', 'stressful', 'complication', 'less time socializing', 'devote more energy to goals', 'not prepare in advance', 'get out of your own way', 'curveball', 'drain', 'drained', 'heavy', 'burden', 'weary'],
    posSummaries: ['工作进展顺利，项目有望取得突破性进展', '贵人运强，工作中的困难容易得到同事帮助', '创意涌现，适合推动新计划或学习新技能'],
    negSummaries: ['工作压力较大，注意合理分配精力避免出错', '职场可能有小人作祟，与人合作需多留心眼', '状态欠佳，不宜做重大决策或关键谈判'],
    neutralSummaries: ['事业运势平稳，按部就班推进即可'],
    emptyPosSummaries: ['整体运势向好，工作上的挑战能从容应对', '今日状态不错，处理工作事务会更加得心应手'],
    emptyNegSummaries: ['整体运势压力较大，工作上需谨慎应对避免失误', '今日精力偏紧绷，重要工作建议择日再推进'],
  },
  wealth: {
    label: '财富',
    sentKw: ['money', 'financial', 'income', 'invest', 'investment', 'save', 'rich', 'wealth', 'profit', 'gain', 'earn', 'bonus', 'salary', 'deal', 'bargain', 'afford', 'reward', 'windfall'],
    posKw: ['money', 'financial', 'income', 'profit', 'gain', 'bonus', 'reward', 'windfall', 'bargain', 'afford', 'save', 'wealth', 'rich', 'earn', 'prosper'],
    negKw: ['expense', 'spending', 'debt', 'lose', 'loss', 'losses', 'broke', 'cost', 'costly', 'waste', 'wasted', 'scam', 'trick', 'trap', 'risk', 'risky', 'curveball', 'spending time with friends', 'fun with friends', 'get out of your own way'],
    posSummaries: ['财运上升，理财投资容易有意外收获', '今日适合谈合作或签合同，有利可图', '财务状况改善，可能有奖金或兼职收入'],
    negSummaries: ['财务上需谨慎，防止破财或冲动消费', '投资理财有风险，不宜冒进或轻信推荐', '可能有意外支出，建议提前做好预算规划'],
    neutralSummaries: ['财富运势平稳，量入为出保守理财即可'],
    emptyPosSummaries: ['整体运势向好，财务上的小问题能顺利化解', '今日心情顺畅，财务决策更容易做出明智选择'],
    emptyNegSummaries: ['整体运势有压力，财务决策宜谨慎保守为主', '今日状态偏紧张，涉及金钱的事情建议三思后行'],
  },
};

function pick(arr: string[]): string {
  // 用文本长度做 seed，选择相对固定的项（不用 random）
  return arr[0];
}

function analyzeDim(rawText: string, dim: Dim): { label: string; stars: number; summary: string } {
  const cfg = DIMS[dim];
  const tl = rawText.toLowerCase();

  // 1. 找所有句子，按 sentKw 分类到维度
  const sentences = rawText.split(/[.!?]/).map(s => s.trim()).filter(s => s.length > 5);
  const dimSents = sentences.filter(s =>
    cfg.sentKw.some(kw => s.toLowerCase().includes(kw.toLowerCase()))
  );

  // 2. 计算维度内正/负信号
  const posHits = cfg.posKw.reduce((n, kw) => n + ((tl.match(new RegExp(kw.replace(/[.?]/g, ''), 'gi')) || []).length), 0);
  const negHits = cfg.negKw.reduce((n, kw) => n + ((tl.match(new RegExp(kw.replace(/[.?]/g, ''), 'gi')) || []).length), 0);

  // 3. 打分：优先用维度相关句，否则用全文情感
  let stars: number;
  let summary: string;

  if (dimSents.length > 0) {
    const dimText = dimSents.join(' ');
    stars = score(dimText);
    if (posHits > negHits && stars >= 4) {
      summary = cfg.posSummaries[Math.min(posHits - 1, cfg.posSummaries.length - 1)];
    } else if (negHits > posHits && stars <= 2) {
      summary = cfg.negSummaries[Math.min(negHits - 1, cfg.negSummaries.length - 1)];
    } else {
      summary = cfg.neutralSummaries[0];
    }
  } else {
    // 无维度专属句 → 用全文情感独立判断
    const overallStars = score(rawText.slice(0, 300));
    if (overallStars >= 4) {
      summary = cfg.emptyPosSummaries[Math.min(posHits, cfg.emptyPosSummaries.length - 1)];
    } else if (overallStars <= 2) {
      summary = cfg.emptyNegSummaries[Math.min(negHits, cfg.emptyNegSummaries.length - 1)];
    } else {
      summary = cfg.neutralSummaries[0];
    }
    stars = Math.min(5, Math.max(1, overallStars + (posHits - negHits)));
  }

  return { label: cfg.label, stars, summary };
}

const Stars: React.FC<{ stars: number }> = ({ stars }) => (
  <span className="text-sm leading-none shrink-0">
    {[1, 2, 3, 4, 5].map(i => (
      <span key={i} className={i <= stars ? 'text-amber-400' : 'text-gray-300'}>★</span>
    ))}
  </span>
);

interface Props { apiBase?: string; }

export const Horoscope: React.FC<Props> = ({ apiBase = '' }) => {
  const [selected, setSelected] = useState<string>('金牛座');
  const [data, setData] = useState<HoroscopeData | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchSign = async (sign: string) => {
    if (CACHE[sign]) { setData(CACHE[sign]); return; }
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/life/horoscope?sign=${encodeURIComponent(sign)}`);
      const json: HoroscopeData = await res.json();
      CACHE[sign] = json;
      setData(json);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchSign('金牛座'); fetchSign('巨蟹座'); }, []);

  const handleChange = (sign: string) => { setSelected(sign); fetchSign(sign); };

  const info = ALL_SIGNS.find(s => s.name === selected);
  const emoji = info?.emoji || '⭐';
  const rawText = data?.horoscope || '';
  const dims = rawText
    ? (['love', 'career', 'wealth'] as Dim[]).map(k => analyzeDim(rawText, k))
    : [];

  return (
    <div className="space-y-3">
      <div>
        <select
          value={selected}
          onChange={e => handleChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-purple-300"
        >
          {ALL_SIGNS.map(s => (
            <option key={s.name} value={s.name}>
              {s.emoji} {s.name}{s.recommended ? ' ⭐' : ''}
            </option>
          ))}
        </select>
        <p className="text-xs text-gray-400 mt-1">
          ⭐ 重点关注：{ALL_SIGNS.filter(s => s.recommended).map(s => s.name).join('、')}
        </p>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-pulse text-gray-400 text-sm">星座运势加载中...</div>
        </div>
      )}

      {!loading && !data && (
        <div className="text-center py-8 text-gray-400 text-sm">暂无数据</div>
      )}

      {!loading && data && (
        <>
          <div className="text-center pb-3 border-b border-gray-200">
            <p className="text-3xl">{emoji}</p>
            <p className="text-base font-semibold text-gray-800">
              {data.sign || selected}
              {info?.recommended && <span className="ml-1 text-amber-400">⭐</span>}
            </p>
            <p className="text-xs text-gray-400">{data.date}</p>
            <div className="flex justify-center gap-3 mt-1">
              {data.element && <span className="text-xs bg-purple-50 text-purple-500 px-2 py-0.5 rounded">{data.element}元素</span>}
              {data.planet && <span className="text-xs bg-blue-50 text-blue-500 px-2 py-0.5 rounded">{data.planet}</span>}
            </div>
          </div>

          <div className="space-y-2">
            {dims.map(dim => (
              <div key={dim.label} className="flex items-start gap-3 py-2 border-b border-gray-50 last:border-0">
                <span className="text-xs text-gray-500 w-8 shrink-0 pt-0.5">{dim.label}</span>
                <Stars stars={dim.stars} />
                <span className="text-xs text-gray-600 flex-1 leading-relaxed">{dim.summary}</span>
              </div>
            ))}
          </div>

          {data.lucky && data.lucky.length > 0 && (
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs text-gray-500 shrink-0">幸运：</span>
              {data.lucky.map((item, idx) => (
                <span key={idx} className="text-xs bg-yellow-50 text-yellow-600 px-2 py-0.5 rounded border border-yellow-100">{item}</span>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
};
