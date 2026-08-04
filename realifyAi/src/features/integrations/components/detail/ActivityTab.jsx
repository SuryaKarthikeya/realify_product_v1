import React, { useMemo, useState } from 'react';
import SelectMenu from '@/components/ui/SelectMenu';
import {
  ACTIVITY_STATUS,
  activityFeeds,
  activitySummary,
  connectorActivity,
} from '@/features/integrations/data/connectorDetailData';

const PAGE_SIZE = 5;

const Card = ({ children, className = '' }) => (
  <div className={`bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl ${className}`}>
    {children}
  </div>
);

/**
 * Every sync, update and event for one connector.
 *
 * The tiles, the feed filter and the pagination all read from the same log, so
 * the counts above the table always describe the rows in it.
 */
const ActivityTab = ({ connector, filters }) => {
  const rows = useMemo(() => connectorActivity(connector), [connector]);
  const summary = useMemo(() => activitySummary(connector, rows), [connector, rows]);
  const feeds = useMemo(() => activityFeeds(rows), [rows]);

  const [feed, setFeed] = useState('All feeds');
  const [page, setPage] = useState(1);

  /* The rail owns Type and Status; this tab owns the feed. Filtering here keeps
     the two sets of controls acting on one list. */
  const filtered = useMemo(
    () =>
      rows.filter(
        (r) =>
          (feed === 'All feeds' || r.feed === feed) &&
          (!filters?.type || filters.type === 'All types' || r.type === filters.type) &&
          (!filters?.status ||
            filters.status === 'All status' ||
            ACTIVITY_STATUS[r.status].label === filters.status)
      ),
    [rows, feed, filters]
  );

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const visible = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);
  const lifetimeTotal = summary[0].value;

  /* Export what is on screen, so the file matches what the user is looking at. */
  const exportCsv = () => {
    const head = ['Activity', 'Feed', 'Status', 'Type', 'Date', 'Time', 'Duration'];
    const body = filtered.map((r) => [
      r.label, r.feed, ACTIVITY_STATUS[r.status].label, r.type, r.date, r.time, r.duration,
    ]);
    const csv = [head, ...body]
      .map((cols) => cols.map((c) => (/[",]/.test(c) ? `"${c.replace(/"/g, '""')}"` : c)).join(','))
      .join('\n');

    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = `${connector.id}-activity.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (rows.length === 0) {
    return (
      <Card className="py-12 flex flex-col items-center text-center px-5">
        <div className="w-11 h-11 rounded-full bg-gray-50 dark:bg-slate-800 flex items-center justify-center mb-3.5 text-gray-400 dark:text-slate-500">
          <i className="fa-solid fa-clock-rotate-left text-[15px]" />
        </div>
        <p className="text-[13.5px] font-bold text-gray-800 dark:text-slate-200 mb-1">No activity yet</p>
        <p className="text-[12.5px] text-gray-500 dark:text-slate-400 max-w-[340px] leading-relaxed">
          {connector.name} has not synced yet. Activity appears here after the first run.
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">

      {/* ── Header ── */}
      <div>
        <h2 className="text-[16px] font-bold text-gray-900 dark:text-white">Activity</h2>
        <p className="text-[12px] text-gray-500 dark:text-slate-400 mt-0.5">
          View all syncs, updates, and events related to this integration.
        </p>
      </div>

      {/* ── Counters ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {summary.map((tile) => (
          <Card key={tile.key} className="px-4 py-3.5">
            <p className="text-[24px] font-bold text-gray-900 dark:text-white leading-none">
              {tile.value}
            </p>
            <p className="text-[12px] text-gray-500 dark:text-slate-400 mt-1.5">{tile.label}</p>
            {tile.delta ? (
              <p
                className={`text-[11px] mt-1.5 flex items-center gap-1 ${
                  tile.tone === 'rose'
                    ? 'text-rose-600 dark:text-rose-400'
                    : 'text-emerald-600 dark:text-emerald-400'
                }`}
              >
                <i className={`fa-solid fa-arrow-${tile.dir} text-[9px]`} />
                {tile.delta}
                <span className="text-gray-400 dark:text-slate-500 font-normal">vs last 7 days</span>
              </p>
            ) : (
              <p className="text-[11px] text-gray-400 dark:text-slate-500 mt-1.5">{tile.flat}</p>
            )}
          </Card>
        ))}
      </div>

      {/* ── Recent activity ── */}
      <Card className="p-4">
        <div className="flex items-center justify-between gap-3 mb-3.5">
          <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white">Recent activity</h3>
          <button className="text-[11.5px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 flex items-center gap-1.5">
            View all activity <i className="fa-solid fa-arrow-right text-[9px]" />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
          {rows.slice(0, 4).map((row) => {
            const s = ACTIVITY_STATUS[row.status];
            return (
              <div
                key={row.id}
                className="rounded-xl border border-gray-200 dark:border-slate-800 p-3"
              >
                <p className="text-[12.5px] font-bold text-gray-900 dark:text-white leading-snug flex items-start gap-2">
                  <i className={`fa-solid ${s.icon} text-[10px] mt-[3px] flex-shrink-0 ${s.iconTone}`} />
                  <span className="min-w-0">{row.label}</span>
                </p>
                <p className="text-[11px] text-gray-400 dark:text-slate-500 mt-1.5">{row.time}</p>
                <span className={`inline-block mt-2 px-2 py-0.5 rounded text-[10.5px] font-semibold ${s.chip}`}>
                  {s.cardChip}
                </span>
              </div>
            );
          })}
        </div>
      </Card>

      {/* ── Activity log ── */}
      <Card>
        <div className="p-4 flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white">Activity log</h3>
          <div className="flex items-center gap-2">
            <SelectMenu
              value={feed}
              options={feeds}
              onChange={(f) => { setFeed(f); setPage(1); }}
              size="sm"
              ariaLabel="Filter by feed"
              className="w-[140px] flex-shrink-0"
            />
            <button
              onClick={exportCsv}
              className="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[12px] font-semibold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-2 whitespace-nowrap"
            >
              Export <i className="fa-solid fa-download text-[10px]" />
            </button>
          </div>
        </div>

        <div className="overflow-x-auto custom-scrollbar">
          <table className="w-full min-w-[620px]">
            <thead>
              <tr className="border-y border-gray-100 dark:border-slate-800">
                {['Activity', 'Status', 'Type', 'Start time', 'Duration', ''].map((h, i) => (
                  <th
                    key={h || 'chevron'}
                    className={`px-4 py-2.5 text-[10.5px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider ${
                      i === 0 ? 'text-left' : i === 5 ? 'w-8' : 'text-left'
                    }`}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visible.map((row) => {
                const s = ACTIVITY_STATUS[row.status];
                return (
                  <tr
                    key={row.id}
                    className="border-b border-gray-100 dark:border-slate-800 last:border-0 hover:bg-gray-50/60 dark:hover:bg-slate-800/40 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <p className="text-[12.5px] font-semibold text-gray-900 dark:text-white leading-snug">
                        {row.label}
                      </p>
                      <p className="text-[11px] text-gray-400 dark:text-slate-500 mt-0.5">
                        Feed: {row.feed}
                      </p>
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1.5 whitespace-nowrap">
                        <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
                        <span className={`px-2 py-0.5 rounded text-[10.5px] font-semibold ${s.chip}`}>
                          {s.label}
                        </span>
                      </span>
                    </td>
                    <td className="px-4 py-3 text-[12px] text-gray-600 dark:text-slate-300">{row.type}</td>
                    <td className="px-4 py-3">
                      <p className="text-[12px] text-gray-600 dark:text-slate-300">{row.date}</p>
                      <p className="text-[11px] text-gray-400 dark:text-slate-500 mt-0.5">
                        <i className="fa-regular fa-clock text-[9px] mr-1" />
                        {row.time}
                      </p>
                    </td>
                    <td className="px-4 py-3 text-[12px] text-gray-600 dark:text-slate-300 whitespace-nowrap">
                      {row.duration}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        aria-label={`Open ${row.label}`}
                        className="text-gray-300 dark:text-slate-600 hover:text-gray-500 dark:hover:text-slate-400 transition-colors"
                      >
                        <i className="fa-solid fa-chevron-right text-[11px]" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* ── Pagination ── */}
        <div className="p-4 flex flex-wrap items-center justify-between gap-3 border-t border-gray-100 dark:border-slate-800">
          <p className="text-[12px] text-gray-500 dark:text-slate-400">
            Showing {filtered.length === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1} to{' '}
            {Math.min(currentPage * PAGE_SIZE, filtered.length)} of{' '}
            {lifetimeTotal.toLocaleString('en-US')} activities
          </p>

          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              aria-label="Previous page"
              className="w-7 h-7 rounded-lg border border-gray-200 dark:border-slate-700 text-gray-400 hover:text-gray-700 dark:hover:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center justify-center disabled:opacity-40"
            >
              <i className="fa-solid fa-chevron-left text-[9px]" />
            </button>

            {Array.from({ length: totalPages }, (_, i) => i + 1).map((n) => (
              <button
                key={n}
                onClick={() => setPage(n)}
                className={`w-7 h-7 rounded-lg text-[12px] font-semibold transition-colors ${
                  n === currentPage
                    ? 'border border-indigo-500 text-indigo-600 dark:text-indigo-400'
                    : 'text-gray-500 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-slate-800'
                }`}
              >
                {n}
              </button>
            ))}

            <button
              onClick={() => setPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              aria-label="Next page"
              className="w-7 h-7 rounded-lg border border-gray-200 dark:border-slate-700 text-gray-400 hover:text-gray-700 dark:hover:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center justify-center disabled:opacity-40"
            >
              <i className="fa-solid fa-chevron-right text-[9px]" />
            </button>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default ActivityTab;
