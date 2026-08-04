import React from 'react';

// Compact, sticky-header data table primitives shared across the Detailed View
// tabs (Sales/Ads/etc). Denser than the generic <DataTable> — uppercase 10px
// headers, 2.5px row padding, optional scrollable max-height body.

export const TableCard = ({ children, scrollable }) => (
  <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl overflow-hidden">
    <div className={scrollable ? 'overflow-auto max-h-[300px]' : 'overflow-x-auto'}>{children}</div>
  </div>
);

export const TH = ({ children }) => (
  <th className="px-4 py-2.5 text-left text-[10px] font-bold uppercase tracking-wider text-gray-400 dark:text-slate-500 whitespace-nowrap">{children}</th>
);

export const TD = ({ children, className = '' }) => (
  <td className={`px-4 py-2.5 text-xs ${className}`}>{children}</td>
);

export const TR = ({ children, onClick }) => (
  <tr onClick={onClick} className={`border-b border-gray-50 dark:border-slate-800/50 hover:bg-gray-50/40 dark:hover:bg-slate-800/20 transition-colors ${onClick ? 'cursor-pointer' : ''}`}>{children}</tr>
);

export const TableHead = ({ cols }) => (
  <thead className="sticky top-0 z-10">
    <tr className="border-b border-gray-100 dark:border-slate-800 bg-gray-50 dark:bg-slate-800">
      {cols.map(c => <TH key={c}>{c}</TH>)}
    </tr>
  </thead>
);
