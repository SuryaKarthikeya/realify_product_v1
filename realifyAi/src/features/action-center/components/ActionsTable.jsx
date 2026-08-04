import React from 'react';
import { ACTION_COLUMNS } from '@/features/action-center/components/actionColumns';

const alignClass = (align) => (align === 'right' ? 'text-right' : 'text-left');

const ActionRow = React.memo(({ action, columns, isSelected, onSelect, ctx }) => (
  <tr
    onClick={() => onSelect(action)}
    aria-selected={isSelected}
    className={`cursor-pointer transition-colors ${isSelected
      ? 'bg-blue-50/70 dark:bg-blue-900/10'
      : 'hover:bg-gray-50 dark:hover:bg-slate-800/40'
      }`}
  >
    {columns.map((col) => (
      <td
        key={col.key}
        className={`px-4 py-3 ${alignClass(col.align)} ${col.className || ''}`}
        onClick={col.stopRowClick ? (e) => e.stopPropagation() : undefined}
      >
        {col.render(action, ctx)}
      </td>
    ))}
  </tr>
));

/**
 * Unified actions table — every action across all SKUs and categories,
 * unfiltered by default. Row click selects the action so the existing
 * right-side detail panel (Overview / Simulate) shows it; that panel is
 * untouched, only the trigger moved from card click to row click.
 */
const ActionsTable = ({
  actions = [],
  columns = ACTION_COLUMNS,
  selectedId,
  onSelect,
  onCta,
  emptyState = null,
}) => {
  if (!actions.length) {
    return (
      emptyState || (
        <div className="py-32 text-center">
          <div className="w-20 h-20 bg-gray-50 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4 border border-gray-100 dark:border-slate-800">
            <i className="fa-solid fa-magnifying-glass text-4xl text-gray-200"></i>
          </div>
          <p className="text-gray-500 dark:text-slate-500 font-bold tracking-tight">No actions match this search</p>
          <p className="text-xs text-gray-400 mt-1 tracking-widest">Clear the search or priority filter to see all actions</p>
        </div>
      )
    );
  }

  const ctx = { onCta };

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="sticky top-0 z-10 bg-white dark:bg-slate-900">
          <tr className="border-b border-gray-100 dark:border-slate-800">
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                className={`px-4 py-2.5 text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider whitespace-nowrap ${alignClass(col.align)}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-slate-800/60">
          {actions.map((action) => (
            <ActionRow
              key={action.id}
              action={action}
              columns={columns}
              isSelected={selectedId === action.id}
              onSelect={onSelect}
              ctx={ctx}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ActionsTable;
