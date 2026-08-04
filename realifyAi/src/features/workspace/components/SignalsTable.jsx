import React from 'react';
import { getSignalColumns } from '@/features/workspace/components/signalColumns';

const alignClass = (align) =>
  align === 'right' ? 'text-right' : align === 'center' ? 'text-center' : 'text-left';

// ── One signal row ──
// Gmail-inspired: airy single line, whisper-quiet separator, soft hover, and a
// clear left-accent + tint for the selected state. Columns / content untouched.
// Collapsed beside the simulation panel every column still has to fit, and eight
// cells of `sm:px-3.5` alone burn ~220px. Tightening the gutter here rather than
// in the column config avoids losing to that media-query rule.
const cellPad = (isCollapsed) =>
  isCollapsed ? 'px-1.5 xl:px-2' : 'px-2.5 sm:px-3.5';

const SignalRow = React.memo(({ signal, columns, isSelected, onSelect, ctx, isCollapsed }) => (
  <tr
    onClick={() => onSelect?.(signal)}
    onKeyDown={(e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect?.(signal); }
    }}
    tabIndex={0}
    aria-selected={isSelected}
    className={`group cursor-pointer outline-none transition-colors duration-100 focus-ring ${isSelected
      ? 'bg-blue-50/80 dark:bg-blue-950/40'
      : 'hover:bg-slate-50 dark:hover:bg-slate-800/40'
      }`}
  >
    {columns.map((col, idx) => (
      <td
        key={col.key}
        className={`${cellPad(isCollapsed)} py-3 align-middle ${
          idx === 0
            ? `border-l-2 ${isSelected ? 'border-blue-500 dark:border-blue-400' : 'border-transparent'}`
            : ''
        } ${alignClass(col.align)} ${col.className || ''}`}
        onClick={col.stopRowClick ? (e) => e.stopPropagation() : undefined}
      >
        {col.render(signal, ctx)}
      </td>
    ))}
  </tr>
));

/** Label used in the empty state, so it reads as the domain the user is in. */
const DOMAIN_LABELS = {
  sales: 'revenue',
  margin: 'margin',
  inventory: 'inventory',
  ads: 'ads',
  cash: 'cash',
};

/**
 * Shown in place of rows when nothing matches.
 *
 * Distinguishes "no actions exist" from "your filters hid them all" — the second
 * is the recoverable case, so it offers a way back.
 */
const EmptyState = ({ activeDomain, isFiltered, onClearFilters }) => (
  <div className="flex flex-col items-center justify-center text-center px-6 py-14">
    <div className="w-11 h-11 rounded-full bg-gray-50 dark:bg-slate-800 flex items-center justify-center mb-3.5">
      <i className={`fa-solid ${isFiltered ? 'fa-filter-circle-xmark' : 'fa-circle-check'} text-[15px] text-gray-400 dark:text-slate-500`} />
    </div>

    <p className="text-[13.5px] font-bold text-gray-800 dark:text-slate-200 mb-1">
      {isFiltered
        ? 'No actions match these filters'
        : `No ${DOMAIN_LABELS[activeDomain] || ''} actions right now`}
    </p>

    <p className="text-[12.5px] text-gray-500 dark:text-slate-400 max-w-[340px] leading-relaxed">
      {isFiltered
        ? 'Every action is filtered out. Widen the channel, category or SKU filters to see what is available.'
        : 'Nothing needs your attention here — we will surface an action as soon as a signal crosses its threshold.'}
    </p>

    {isFiltered && onClearFilters && (
      <button
        onClick={onClearFilters}
        className="mt-4 px-4 py-1.5 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-[12px] font-bold text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/30 transition-colors"
      >
        Clear all filters
      </button>
    )}
  </div>
);

/**
 * Actions listing for the Workspace — one flat table row per signal.
 */
const SignalsTable = ({
  signals = [],
  columns,
  selectedId,
  onSelect,
  onSimulate,
  onTakeAction,
  isCollapsed = false,
  executedSignalIds = [],
  activeDomain = 'sales',
  isFiltered = false,
  onClearFilters,
}) => {
  const activeColumns = columns || getSignalColumns(isCollapsed, activeDomain);
  const ctx = { onSimulate, onTakeAction, executedSignalIds };

  return (
    <div className="w-full">
      <table className="w-full table-fixed">
        {/* Sticky, quiet header — barely-there labels with a single hairline rule */}
        <thead className="sticky top-0 z-20 bg-white/95 dark:bg-slate-900/95 backdrop-blur-sm">
          <tr className="border-b border-gray-100 dark:border-slate-800">
            {activeColumns.map((col, idx) => (
              <th
                key={col.key}
                scope="col"
                className={`${cellPad(isCollapsed)} py-2.5 ${isCollapsed ? 'text-[9px] tracking-[0.05em]' : 'text-[10px] tracking-[0.08em]'} font-mono font-semibold text-gray-400 dark:text-slate-500 uppercase whitespace-nowrap leading-none ${idx === 0 ? 'border-l-2 border-transparent' : ''} ${alignClass(col.align)} ${col.className || ''}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100/80 dark:divide-slate-800/50">
          {signals.map((signal) => (
            <SignalRow
              key={signal.id}
              signal={signal}
              columns={activeColumns}
              isSelected={selectedId === signal.id}
              onSelect={onSelect}
              ctx={ctx}
              isCollapsed={isCollapsed}
            />
          ))}
        </tbody>
      </table>

      {signals.length === 0 && (
        <EmptyState
          activeDomain={activeDomain}
          isFiltered={isFiltered}
          onClearFilters={onClearFilters}
        />
      )}
    </div>
  );
};

export default React.memo(SignalsTable);
