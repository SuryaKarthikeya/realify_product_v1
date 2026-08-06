import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  DATASET_STATUS,
  FEED_TAG_TONES,
  connectorDatasets,
  dataSummary,
} from '@/features/integrations/data/connectorDetailData';
import { datasetSlug } from '@/features/integrations/data/datasetDetailData';
import { ROUTES } from '@/constants/routes';

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
 * Selecting a row previews it in the rail beside the table; the eye icon opens
 * that dataset's own screen, where the record rows live. Selection is owned by
 * the page rather than by this table, so the rail can never preview a different
 * dataset from the one the table has highlighted.
 */
const DataTab = ({ connector, selectedKey, onSelect }) => {
  const navigate = useNavigate();
  const rows = useMemo(() => connectorDatasets(connector), [connector]);
  const summary = useMemo(() => dataSummary(connector, rows), [connector, rows]);

  const [query, setQuery] = useState('');

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter(
      (r) => r.name.toLowerCase().includes(q) || r.feed.toLowerCase().includes(q)
    );
  }, [rows, query]);

  const openDataset = (dataset) =>
    navigate(
      ROUTES.DATASET_DETAIL
        .replace(':connectorId', connector.id)
        .replace(':datasetId', datasetSlug(dataset.name))
    );

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
          const isSelected = d.key === selectedKey;
          return (
            <div
              key={d.key}
              onClick={() => onSelect(d.key)}
              className={`border-b border-gray-100 dark:border-slate-800 last:border-0 cursor-pointer transition-colors ${
                isSelected
                  ? 'bg-indigo-50/50 dark:bg-indigo-950/20'
                  : 'hover:bg-gray-50/70 dark:hover:bg-slate-800/40'
              }`}
            >
              <div className="grid grid-cols-1 sm:grid-cols-[minmax(0,1.4fr)_90px_minmax(0,0.8fr)_minmax(0,1.1fr)_100px_74px] gap-2 sm:gap-3 px-4 py-3 items-center relative">
                {/* Marks the previewed row without moving anything: a left rule
                    rather than a border that would shift the row by a pixel. */}
                {isSelected && (
                  <span className="absolute left-0 top-0 bottom-0 w-[2.5px] bg-indigo-500 dark:bg-indigo-400" />
                )}

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
                    onClick={(e) => {
                      e.stopPropagation();
                      downloadCsv(`${connector.id}-${datasetSlug(d.name)}.csv`, HEAD, [toRow(d)]);
                    }}
                    aria-label={`Download ${d.name}`}
                    className={iconButton}
                  >
                    <i className="fa-solid fa-download text-[10px]" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      openDataset(d);
                    }}
                    aria-label={`Open ${d.name}`}
                    className={iconButton}
                  >
                    <i className="fa-solid fa-eye text-[10px]" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}

        {filtered.length === 0 && (
          <div className="px-4 py-10 text-center">
            <p className="text-[12.5px] text-gray-500 dark:text-slate-400">
              No datasets match “{query.trim()}”.
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
