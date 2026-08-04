import React, { useMemo, useState } from 'react';
import {
  DATASET_STATUS,
  FEED_TAG_TONES,
  connectorDatasets,
  dataSummary,
} from '@/features/integrations/data/connectorDetailData';

const Card = ({ children, className = '' }) => (
  <div className={`bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl ${className}`}>
    {children}
  </div>
);

const iconButton =
  'w-7 h-7 rounded-lg border border-gray-200 dark:border-slate-700 text-gray-400 hover:text-gray-700 dark:hover:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center justify-center flex-shrink-0';

/** One CSV out of a row set, quoted so a comma inside a value cannot split it. */
const downloadCsv = (filename, head, body) => {
  const csv = [head, ...body]
    .map((cols) =>
      cols
        .map((c) => (/[",\n]/.test(String(c)) ? `"${String(c).replace(/"/g, '""')}"` : String(c)))
        .join(',')
    )
    .join('\n');

  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }));
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
};

const HEAD = ['Dataset', 'Feed', 'Records', 'Last updated', 'Status'];
const toRow = (d) => [d.name, d.feed, d.records, `${d.when} (${d.at})`, DATASET_STATUS[d.status].label];

/**
 * Every dataset one connector is syncing.
 *
 * Search lives here and Type / Status live in the rail, but all three narrow the
 * same list — so the count in the footer always describes the rows on screen.
 */
const DataTab = ({ connector, filters }) => {
  const rows = useMemo(() => connectorDatasets(connector), [connector]);
  const summary = useMemo(() => dataSummary(connector, rows), [connector, rows]);
  const totalRecords = useMemo(() => rows.reduce((sum, r) => sum + r.records, 0), [rows]);

  const [query, setQuery] = useState('');
  /* Which row has its detail strip open. One at a time: two open strips push the
     rows being compared further apart, which is the opposite of the point. */
  const [expanded, setExpanded] = useState(null);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return rows.filter(
      (r) =>
        (!q || r.name.toLowerCase().includes(q) || r.feed.toLowerCase().includes(q)) &&
        (!filters?.type || filters.type === 'All types' || r.feed === filters.type) &&
        (!filters?.status ||
          filters.status === 'All status' ||
          DATASET_STATUS[r.status].label === filters.status)
    );
  }, [rows, query, filters]);

  if (rows.length === 0) {
    return (
      <Card className="py-12 flex flex-col items-center text-center px-5">
        <div className="w-11 h-11 rounded-full bg-gray-50 dark:bg-slate-800 flex items-center justify-center mb-3.5 text-gray-400 dark:text-slate-500">
          <i className="fa-solid fa-database text-[15px]" />
        </div>
        <p className="text-[13.5px] font-bold text-gray-800 dark:text-slate-200 mb-1">No datasets yet</p>
        <p className="text-[12.5px] text-gray-500 dark:text-slate-400 max-w-[340px] leading-relaxed">
          {connector.name} has not synced any data yet. Datasets appear here after the first run.
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">

      {/* ── Header ── */}
      <div>
        <h2 className="text-[16px] font-bold text-gray-900 dark:text-white">Data</h2>
        <p className="text-[12px] text-gray-500 dark:text-slate-400 mt-0.5">
          Explore, preview, and validate the data being synced from {connector.name}.
        </p>
      </div>

      {/* ── Tiles ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {summary.map((tile) => (
          <Card key={tile.key} className="px-4 py-3.5">
            <p className="text-[12px] text-gray-500 dark:text-slate-400">{tile.label}</p>
            <p className="text-[21px] font-bold text-gray-900 dark:text-white leading-tight mt-1 truncate">
              {tile.value}
            </p>
            <p className="text-[11px] text-gray-400 dark:text-slate-500 mt-1">{tile.sub}</p>
          </Card>
        ))}
      </div>

      {/* ── Datasets ── */}
      <Card className="overflow-hidden">
        <div className="px-4 py-3 flex flex-col lg:flex-row lg:items-center justify-between gap-3 border-b border-gray-100 dark:border-slate-800">
          <h3 className="text-[14px] font-bold text-gray-900 dark:text-white flex-shrink-0">Datasets</h3>

          <div className="flex items-center gap-2 flex-wrap">
            <div className="relative flex-1 min-w-[180px]">
              <i className="fa-solid fa-magnifying-glass text-[11px] text-gray-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search datasets..."
                aria-label="Search datasets"
                className="w-full bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl pl-8 pr-3 py-1.5 text-[12.5px] text-gray-800 dark:text-slate-200 placeholder:text-gray-400 dark:placeholder:text-slate-500 outline-none focus:border-indigo-400 transition-colors"
              />
            </div>

            <div className="rounded-xl border border-gray-200 dark:border-slate-700 px-3 py-1.5 flex items-center gap-2 flex-shrink-0">
              <i className="fa-regular fa-calendar text-[11px] text-gray-400 dark:text-slate-500" />
              <span className="text-[12.5px] font-medium text-gray-800 dark:text-slate-200 whitespace-nowrap">
                May 6, 2025 – May 12, 2025
              </span>
            </div>

            <button
              onClick={() => downloadCsv(`${connector.id}-datasets.csv`, HEAD, filtered.map(toRow))}
              aria-label="Download dataset list"
              className={iconButton}
            >
              <i className="fa-solid fa-download text-[11px]" />
            </button>
          </div>
        </div>

        {/* Header row and body share one grid template so the columns line up
            without a <table>'s fixed-layout constraints. */}
        <div className="hidden sm:grid grid-cols-[minmax(0,1.4fr)_90px_minmax(0,0.8fr)_minmax(0,1.1fr)_100px_74px] gap-3 px-4 py-2 bg-gray-50/70 dark:bg-slate-800/40 border-b border-gray-100 dark:border-slate-800">
          {['Dataset', 'Feed', 'Records', 'Last updated', 'Status', 'Actions'].map((h, i) => (
            <p
              key={h}
              className={`text-[10.5px] font-bold text-gray-500 dark:text-slate-400 uppercase tracking-wider ${
                i === 5 ? 'text-right' : ''
              }`}
            >
              {h}
            </p>
          ))}
        </div>

        {filtered.map((d) => {
          const status = DATASET_STATUS[d.status];
          const isOpen = expanded === d.key;
          return (
            <div key={d.key} className="border-b border-gray-100 dark:border-slate-800 last:border-0">
              <div className="grid grid-cols-1 sm:grid-cols-[minmax(0,1.4fr)_90px_minmax(0,0.8fr)_minmax(0,1.1fr)_100px_74px] gap-2 sm:gap-3 px-4 py-3 items-center">
                <p className="text-[12.5px] font-semibold text-gray-900 dark:text-white truncate">
                  {d.name}
                </p>

                <span
                  className={`px-2 py-0.5 rounded text-[10.5px] font-semibold justify-self-start whitespace-nowrap ${
                    FEED_TAG_TONES[d.feed] || FEED_TAG_TONES.Catalog
                  }`}
                >
                  {d.feed}
                </span>

                <p className="text-[12.5px] text-gray-600 dark:text-slate-300 tabular-nums">
                  {d.records.toLocaleString('en-US')}
                </p>

                <div className="min-w-0">
                  <p className="text-[12.5px] text-gray-800 dark:text-slate-200 leading-snug">{d.when}</p>
                  <p className="text-[11px] text-gray-400 dark:text-slate-500 leading-snug">{d.at}</p>
                </div>

                <p className={`text-[12px] font-semibold flex items-center gap-1.5 ${status.text}`}>
                  <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${status.dot}`} />
                  {status.label}
                </p>

                <div className="flex items-center gap-1.5 sm:justify-end">
                  <button
                    onClick={() => downloadCsv(`${connector.id}-${d.key.toLowerCase().replace(/\s+/g, '-')}.csv`, HEAD, [toRow(d)])}
                    aria-label={`Download ${d.name}`}
                    className={iconButton}
                  >
                    <i className="fa-solid fa-download text-[10px]" />
                  </button>
                  <button
                    onClick={() => setExpanded(isOpen ? null : d.key)}
                    aria-label={`${isOpen ? 'Hide' : 'Preview'} ${d.name}`}
                    aria-expanded={isOpen}
                    className={`${iconButton} ${isOpen ? 'bg-gray-50 dark:bg-slate-800 text-gray-700 dark:text-slate-200' : ''}`}
                  >
                    <i className={`fa-solid ${isOpen ? 'fa-eye-slash' : 'fa-eye'} text-[10px]`} />
                  </button>
                </div>
              </div>

              {/* Preview strip — only the facts we actually hold for this dataset,
                  so nothing here is invented to fill a panel. */}
              {isOpen && (
                <div className="px-4 pb-3.5 -mt-0.5">
                  <div className="rounded-xl bg-gray-50/70 dark:bg-slate-800/40 border border-gray-100 dark:border-slate-800 px-3.5 py-3 grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {[
                      { label: 'Records', value: d.records.toLocaleString('en-US') },
                      {
                        label: 'Share of synced rows',
                        value: totalRecords ? `${((d.records / totalRecords) * 100).toFixed(1)}%` : '—',
                      },
                      { label: 'Last updated', value: d.at },
                      { label: 'Status', value: status.label },
                    ].map((f) => (
                      <div key={f.label} className="min-w-0">
                        <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider">
                          {f.label}
                        </p>
                        <p className="text-[12px] font-semibold text-gray-800 dark:text-slate-200 mt-0.5 truncate">
                          {f.value}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {filtered.length === 0 && (
          <div className="px-4 py-10 text-center">
            <p className="text-[12.5px] text-gray-500 dark:text-slate-400">
              No datasets match {query ? `“${query.trim()}”` : 'these filters'}.
            </p>
          </div>
        )}

        <div className="px-4 py-3 border-t border-gray-100 dark:border-slate-800">
          <p className="text-[12px] text-gray-500 dark:text-slate-400">
            {filtered.length === 0
              ? `Showing 0 of ${rows.length} datasets`
              : `Showing 1 to ${filtered.length} of ${rows.length} datasets`}
          </p>
        </div>
      </Card>
    </div>
  );
};

export default DataTab;
