import React, { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import DashboardLayout from '@/layouts/DashboardLayout';
import { CONNECTORS } from '@/features/integrations/data/integrationsData';
import {
  DATASET_STATUS,
  connectorDatasets,
} from '@/features/integrations/data/connectorDetailData';
import {
  RECORDS_PAGE_SIZE,
  RECORD_STATUS_TONES,
  datasetDetail,
  datasetSlug,
} from '@/features/integrations/data/datasetDetailData';
import { ROUTES } from '@/constants/routes';

const Card = ({ children, className = '' }) => (
  <div className={`bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl ${className}`}>
    {children}
  </div>
);

const Row = ({ label, value }) => (
  <div className="flex items-start justify-between gap-3">
    <span className="text-[12px] text-gray-500 dark:text-slate-400 flex-shrink-0">{label}</span>
    <span className="text-[12px] font-semibold text-gray-900 dark:text-white text-right min-w-0 break-words">
      {value}
    </span>
  </div>
);

const linkButton =
  'text-[12px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 flex items-center gap-1.5';

/** How many schema chips show before the rest are folded away. */
const CHIP_LIMIT = 6;

/** The quality ring — an SVG arc, so the number and the sweep cannot disagree. */
const QualityDial = ({ percent }) => {
  const radius = 46;
  const circumference = 2 * Math.PI * radius;
  return (
    <div className="relative w-[120px] h-[120px] flex-shrink-0">
      <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
        <circle cx="60" cy="60" r={radius} fill="none" strokeWidth="9" className="stroke-gray-100 dark:stroke-slate-800" />
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          strokeWidth="9"
          strokeLinecap="round"
          className="stroke-emerald-500"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - percent / 100)}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-[20px] font-bold text-gray-900 dark:text-white leading-none">{percent}%</span>
        <span className="text-[10.5px] text-gray-400 dark:text-slate-500 mt-1">Valid</span>
      </div>
    </div>
  );
};

/**
 * One dataset, in full — the screen the eye icon in the Datasets table opens.
 *
 * The record table's columns come from the dataset itself, so a Sales Orders
 * preview shows buyers and amounts while an Inventory preview shows warehouses
 * and on-hand counts. Everything here is demo data (see datasetDetailData.js).
 */
