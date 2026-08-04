/** Number/currency formatting used across the KPI drill-down tables. */

/* ── Format helpers ────────────────────────────────────────────── */
export const $c = (n) => {
  if (n == null) return '—';
  if (n >= 1000000) return `$${(n / 1000000).toFixed(2)}M`;
  if (n >= 1000) return `$${(n / 1000).toFixed(1)}K`;
  return `$${Math.round(n).toLocaleString()}`;
};
export const fN = (n) => n == null ? '—' : n >= 1000 ? `${(n / 1000).toFixed(1)}K` : n.toLocaleString();
export const fP = (n) => n == null ? '—' : `${(+n).toFixed(1)}%`;
export const fX = (n) => n == null ? '—' : `${(+n).toFixed(2)}x`;
export const fPr = (n) => n == null ? '—' : `$${(+n).toFixed(2)}`;

/* ── Product master data ───────────────────────────────────────── */
