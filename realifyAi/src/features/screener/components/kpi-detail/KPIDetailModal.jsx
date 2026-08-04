import React from 'react';
import Modal from '@/components/overlays/Modal';
import { getTableDef } from '@/features/screener/components/kpi-detail/tableDefinitions';
import { renderTotalCell } from '@/features/screener/components/kpi-detail/renderTotalCell';

/* ── Period labels ─────────────────────────────────────────────── */
const PERIOD_LABELS = {
  'last-7-days': 'Last 7 Days',
  'last-30-days': 'Last 30 Days',
  'last-90-days': 'Last 90 Days',
  'ytd': 'Year to Date',
  'custom': 'Custom Range',
};

/* ── Format helpers ────────────────────────────────────────────── */


/* ── Main Modal ────────────────────────────────────────────────── */
const KPIDetailModal = ({ isOpen, onClose, stat, filterContext = {} }) => {
  if (!isOpen || !stat) return null;

  const periodLabel = PERIOD_LABELS[filterContext?.dateRange] || 'All Time';
  const { summary, cols, rows, totals } = getTableDef(stat.title);
  const activeFilters = [
    ...(filterContext.categories?.length ? filterContext.categories.map(c => c) : []),
    ...(filterContext.channels?.length ? filterContext.channels.map(c => c) : []),
  ];

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div
        className="bg-white dark:bg-slate-900 w-full max-w-5xl rounded-2xl shadow-2xl overflow-hidden border border-gray-100 dark:border-slate-800 flex flex-col"
        style={{ maxHeight: '90vh' }}
        onClick={e => e.stopPropagation()}
      >
        {/* ── Header ── */}
        <div className="flex items-start justify-between px-7 py-6 border-b border-gray-100 dark:border-slate-800 flex-shrink-0">
          <div className="min-w-0 flex-1 mr-4">
            <div className="flex items-center gap-2.5 flex-wrap mb-2">
              <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">{stat.title}</h3>
              <span className={`text-[11px] font-bold px-2.5 py-1 rounded-full ${stat.isPositive !== false ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400' : 'bg-red-100 dark:bg-red-900/30 text-red-500 dark:text-red-400'}`}>
                {stat.change}&nbsp;
                <i className={`fa-solid ${stat.isPositive !== false ? 'fa-arrow-trend-up' : 'fa-arrow-trend-down'} text-[9px]`} />
              </span>
            </div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <span className="text-3xl font-bold text-gray-900 dark:text-slate-100 leading-none">{stat.value}</span>
              <span className="text-xs text-gray-500 dark:text-slate-400 bg-gray-100 dark:bg-slate-800 px-2.5 py-1 rounded-md">{periodLabel}</span>
              {activeFilters.map((f, i) => (
                <span key={i} className="text-xs text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800/60 px-2.5 py-1 rounded-md">{f}</span>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-1 flex-shrink-0">
            <button className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-400 transition-colors" title="Download">
              <i className="fa-solid fa-download text-sm" />
            </button>
            <button onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-400 transition-colors">
              <i className="fa-solid fa-xmark" />
            </button>
          </div>
        </div>

        {/* ── Summary stats ── */}
        <div className="flex gap-0 border-b border-gray-100 dark:border-slate-800 flex-shrink-0">
          {summary.map((s, i) => (
            <div key={i} className={`flex-1 px-7 py-5 ${i < summary.length - 1 ? 'border-r border-gray-100 dark:border-slate-800' : ''}`}>
              <p className="text-[10px] font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-1.5">{s.label}</p>
              <p className="text-base font-bold text-gray-900 dark:text-slate-100">{s.value}</p>
            </div>
          ))}
        </div>

        {/* ── Table ── */}
        <div className="flex-1 overflow-auto custom-scrollbar">
          <table className="w-full border-collapse" style={{ minWidth: 640 }}>
            <thead className="sticky top-0 z-10 bg-gray-50 dark:bg-slate-800/80 backdrop-blur-sm">
              <tr>
                {cols.map((col, i) => (
                  <th
                    key={i}
                    className={`px-5 py-3.5 text-[10px] font-bold text-gray-500 dark:text-slate-400 uppercase tracking-widest whitespace-nowrap border-b border-gray-100 dark:border-slate-700 ${col.cls}`}
                    style={col.minW ? { minWidth: col.minW } : undefined}
                  >
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-slate-700/60">
              {rows.map((row, ri) => (
                <tr key={ri} className="hover:bg-gray-50/80 dark:hover:bg-slate-800/40 transition-colors group">
                  {cols.map((col, ci) => (
                    <td key={ci} className={`px-5 py-3.5 text-xs ${col.cls}`}>
                      {col.render(row)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
            {totals && (
              <tfoot>
                <tr className="bg-gray-50 dark:bg-slate-800/60 border-t-2 border-gray-200 dark:border-slate-700">
                  {cols.map((col, i) => (
                    <td key={i} className={`px-5 py-3.5 text-xs ${col.cls}`}>
                      {renderTotalCell(col, totals)}
                    </td>
                  ))}
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      </div>
    </Modal>
  );
};

export default KPIDetailModal;
