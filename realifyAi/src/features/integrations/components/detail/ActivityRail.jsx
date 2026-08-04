import React from 'react';
import SelectMenu from '@/components/ui/SelectMenu';
import {
  ACTIVITY_STATUS_FILTERS,
  ACTIVITY_TYPES,
  nextScheduledSync,
} from '@/features/integrations/data/connectorDetailData';

const Card = ({ children, className = '' }) => (
  <div className={`bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl ${className}`}>
    {children}
  </div>
);

const Field = ({ label, children }) => (
  <div>
    <p className="text-[11.5px] font-semibold text-gray-600 dark:text-slate-400 mb-1.5">{label}</p>
    {children}
  </div>
);


/**
 * The rail beside Activity.
 *
 * Filters live here rather than in the table header because they belong to the
 * whole log, not to one column — and the tab reads them back so both sets of
 * controls narrow the same list.
 */
const ActivityRail = ({ connector, filters, onChange }) => {
  const upcoming = nextScheduledSync(connector);
  const isFiltered = filters.type !== ACTIVITY_TYPES[0] || filters.status !== ACTIVITY_STATUS_FILTERS[0];

  return (
    <div className="space-y-4">

      {/* ── Filters ── */}
      <Card className="p-4">
        <div className="flex items-center justify-between gap-3 mb-3.5">
          <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white">Filters</h3>
          <button
            onClick={() => onChange({ type: ACTIVITY_TYPES[0], status: ACTIVITY_STATUS_FILTERS[0] })}
            disabled={!isFiltered}
            className="text-[11.5px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 disabled:opacity-40 disabled:cursor-default"
          >
            Clear all
          </button>
        </div>

        <div className="space-y-3">
          <Field label="Type">
            <SelectMenu
              value={filters.type}
              options={ACTIVITY_TYPES}
              onChange={(v) => onChange({ ...filters, type: v })}
              size="sm"
              ariaLabel="Activity type"
            />
          </Field>

          <Field label="Status">
            <SelectMenu
              value={filters.status}
              options={ACTIVITY_STATUS_FILTERS}
              onChange={(v) => onChange({ ...filters, status: v })}
              size="sm"
              ariaLabel="Activity status"
            />
          </Field>

          <Field label="Date range">
            <div className="rounded-xl border border-gray-200 dark:border-slate-700 px-3 py-2 flex items-center gap-2.5">
              <i className="fa-regular fa-calendar text-[11px] text-gray-400 dark:text-slate-500 flex-shrink-0" />
              <span className="text-[12.5px] font-medium text-gray-800 dark:text-slate-200 truncate">
                May 6, 2025 – May 12, 2025
              </span>
            </div>
          </Field>
        </div>
      </Card>

      {/* ── Live status ── */}
      <div className="rounded-2xl border border-emerald-100 dark:border-emerald-900/40 bg-emerald-50/50 dark:bg-emerald-950/20 p-4">
        <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white mb-2">Live status</h3>
        <p className="text-[12.5px] font-semibold text-emerald-700 dark:text-emerald-400 flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          Healthy
        </p>
        <p className="text-[12px] text-gray-600 dark:text-slate-400 mt-1.5">All systems operational</p>
        <p className="text-[11px] text-gray-400 dark:text-slate-500 mt-0.5">
          Last checked {connector.lastSync || 'just now'}
        </p>
      </div>

      {/* ── Upcoming ── */}
      <Card className="p-4">
        <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white mb-3">Upcoming</h3>
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-start gap-2.5 min-w-0">
            <i className="fa-regular fa-clock text-[12px] text-gray-400 dark:text-slate-500 mt-[3px] flex-shrink-0" />
            <div className="min-w-0">
              <p className="text-[12.5px] font-semibold text-gray-900 dark:text-white leading-snug">
                {upcoming.label}
              </p>
              <p className="text-[11.5px] text-gray-500 dark:text-slate-400 mt-0.5">{upcoming.when}</p>
            </div>
          </div>
          <button className="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 text-[12px] font-semibold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-1.5 whitespace-nowrap flex-shrink-0">
            View schedule <i className="fa-solid fa-arrow-right text-[9px]" />
          </button>
        </div>
      </Card>

      {/* ── About activity ── */}
      <Card className="p-4">
        <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white mb-2">About activity</h3>
        <p className="text-[12px] text-gray-500 dark:text-slate-400 leading-relaxed">
          Activity logs help you monitor data syncs, updates, and issues.
        </p>
        <button className="text-[12px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 mt-2.5 flex items-center gap-1.5">
          Learn more about activity <i className="fa-solid fa-arrow-up-right-from-square text-[9px]" />
        </button>
      </Card>
    </div>
  );
};

export default ActivityRail;
