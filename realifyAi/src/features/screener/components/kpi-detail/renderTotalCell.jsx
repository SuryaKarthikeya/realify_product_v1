import React from 'react';

/** Renders the totals row by reusing each column's own cell renderer. */
export const renderTotalCell = (col, totals) => {
  const v = totals[col.key];
  if (col.key === 'name') return <span className="font-bold text-gray-900 dark:text-slate-100 text-[11px] uppercase tracking-wide">Total</span>;
  if (v == null) return null;
  // Use the column's render on a synthetic row built from totals
  const synth = { ...totals, name: 'TOTAL', channel: '', cat: '' };
  try { return col.render(synth); } catch { return null; }
};
