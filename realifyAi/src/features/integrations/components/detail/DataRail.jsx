import React, { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { DATASET_STATUS } from '@/features/integrations/data/connectorDetailData';
import { datasetDetail, datasetSlug } from '@/features/integrations/data/datasetDetailData';
import { ROUTES } from '@/constants/routes';

const Card = ({ children, className = '' }) => (
  <div className={`bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl ${className}`}>
    {children}
  </div>
);

/** One label/value line in the info cards. */
const Row = ({ label, value }) => (
  <div className="flex items-start justify-between gap-3">
    <span className="text-[11.5px] text-gray-500 dark:text-slate-400 flex-shrink-0">{label}</span>
    <span className="text-[11.5px] font-semibold text-gray-900 dark:text-white text-right min-w-0 break-words">
      {value}
    </span>
  </div>
);

const linkButton =
  'text-[11.5px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 flex items-center gap-1.5';

/** How many schema chips fit before the rail starts to feel like a list. */
const CHIP_LIMIT = 5;

/**
 * The rail beside Data — a preview of whichever dataset is selected in the table.
 *
 * The table always has a selection (the first row by default), so this rail is
 * never empty: opening the tab already answers "what is in this feed" without a
 * click. The full screen behind the eye icon is the same data with the record
 * rows attached.
 */
const DataRail = ({ connector, dataset }) => {
  const navigate = useNavigate();
  const detail = useMemo(() => datasetDetail(connector, dataset), [connector, dataset]);

  if (!detail) {
    return (
      <Card className="py-10 px-5 flex flex-col items-center text-center">
        <div className="w-10 h-10 rounded-full bg-gray-50 dark:bg-slate-800 flex items-center justify-center mb-3 text-gray-400 dark:text-slate-500">
          <i className="fa-solid fa-file-lines text-[14px]" />
        </div>
        <p className="text-[12.5px] text-gray-500 dark:text-slate-400">
          Select a dataset to preview it.
        </p>
      </Card>
    );
  }

  const status = DATASET_STATUS[detail.status];
  const openDataset = () =>
    navigate(
      ROUTES.DATASET_DETAIL
        .replace(':connectorId', connector.id)
        .replace(':datasetId', datasetSlug(detail.name))
    );

  const hiddenChips = detail.fields.length - CHIP_LIMIT;

  return (
    <Card className="p-4 space-y-4">

      {/* ── Identity ── */}
      <div className="flex items-start gap-3">
        <span className="w-9 h-9 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 flex items-center justify-center flex-shrink-0">
          <i className="fa-solid fa-file-lines text-[14px]" />
        </span>
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-[15px] font-bold text-gray-900 dark:text-white truncate">{detail.name}</h3>
            <span className={`text-[11px] font-semibold flex items-center gap-1.5 ${status.text}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${status.dot}`} />
              {status.label}
            </span>
          </div>
          <p className="text-[11.5px] text-gray-500 dark:text-slate-400 mt-0.5">
            Feed: {detail.feed}
            <span className="mx-1.5 text-gray-300 dark:text-slate-600">•</span>
            Records: {detail.records.toLocaleString('en-US')}
          </p>
          <p className="text-[11px] text-gray-400 dark:text-slate-500 mt-0.5">
            Last updated: {detail.at}
          </p>
        </div>
      </div>

      {/* ── Actions ── */}
      <div className="flex items-center gap-2">
        <button className="px-3 py-1.5 rounded-xl border border-gray-200 dark:border-slate-700 text-[12px] font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-2">
          <i className="fa-solid fa-download text-[10px]" /> Download
        </button>
        <button className="px-3 py-1.5 rounded-xl border border-gray-200 dark:border-slate-700 text-[12px] font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-2">
          <i className="fa-solid fa-rotate text-[10px]" /> Refresh
        </button>
        <button
          onClick={openDataset}
          aria-label={`Open ${detail.name}`}
          className="w-8 h-8 rounded-xl border border-gray-200 dark:border-slate-700 text-gray-400 hover:text-gray-700 dark:hover:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center justify-center flex-shrink-0"
        >
          <i className="fa-solid fa-ellipsis text-[11px]" />
        </button>
      </div>

      {/* ── Stat tiles ── */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-2">
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
            dot: status.dot,
            valueClass: status.text,
          },
        ].map((tile) => (
          <div
            key={tile.label}
            className="rounded-xl border border-gray-200 dark:border-slate-800 px-2.5 py-2 min-w-0"
          >
            <p className="text-[10px] text-gray-500 dark:text-slate-400 leading-tight">{tile.label}</p>
            <p className={`text-[12.5px] font-bold leading-snug mt-0.5 ${tile.valueClass || 'text-gray-900 dark:text-white'}`}>
              {tile.value}
            </p>
            <p className="text-[9.5px] text-gray-400 dark:text-slate-500 mt-0.5 flex items-center gap-1 leading-tight">
              {tile.dot && <span className={`w-1 h-1 rounded-full flex-shrink-0 ${tile.dot}`} />}
              {tile.sub}
            </p>
          </div>
        ))}
      </div>

      {/* ── Dataset info + Fields ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <div className="rounded-xl border border-gray-200 dark:border-slate-800 p-3">
          <h4 className="text-[12.5px] font-bold text-gray-900 dark:text-white mb-2.5">Dataset info</h4>
          <div className="space-y-2">
            <Row label="Owner" value={detail.owner} />
            <Row label="Created on" value={detail.createdOn} />
            <Row label="Last updated" value={detail.at.split(',').slice(0, 2).join(',')} />
          </div>
          <button onClick={openDataset} className={`${linkButton} mt-2.5`}>
            View details <i className="fa-solid fa-arrow-right text-[9px]" />
          </button>
        </div>

        <div className="rounded-xl border border-gray-200 dark:border-slate-800 p-3">
          <div className="flex items-center justify-between gap-2 mb-2.5">
            <h4 className="text-[12.5px] font-bold text-gray-900 dark:text-white">
              Fields ({detail.fields.length})
            </h4>
            <button
              onClick={openDataset}
              className="px-2 py-1 rounded-lg border border-gray-200 dark:border-slate-700 text-[10.5px] font-semibold text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
            >
              View schema
            </button>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {detail.fields.slice(0, CHIP_LIMIT).map((field) => (
              <span
                key={field}
                className="px-2 py-0.5 rounded-md bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 text-[10.5px] text-gray-600 dark:text-slate-300 whitespace-nowrap"
              >
                {field}
              </span>
            ))}
          </div>
          {hiddenChips > 0 && (
            <button onClick={openDataset} className={`${linkButton} mt-2.5`}>
              + {hiddenChips} more field{hiddenChips === 1 ? '' : 's'}
            </button>
          )}
        </div>
      </div>

      {/* ── Sync information + Help ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <div className="rounded-xl border border-gray-200 dark:border-slate-800 p-3">
          <h4 className="text-[12.5px] font-bold text-gray-900 dark:text-white mb-2.5">Sync information</h4>
          <div className="space-y-2">
            <Row label="Feed" value={detail.feed} />
            <Row label="Connector" value={detail.connectorName} />
            <Row label="Next sync" value={detail.nextSync} />
            <Row label="Records processed" value={detail.records.toLocaleString('en-US')} />
          </div>
          <button className={`${linkButton} mt-2.5`}>
            View sync history <i className="fa-solid fa-arrow-right text-[9px]" />
          </button>
        </div>

        <div className="rounded-xl border border-gray-200 dark:border-slate-800 p-3">
          <h4 className="text-[12.5px] font-bold text-gray-900 dark:text-white mb-2.5">Need help?</h4>
          <div className="space-y-2.5">
            {[
              { icon: 'fa-book', label: 'View integration guide' },
              { icon: 'fa-comment-dots', label: 'Contact support' },
            ].map((link) => (
              <button
                key={link.label}
                className="w-full flex items-center gap-2 text-[11.5px] text-gray-600 dark:text-slate-300 hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                <i className={`fa-solid ${link.icon} text-[10px] text-gray-400 dark:text-slate-500 flex-shrink-0`} />
                <span className="truncate">{link.label}</span>
                <i className="fa-solid fa-arrow-up-right-from-square text-[8px] ml-auto opacity-50 flex-shrink-0" />
              </button>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
};

export default DataRail;