const DatasetDetailPage = () => {
  const { connectorId, datasetId } = useParams();
  const navigate = useNavigate();

  const connector = CONNECTORS.find((c) => c.id === connectorId);
  const dataset = useMemo(
    () => connectorDatasets(connector).find((d) => datasetSlug(d.name) === datasetId),
    [connector, datasetId]
  );
  const detail = useMemo(() => datasetDetail(connector, dataset), [connector, dataset]);

  const [page, setPage] = useState(1);
  const [showAllFields, setShowAllFields] = useState(false);

  const backToDatasets = () =>
    navigate(`${ROUTES.CONNECTOR_DETAIL.replace(':connectorId', connectorId)}?tab=Data`);

  if (!connector || !detail) {
    return (
      <DashboardLayout showTabs={false} showAIPrompt={false}>
        <div className="max-w-[900px] mx-auto px-5 py-12 flex flex-col items-center text-center">
          <div className="w-11 h-11 rounded-full bg-gray-50 dark:bg-slate-800 flex items-center justify-center mb-3.5 text-gray-400 dark:text-slate-500">
            <i className="fa-solid fa-file-circle-xmark text-[15px]" />
          </div>
          <p className="text-[14px] font-bold text-gray-800 dark:text-slate-200 mb-1">No such dataset</p>
          <p className="text-[12.5px] text-gray-500 dark:text-slate-400 mb-5">
            <span className="font-mono">{datasetId}</span> is not a dataset on this connector.
          </p>
          <button
            onClick={() => navigate(ROUTES.INTEGRATIONS)}
            className="px-4 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[13px] font-bold text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-950/30 transition-colors"
          >
            Back to Integrations
          </button>
        </div>
      </DashboardLayout>
    );
  }

  const status = DATASET_STATUS[detail.status];
  const totalPages = Math.max(1, Math.ceil(detail.rows.length / RECORDS_PAGE_SIZE));
  const pageRows = detail.rows.slice((page - 1) * RECORDS_PAGE_SIZE, page * RECORDS_PAGE_SIZE);
  const firstOnPage = (page - 1) * RECORDS_PAGE_SIZE + 1;
  const visibleFields = showAllFields ? detail.fields : detail.fields.slice(0, CHIP_LIMIT);

  return (
    <DashboardLayout showTabs={false} showAIPrompt={false}>
      <div className="max-w-[1600px] mx-auto px-3 sm:px-4 py-3 font-sans">

        <button
          onClick={backToDatasets}
          className="text-[12.5px] font-semibold text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-200 transition-colors flex items-center gap-2 mb-4"
        >
          <i className="fa-solid fa-arrow-left text-[10px]" /> Back to Datasets
        </button>

        {/* ── Identity ── */}
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          <div className="flex items-start gap-3.5 min-w-0">
            <span className="w-11 h-11 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 flex items-center justify-center flex-shrink-0">
              <i className="fa-solid fa-file-lines text-[17px]" />
            </span>

            <div className="min-w-0">
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="text-[19px] font-bold text-gray-900 dark:text-white tracking-tight">
                  {detail.name}
                </h1>
                <span className={`text-[11.5px] font-semibold flex items-center gap-1.5 ${status.text}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${status.dot}`} />
                  {status.label}
                </span>
              </div>
              <p className="text-[12px] text-gray-500 dark:text-slate-400 mt-1">
                Feed: {detail.feed}
                <span className="mx-1.5 text-gray-300 dark:text-slate-600">•</span>
                Records: {detail.records.toLocaleString('en-US')}
                <span className="mx-1.5 text-gray-300 dark:text-slate-600">•</span>
                Updated: {detail.at}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0 flex-wrap">
            <button className="px-3.5 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[12.5px] font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-2 whitespace-nowrap">
              <i className="fa-solid fa-download text-[11px]" /> Download
            </button>
            <button className="px-3.5 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[12.5px] font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-2 whitespace-nowrap">
              <i className="fa-solid fa-rotate text-[11px]" /> Refresh
            </button>
            <button
              aria-label="More options"
              className="w-9 h-9 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-400 hover:text-gray-600 dark:hover:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center justify-center flex-shrink-0"
            >
              <i className="fa-solid fa-ellipsis text-[12px]" />
            </button>
          </div>
        </div>

        {/* ── Content + rail ── */}
        <div className="flex flex-col xl:flex-row gap-4 items-start mt-4">
          <div className="min-w-0 w-full xl:flex-[9] space-y-4">

            {/* Tiles */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {[
                { label: 'Total records', value: detail.records.toLocaleString('en-US'), sub: 'All time' },
                { label: 'Last synced', value: detail.when, sub: detail.at },
                {
                  label: 'Sync frequency',
                  value: detail.syncFrequency,
                  sub: detail.autoSync ? 'Auto sync is on' : 'Manual only',
                  dot: 'bg-indigo-500',
                },
                {
                  label: 'Status',
                  value: status.label,
                  sub: detail.status === 'healthy' ? 'No issues detected' : 'Needs attention',
                  valueClass: status.text,
                },
              ].map((tile) => (
                <Card key={tile.label} className="px-4 py-3.5 min-w-0">
                  <p className="text-[12px] text-gray-500 dark:text-slate-400">{tile.label}</p>
                  <p className={`text-[19px] font-bold leading-tight mt-1 truncate ${tile.valueClass || 'text-gray-900 dark:text-white'}`}>
                    {tile.value}
                  </p>
                  <p className="text-[11px] text-gray-400 dark:text-slate-500 mt-1 flex items-center gap-1.5 truncate">
                    {tile.dot && <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${tile.dot}`} />}
                    {tile.sub}
                  </p>
                </Card>
              ))}
            </div>

            {/* Recent records */}
            <Card className="overflow-hidden">
              <div className="px-4 py-3 flex items-center justify-between gap-3 border-b border-gray-100 dark:border-slate-800">
                <h3 className="text-[14px] font-bold text-gray-900 dark:text-white">Recent records</h3>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full min-w-[640px]">
                  <thead>
                    <tr className="bg-gray-50/70 dark:bg-slate-800/40 border-b border-gray-100 dark:border-slate-800">
                      {detail.columns.map((c) => (
                        <th
                          key={c.key}
                          className={`px-4 py-2 text-[10.5px] font-bold text-gray-500 dark:text-slate-400 uppercase tracking-wider whitespace-nowrap ${
                            c.align === 'right' ? 'text-right' : 'text-left'
                          }`}
                        >
                          {c.label}
                        </th>
                      ))}
                      <th className="px-4 py-2 w-10" />
                    </tr>
                  </thead>
                  <tbody>
                    {pageRows.map((record, i) => (
                      <tr
                        key={`${page}-${i}`}
                        className="border-b border-gray-100 dark:border-slate-800 last:border-0 hover:bg-gray-50/70 dark:hover:bg-slate-800/40 transition-colors"
                      >
                        {detail.columns.map((c) => (
                          <td
                            key={c.key}
                            className={`px-4 py-3 text-[12.5px] whitespace-nowrap ${
                              c.align === 'right'
                                ? 'text-right tabular-nums text-gray-800 dark:text-slate-200'
                                : 'text-left text-gray-700 dark:text-slate-300'
                            }`}
                          >
                            {c.type === 'status' ? (
                              <span
                                className={`px-2 py-0.5 rounded text-[10.5px] font-semibold ${
                                  RECORD_STATUS_TONES[record[c.key]] ||
                                  'bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-slate-300'
                                }`}
                              >
                                {record[c.key]}
                              </span>
                            ) : (
                              record[c.key]
                            )}
                          </td>
                        ))}
                        <td className="px-4 py-3 text-right">
                          <i className="fa-solid fa-chevron-right text-[10px] text-gray-300 dark:text-slate-600" />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="px-4 py-3 border-t border-gray-100 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <p className="text-[12px] text-gray-500 dark:text-slate-400">
                  Showing {firstOnPage} to {firstOnPage + pageRows.length - 1} of{' '}
                  {detail.records.toLocaleString('en-US')} records
                </p>

                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    aria-label="Previous page"
                    className="w-7 h-7 rounded-lg border border-gray-200 dark:border-slate-700 text-gray-400 hover:text-gray-700 dark:hover:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center justify-center disabled:opacity-40 disabled:hover:bg-transparent"
                  >
                    <i className="fa-solid fa-chevron-left text-[10px]" />
                  </button>

                  {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                    <button
                      key={p}
                      onClick={() => setPage(p)}
                      aria-current={p === page ? 'page' : undefined}
                      className={`w-7 h-7 rounded-lg text-[11.5px] font-semibold transition-colors ${
                        p === page
                          ? 'border border-indigo-500 text-indigo-600 dark:text-indigo-400 bg-indigo-50/60 dark:bg-indigo-950/30'
                          : 'border border-gray-200 dark:border-slate-700 text-gray-500 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-slate-800'
                      }`}
                    >
                      {p}
                    </button>
                  ))}

                  {/* The dataset holds far more rows than the preview loads —
                      the gap is stated rather than drawn as pages that lead
                      nowhere. */}
                  <span className="px-1 text-[11.5px] text-gray-400 dark:text-slate-500">…</span>

                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    aria-label="Next page"
                    className="w-7 h-7 rounded-lg border border-gray-200 dark:border-slate-700 text-gray-400 hover:text-gray-700 dark:hover:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center justify-center disabled:opacity-40 disabled:hover:bg-transparent"
                  >
                    <i className="fa-solid fa-chevron-right text-[10px]" />
                  </button>
                </div>
              </div>
            </Card>
          </div>

          {/* ── Rail ── */}
          <div className="w-full xl:w-auto xl:flex-[5] min-w-0 space-y-4">

            <Card className="p-4">
              <h3 className="text-[14px] font-bold text-gray-900 dark:text-white mb-3">Data quality</h3>

              <div className="flex justify-center py-1">
                <QualityDial percent={detail.quality.quality} />
              </div>

              <div className="mt-4 space-y-2.5">
                {[
                  {
                    label: 'Valid records',
                    value: `${detail.quality.valid.toLocaleString('en-US')} (${detail.quality.quality}%)`,
                    dot: 'bg-emerald-500',
                  },
                  {
                    label: 'Invalid records',
                    value: `${detail.quality.invalid.toLocaleString('en-US')} (${detail.quality.invalidPct}%)`,
                    dot: 'bg-rose-500',
                  },
                ].map((row) => (
                  <div key={row.label} className="flex items-center justify-between gap-3">
                    <span className="flex items-center gap-2 min-w-0 text-[12px] text-gray-600 dark:text-slate-300">
                      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${row.dot}`} />
                      <span className="truncate">{row.label}</span>
                    </span>
                    <span className="text-[12px] font-semibold text-gray-900 dark:text-white whitespace-nowrap">
                      {row.value}
                    </span>
                  </div>
                ))}
              </div>

              <button className={`${linkButton} mt-3`}>
                View validation results <i className="fa-solid fa-arrow-right text-[9px]" />
              </button>
            </Card>

            <Card className="p-4">
              <h3 className="text-[14px] font-bold text-gray-900 dark:text-white mb-3">Sync information</h3>
              <div className="space-y-2.5">
                <Row label="Feed" value={detail.feed} />
                <Row label="Connector" value={detail.connectorName} />
                <Row label="Next sync" value={detail.nextSync} />
                <Row label="Records processed" value={detail.records.toLocaleString('en-US')} />
              </div>
              <button className={`${linkButton} mt-3`}>
                View sync history <i className="fa-solid fa-arrow-right text-[9px]" />
              </button>
            </Card>

            <Card className="p-4">
              <h3 className="text-[14px] font-bold text-gray-900 dark:text-white mb-3">Dataset info</h3>
              <div className="space-y-2.5">
                <Row label="Owner" value={detail.owner} />
                <Row label="Created on" value={detail.createdOn} />
                <Row label="Last updated" value={detail.at.split(',').slice(0, 2).join(',')} />
              </div>
              <button onClick={backToDatasets} className={`${linkButton} mt-3`}>
                View details <i className="fa-solid fa-arrow-right text-[9px]" />
              </button>
            </Card>

            <Card className="p-4 bg-emerald-50/40 dark:bg-emerald-950/10 border-emerald-100 dark:border-emerald-900/40">
              <h3 className="text-[14px] font-bold text-gray-900 dark:text-white mb-3">Need help?</h3>
              <div className="space-y-2.5">
                {[
                  { icon: 'fa-book', label: 'View integration guide' },
                  { icon: 'fa-comment-dots', label: 'Contact support' },
                ].map((link) => (
                  <button
                    key={link.label}
                    className="w-full flex items-center gap-2.5 text-[12px] text-gray-600 dark:text-slate-300 hover:text-gray-900 dark:hover:text-white transition-colors"
                  >
                    <i className={`fa-solid ${link.icon} text-[11px] text-gray-400 dark:text-slate-500 flex-shrink-0`} />
                    <span className="truncate">{link.label}</span>
                    <i className="fa-solid fa-arrow-up-right-from-square text-[9px] ml-auto opacity-50 flex-shrink-0" />
                  </button>
                ))}
              </div>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default DatasetDetailPage;
