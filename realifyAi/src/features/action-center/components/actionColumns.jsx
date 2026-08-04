import React from 'react';
import {
  CATEGORY_ICONS,
  formatImpactPct,
  formatImpactValue,
  getActionCta,
} from '@/config/actionTypeConfig';

const PRIORITY_DOT = {
  CRITICAL: 'bg-red-500',
  HIGH: 'bg-orange-500',
  MEDIUM: 'bg-yellow-500',
  LOW: 'bg-blue-500',
};

/**
 * ── Column config ──
 * Add / remove / reorder columns here; the table body and header are both
 * generated from this array, so no JSX changes are needed per column.
 *
 * Each column: { key, header, align?, className?, render(action, ctx) }
 * `ctx` carries the row handlers ({ onCta }).
 */
export const ACTION_COLUMNS = [
  {
    key: 'name',
    header: 'Action Name',
    render: (action) => (
      <div className="flex items-center gap-2.5 min-w-0">
        <span
          className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${PRIORITY_DOT[action.priority] || PRIORITY_DOT.LOW}`}
          title={action.priority}
        />
        <div className="min-w-0">
          <p className="text-[13px] font-semibold text-gray-900 dark:text-slate-100 truncate">{action.title}</p>
          <p className="text-[10.5px] font-mono text-gray-400 dark:text-slate-500 mt-0.5">
            {action.actionId} · {action.signalType}
          </p>
        </div>
      </div>
    ),
  },
  {
    key: 'sku',
    header: 'Affected SKU',
    className: 'whitespace-nowrap',
    render: (action) => (
      <span className="text-[11.5px] font-mono bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-slate-300 px-1.5 py-0.5 rounded">
        {action.skuCode || '—'}
      </span>
    ),
  },
  {
    key: 'category',
    header: 'Category',
    className: 'whitespace-nowrap',
    render: (action) => (
      <span className="inline-flex items-center gap-1.5 text-[12px] font-medium text-gray-600 dark:text-slate-400">
        <i className={`fa-solid ${CATEGORY_ICONS[action.category] || 'fa-wallet'} text-[10px] opacity-70`} />
        {action.category}
      </span>
    ),
  },
  {
    key: 'impact',
    header: 'Impact Value',
    align: 'right',
    className: 'whitespace-nowrap',
    render: (action) => {
      const isPositive = (action.impactValue || 0) >= 0;
      const tone = isPositive
        ? 'text-emerald-600 dark:text-emerald-400'
        : 'text-red-600 dark:text-red-400';
      return (
        <div className={`font-mono ${tone}`} title={action.impactBasisLabel}>
          <span className="text-[13px] font-semibold">{formatImpactValue(action.impactValue)}</span>
          <span className="text-gray-400 dark:text-slate-500 font-normal text-[11px]">/mo</span>
          <div className="text-[11px] font-semibold mt-0.5">{formatImpactPct(action.impactPct)}</div>
        </div>
      );
    },
  },
  {
    key: 'cta',
    header: '',
    align: 'right',
    className: 'whitespace-nowrap',
    stopRowClick: true,
    render: (action, ctx) => {
      const cta = getActionCta(action);
      return (
        <button
          onClick={(e) => {
            e.stopPropagation();
            ctx.onCta?.(action);
          }}
          className="inline-flex items-center justify-center h-7 px-3 whitespace-nowrap max-w-full text-[11.5px] font-bold leading-none text-white bg-[#2563eb] hover:bg-[#1d4ed8] dark:bg-[#2563eb] dark:hover:bg-[#1d4ed8] rounded-[8px] transition active:scale-95 shadow-sm"
        >
          <i className={`fa-solid ${cta.icon} mr-1.5 text-[10px]`} />
          {cta.label}
        </button>
      );
    },
  },
];
