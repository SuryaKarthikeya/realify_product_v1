import React, { useMemo } from 'react';
import SelectMenu from '@/components/ui/SelectMenu';
import {
  DATASET_STATUS_FILTERS,
  connectorDatasets,
  dataHealth,
  datasetTypes,
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
 * The rail beside Data.
 *
 * Same arrangement as Activity's: the filters belong to the whole dataset list
 * rather than to one column, and the tab reads them back so the rail and the
 * table's own search narrow a single list.
 */
const DataRail = ({ connector, filters, onChange }) => {
  const rows = useMemo(() => connectorDatasets(connector), [connector]);
  const types = useMemo(() => datasetTypes(rows), [rows]);
  const health = useMemo(() => dataHealth(connector, rows), [connector, rows]);

  const isFiltered = filters.type !== types[0] || filters.status !== DATASET_STATUS_FILTERS[0];

  return (
    <div className="space-y-4">

      {/* ── Filters ── */}
      <Card className="p-4">
        <div className="flex items-center justify-between gap-3 mb-3.5">
          <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white">Filters</h3>
          <button
            onClick={() => onChange({ type: types[0], status: DATASET_STATUS_FILTERS[0] })}
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
              options={types}
              onChange={(v) => onChange({ ...filters, type: v })}
              size="sm"
              ariaLabel="Dataset type"
            />
          </Field>

          <Field label="Status">
            <SelectMenu
              value={filters.status}
              options={DATASET_STATUS_FILTERS}
              onChange={(v) => onChange({ ...filters, status: v })}
              size="sm"
              ariaLabel="Dataset status"
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

      {/* ── Data health ── */}
      <Card className="p-4">
        <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white mb-2.5">Data health</h3>

        <p className="text-[28px] font-bold text-gray-900 dark:text-white leading-none">
          {health.quality}%
        </p>
        <p className="text-[12px] text-gray-500 dark:text-slate-400 mt-1">Overall data quality</p>

        <div className="mt-3 h-1.5 rounded-full bg-gray-100 dark:bg-slate-800 overflow-hidden flex">
          <div className="h-full bg-emerald-500" style={{ width: `${health.quality}%` }} />
          <div className="h-full bg-rose-500 flex-1" />
        </div>

        <div className="mt-3.5 space-y-2">
          {[
            { label: 'Valid records', value: health.validLabel, dot: 'bg-emerald-500' },
            { label: 'Invalid records', value: health.invalidLabel, dot: 'bg-rose-500' },
          ].map((row) => (
            <div key={row.label} className="flex items-center justify-between gap-3">
              <span className="flex items-center gap-2 min-w-0 text-[12px] text-gray-600 dark:text-slate-300">
                <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${row.dot}`} />
                <span className="truncate">{row.label}</span>
              </span>
              <span className="text-[12px] font-semibold text-gray-900 dark:text-white whitespace-nowrap flex-shrink-0">
                {row.value}
              </span>
            </div>
          ))}
        </div>

        <button className="text-[12px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 mt-3 flex items-center gap-1.5">
          View quality details <i className="fa-solid fa-arrow-right text-[9px]" />
        </button>
      </Card>

      {/* ── About data ── */}
      <Card className="p-4">
        <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white mb-2">About data</h3>
        <p className="text-[12px] text-gray-500 dark:text-slate-400 leading-relaxed">
          This data is fetched from {connector.name} and updated on a scheduled basis.
        </p>
        <button className="text-[12px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 mt-2.5 flex items-center gap-1.5">
          Learn more about data <i className="fa-solid fa-arrow-up-right-from-square text-[9px]" />
        </button>
      </Card>
    </div>
  );
};

export default DataRail;
