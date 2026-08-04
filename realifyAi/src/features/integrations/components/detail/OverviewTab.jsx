import React, { useState } from 'react';
import SelectMenu from '@/components/ui/SelectMenu';
import {
  FEED_TAG_TONES,
  SYNC_DAYS,
  SYNC_METRICS,
  connectorOverview,
  syncSeries,
} from '@/features/integrations/data/connectorDetailData';

const STAT_TONES = {
  emerald: 'text-emerald-600 dark:text-emerald-400',
  amber: 'text-amber-600 dark:text-amber-400',
  muted: 'text-gray-400 dark:text-slate-500',
};

/**
 * Sync-activity line chart.
 *
 * An inline SVG rather than a charting library: it is one polyline over a fixed
 * grid, so pulling in a dependency would cost bundle size for nothing.
 */
const SyncChart = ({ series }) => {
  const max = 100;
  const points = series
    .map((v, i) => {
      const x = (i / (series.length - 1)) * 100;
      const y = 100 - (v / max) * 100;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(' ');

  return (
    <div className="flex gap-3">
      {/* Y axis */}
      <div className="flex flex-col justify-between text-[10px] text-gray-400 dark:text-slate-500 h-[190px] py-[2px] flex-shrink-0">
        {[100, 75, 50, 25, 0].map((t) => (
          <span key={t}>{t}%</span>
        ))}
      </div>

      <div className="flex-1 min-w-0">
        <div className="relative h-[190px]">
          {/* Gridlines at each labelled tick */}
          {[0, 25, 50, 75, 100].map((t) => (
            <div
              key={t}
              className="absolute left-0 right-0 border-t border-gray-100 dark:border-slate-800"
              style={{ top: `${100 - t}%` }}
            />
          ))}

          <svg
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            className="absolute inset-0 w-full h-full"
            aria-hidden="true"
          >
            <polyline
              points={points}
              fill="none"
              stroke="#6366f1"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
              vectorEffect="non-scaling-stroke"
            />
          </svg>
        </div>

        {/* X axis */}
        <div className="flex justify-between text-[10px] text-gray-400 dark:text-slate-500 mt-2">
          {SYNC_DAYS.map((d) => (
            <span key={d}>{d}</span>
          ))}
        </div>
      </div>
    </div>
  );
};

const Card = ({ children, className = '' }) => (
  <div className={`bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl ${className}`}>
    {children}
  </div>
);

/** The Overview tab: connection health, the feeds it supplies, usage and trend. */
const OverviewTab = ({ connector }) => {
  const [metric, setMetric] = useState(SYNC_METRICS[0]);
  const overview = connectorOverview(connector);
  if (!overview) return null;

  const { stats, feeds, feedsSummary, usage } = overview;

  return (
    <div className="space-y-4">

      {/* ── Stat strip ── */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {stats.map((stat) => (
          <Card key={stat.key} className="px-3.5 py-3">
            <p className="text-[11.5px] text-gray-500 dark:text-slate-400 leading-snug">{stat.label}</p>

            <p
              className={`font-bold leading-tight mt-1.5 ${
                stat.big ? 'text-[24px]' : 'text-[15px]'
              } ${stat.tone && stat.big ? STAT_TONES[stat.tone] : 'text-gray-900 dark:text-white'}`}
            >
              {stat.icon && !stat.big && (
                <i className={`fa-solid ${stat.icon} text-[11px] mr-1.5 ${STAT_TONES[stat.tone] || ''}`} />
              )}
              <span className={stat.icon && !stat.big ? STAT_TONES[stat.tone] : ''}>{stat.value}</span>
            </p>

            {stat.sub && (
              <p className={`text-[10.5px] mt-1 leading-snug ${stat.big && stat.tone ? STAT_TONES[stat.tone] : 'text-gray-400 dark:text-slate-500'}`}>
                {stat.sub}
              </p>
            )}
          </Card>
        ))}
      </div>

      {/* ── Data feeds + usage ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2 p-4">
          <div className="flex items-start justify-between gap-3 mb-4">
            <div className="min-w-0">
              <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white">Data feeds</h3>
              <p className="text-[11.5px] text-gray-500 dark:text-slate-400 mt-0.5">{feedsSummary}</p>
            </div>
            <button className="text-[11.5px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 flex-shrink-0">
              View all feeds
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6">
            {feeds.map((feed) => (
              <div
                key={feed.name}
                className="flex items-center gap-2 py-2 border-b border-gray-50 dark:border-slate-800/60 last:border-0"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0" />
                <span className="text-[12.5px] font-semibold text-gray-900 dark:text-white truncate">
                  {feed.name}
                </span>
                <span
                  className={`px-1.5 py-0.5 rounded text-[9.5px] font-semibold whitespace-nowrap flex-shrink-0 ${
                    FEED_TAG_TONES[feed.tag] || FEED_TAG_TONES.Catalog
                  }`}
                >
                  {feed.tag}
                </span>
                <span className="text-[11px] text-gray-400 dark:text-slate-500 ml-auto whitespace-nowrap flex-shrink-0">
                  {feed.when}
                </span>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-4">
          <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white mb-3.5">Usage</h3>

          <p className="text-[11.5px] text-gray-500 dark:text-slate-400">API calls ({usage.window})</p>
          <div className="flex items-end justify-between gap-2 mt-1">
            <p className="text-[20px] font-bold text-gray-900 dark:text-white leading-none">
              {usage.usedLabel}
              <span className="text-[12px] font-medium text-gray-400 dark:text-slate-500">
                {' '}/ {usage.limitLabel}
              </span>
            </p>
            <span className="text-[12px] font-semibold text-gray-600 dark:text-slate-300">
              {usage.pct}%
            </span>
          </div>

          <div className="mt-2 h-1.5 rounded-full bg-gray-100 dark:bg-slate-800 overflow-hidden">
            <div className="h-full rounded-full bg-indigo-600" style={{ width: `${usage.pct}%` }} />
          </div>

          <div className="mt-4 space-y-2.5">
            {[
              { label: 'Rate limit', value: usage.rateLabel },
              { label: 'Remaining', value: `${usage.remainingLabel} calls` },
              { label: 'Resets in', value: usage.resetsIn },
            ].map((row) => (
              <div key={row.label} className="flex items-center justify-between gap-3">
                <span className="text-[12px] text-gray-500 dark:text-slate-400">{row.label}</span>
                <span className="text-[12px] font-semibold text-gray-900 dark:text-white text-right">
                  {row.value}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* ── Sync activity ── */}
      <Card className="p-4">
        <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
          <h3 className="text-[13.5px] font-bold text-gray-900 dark:text-white">
            Sync activity{' '}
            <span className="font-medium text-gray-400 dark:text-slate-500">(Last 7 days)</span>
          </h3>
          <SelectMenu
            value={metric}
            options={SYNC_METRICS}
            onChange={setMetric}
            size="sm"
            ariaLabel="Chart metric"
            className="w-[168px] flex-shrink-0"
          />
        </div>

        <SyncChart series={syncSeries(metric)} />
      </Card>
    </div>
  );
};

export default OverviewTab;
