import { V2_DATE_OPTS, V2_CAT_OPTS } from '@/constants/filterOptions';

// ─── Product heatmap ────────────────────────────────────────────────────────────

export const getHeatColor = (change) => {
  if (change >= 25) return '#000000';
  if (change >= 18) return '#111827';
  if (change >= 12) return '#1f2937';
  if (change >= 7) return '#374151';
  if (change >= 3) return '#4b5563';
  if (change >= 0) return '#9ca3af';
  if (change >= -3) return '#d1d5db';
  if (change >= -8) return '#e5e7eb';
  if (change >= -14) return '#f3f4f6';
  return '#f9fafb';
};

// ─── Campaign / ROAS status badge — shared by Sales ROAS table and Ads campaign table ──

export const campaignStatusColor = (status) => {
  if (status === 'Scale') return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400';
  if (status === 'Healthy') return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400';
  if (status === 'Review') return 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400';
  return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400';
};

// ─── Date/calendar helpers ───────────────────────────────────────────────────────

export const isSameDay = (a, b) => !!(a && b && a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate());

export const isInRange = (date, start, end) => {
  if (!start || !end) return false;
  const d = date.getTime(), s = Math.min(start.getTime(), end.getTime()), e = Math.max(start.getTime(), end.getTime());
  return d > s && d < e;
};

export const formatCalDate = (d) => !d ? '' : `${d.getDate()} ${['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][d.getMonth()]} ${d.getFullYear()}`;

export const quickToRange = (key) => {
  const end = new Date(); end.setHours(23, 59, 59, 999);
  const start = new Date(end);
  if (key === 'last-7-days') start.setDate(start.getDate() - 6);
  else if (key === 'last-30-days') start.setDate(start.getDate() - 29);
  else if (key === 'last-90-days') start.setDate(start.getDate() - 89);
  else if (key === 'ytd') { start.setMonth(0); start.setDate(1); }
  else start.setDate(start.getDate() - 29);
  start.setHours(0, 0, 0, 0);
  return { start, end };
};

export const v2DateLabel = (v) => V2_DATE_OPTS.find(([k]) => k === v)?.[1] || v;
export const v2CatLabel = (v) => V2_CAT_OPTS.find(([k]) => k === v)?.[1] || v;
