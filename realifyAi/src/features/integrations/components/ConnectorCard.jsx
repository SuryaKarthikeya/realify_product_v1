import React from 'react';
import { STATUS, CATEGORY_BY_KEY, statusLine } from '@/features/integrations/data/integrationsData';

/**
 * One connector. Grid and list layouts off the same data.
 *
 * The root is a `div` with a button role rather than a real `<button>`, because
 * it contains the Manage button and the kebab — nesting a button inside a button
 * is invalid HTML.
 */
const ConnectorCard = ({ connector, view = 'grid', onSelect, isSelected = false }) => {
  const status = statusLine(connector);
  const categoryLabel = CATEGORY_BY_KEY[connector.category] || connector.category;

  /* Selected wins over the attention ring, so the open card is always the one
     that reads as active. */
  const ring = isSelected
    ? 'border-indigo-500 dark:border-indigo-500 ring-1 ring-indigo-200 dark:ring-indigo-800'
    : status.ring || 'border-gray-200 dark:border-slate-800 hover:border-gray-300 dark:hover:border-slate-700';

  const selectable = {
    onClick: () => onSelect?.(connector),
    onKeyDown: (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect?.(connector); }
    },
    role: 'button',
    tabIndex: 0,
  };

  const stop = (e) => e.stopPropagation();

  const icon = (
    <div className="relative flex-shrink-0">
      <div className={`w-9 h-9 rounded-xl flex items-center justify-center text-[15px] ${connector.tone}`}>
        <i className={connector.icon} />
      </div>
      {isSelected && (
        <span className="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full bg-indigo-600 text-white flex items-center justify-center ring-2 ring-white dark:ring-slate-900">
          <i className="fa-solid fa-check text-[7px]" />
        </span>
      )}
    </div>
  );

  const statusRow = (
    <div className="flex items-center gap-1.5 min-w-0">
      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${status.dot}`} />
      <span className={`text-[11px] font-semibold whitespace-nowrap ${status.text}`}>
        {status.label}
      </span>
      {status.detail && (
        <span className="text-[11px] text-gray-400 dark:text-slate-500 truncate">
          {status.detail}
        </span>
      )}
    </div>
  );

  const actionButton = (
    <button
      onClick={stop}
      className={`flex-1 min-w-0 px-3 py-1.5 rounded-lg border text-[12px] font-semibold transition-colors truncate ${
        connector.status === STATUS.attention.key
          ? 'border-amber-300 dark:border-amber-700 text-amber-700 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-950/30'
          : 'border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800'
      }`}
    >
      {status.action}
    </button>
  );

  const kebab = (
    <button
      onClick={stop}
      aria-label={`More options for ${connector.name}`}
      className="w-8 h-7 flex-shrink-0 rounded-lg border border-gray-200 dark:border-slate-700 text-gray-400 hover:text-gray-600 dark:hover:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center justify-center"
    >
      <i className="fa-solid fa-ellipsis-vertical text-[11px]" />
    </button>
  );

  if (view === 'list') {
    return (
      <div
        {...selectable}
        className={`bg-white dark:bg-slate-900 border rounded-2xl px-4 py-3 flex items-center gap-3.5 transition-all cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ${ring}`}
      >
        {icon}
        <div className="min-w-0 w-[170px] flex-shrink-0">
          <p className="text-[13px] font-bold text-gray-900 dark:text-white truncate">{connector.name}</p>
          <p className="text-[9.5px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider truncate">
            {categoryLabel}
          </p>
        </div>
        <p className="text-[11.5px] text-gray-500 dark:text-slate-400 flex-1 min-w-0 truncate">
          Feeds: {connector.feeds.join(' · ')}
        </p>
        <div className="hidden sm:block flex-shrink-0">{statusRow}</div>
        <div className="flex items-center gap-1.5 flex-shrink-0 w-[150px]">
          {actionButton}
          {kebab}
        </div>
      </div>
    );
  }

  return (
    <div
      {...selectable}
      className={`bg-white dark:bg-slate-900 border rounded-2xl p-3.5 flex flex-col gap-2.5 transition-all cursor-pointer hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ${ring}`}
    >
      <div className="flex items-start gap-2.5">
        {icon}
        <div className="min-w-0 flex-1">
          <p className="text-[13px] font-bold text-gray-900 dark:text-white leading-snug">
            {connector.name}
          </p>
          <p className="text-[9.5px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider mt-0.5">
            {categoryLabel}
          </p>
        </div>
      </div>

      <p className="text-[11.5px] text-gray-500 dark:text-slate-400 truncate">
        Feeds: {connector.feeds.join(' · ')}
      </p>

      <div className="mt-auto pt-2.5 border-t border-gray-100 dark:border-slate-800 space-y-2.5">
        {statusRow}
        <div className="flex items-center gap-1.5">
          {actionButton}
          {kebab}
        </div>
      </div>
    </div>
  );
};

export default React.memo(ConnectorCard);
