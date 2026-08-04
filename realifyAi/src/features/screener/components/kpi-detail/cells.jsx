import React from 'react';

/** Cell renderers shared by the KPI drill-down tables. */

/* ── Mini sub-components ───────────────────────────────────────── */
const CHANNEL_COLORS = {
  'Amazon': 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300',
  'Shopify': 'bg-green-100  dark:bg-green-900/30  text-green-700  dark:text-green-300',
  'TikTok Shop': 'bg-sky-100    dark:bg-sky-900/30    text-sky-700    dark:text-sky-300',
  'Mixed': 'bg-gray-100   dark:bg-slate-800     text-gray-600   dark:text-slate-400',
};

export const ChannelBadge = ({ ch }) => (
  <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-md whitespace-nowrap ${CHANNEL_COLORS[ch] || CHANNEL_COLORS['Mixed']}`}>{ch}</span>
);

export const ProductCell = ({ name, sku, cat }) => (
  <div className="min-w-0">
    <p className="text-xs font-semibold text-gray-800 dark:text-slate-200 truncate leading-tight">{name}</p>
    <p className="text-[10px] text-gray-400 dark:text-slate-500 leading-tight">{sku} · {cat}</p>
  </div>
);

export const CampaignCell = ({ name, sku, type: _type }) => (
  <div className="min-w-0">
    <p className="text-xs font-semibold text-gray-800 dark:text-slate-200 truncate leading-tight">{name}</p>
    <p className="text-[10px] text-gray-400 dark:text-slate-500 leading-tight">{sku}</p>
  </div>
);

export const ReturnQtyCell = ({ qty, units }) => {
  const rate = qty / units * 100;
  return (
    <span className={rate > 8 ? 'text-red-500 dark:text-red-400 font-semibold' : rate > 4 ? 'text-amber-500 font-medium' : 'text-gray-500 dark:text-slate-400'}>
      {qty}
    </span>
  );
};

export const PctBar = ({ pct }) => (
  <div className="flex items-center gap-1.5 justify-end">
    <div className="w-16 h-1.5 bg-gray-100 dark:bg-slate-700 rounded-full overflow-hidden">
      <div className="h-full bg-blue-400 dark:bg-blue-500 rounded-full" style={{ width: `${Math.min(100, +pct)}%` }} />
    </div>
    <span className="text-[10px] text-gray-500 dark:text-slate-400 w-8 text-right">{pct}%</span>
  </div>
);

export const BBCell = ({ pct, status }) => (
  <span className={`font-semibold ${status === 'Winning' ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'}`}>{pct}%</span>
);

export const BBStatus = ({ status }) => (
  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-md ${status === 'Winning' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'}`}>{status}</span>
);

export const DOCStatus = ({ s }) => {
  const cfg = { Low: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400', Healthy: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300', Excess: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400' };
  return <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-md ${cfg[s] || cfg.Healthy}`}>{s}</span>;
};

const AD_TYPE = {
  SP: { label: 'Sponsored Products', color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' },
  SB: { label: 'Sponsored Brands', color: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300' },
  SD: { label: 'Sponsored Display', color: 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300' },
  TT: { label: 'TikTok Ads', color: 'bg-sky-100 dark:bg-sky-900/30 text-sky-700 dark:text-sky-300' },
  GS: { label: 'Google Shopping', color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' },
};
export const AdTypeBadge = ({ t }) => {
  const c = AD_TYPE[t] || AD_TYPE.SP;
  return <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-md whitespace-nowrap ${c.color}`}>{c.label}</span>;
};

export const SettlementStatus = ({ s, date }) => (
  <div className="text-center">
    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-md block mb-0.5 ${s === 'Settled' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300'}`}>{s}</span>
    <span className="text-[9px] text-gray-400 dark:text-slate-500">{date}</span>
  </div>
);

export const PaidBadge = ({ s }) => (
  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-md ${s === 'Paid' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-300'}`}>{s}</span>
);

const CAT_COLORS = {
  'Inventory Restock': 'bg-blue-100   dark:bg-blue-900/30   text-blue-700   dark:text-blue-300',
  'Ad Spend': 'bg-purple-100 dark:bg-purple-900/30 text-purple-700  dark:text-purple-300',
  'Fulfillment / FBA': 'bg-orange-100 dark:bg-orange-900/30 text-orange-700  dark:text-orange-300',
  'Platform Fees': 'bg-gray-100   dark:bg-slate-800     text-gray-600    dark:text-slate-400',
  'Returns & Refunds': 'bg-red-100    dark:bg-red-900/30    text-red-600     dark:text-red-400',
  'Shipping & Freight': 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700  dark:text-yellow-300',
  'SaaS / Software': 'bg-teal-100   dark:bg-teal-900/30   text-teal-700    dark:text-teal-300',
};
export const CatBadge = ({ cat }) => (
  <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-md whitespace-nowrap ${CAT_COLORS[cat] || 'bg-gray-100 dark:bg-slate-800 text-gray-500'}`}>{cat}</span>
);

/* ── Totals row renderer ───────────────────────────────────────── */


/* ── Totals row renderer ───────────────────────────────────────── */

/* ── Main Modal ────────────────────────────────────────────────── */
