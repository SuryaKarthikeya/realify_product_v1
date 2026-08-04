import React from 'react';
import { formatCompactMoney, formatCompactMagnitude } from '@/utils/formatters';

const exposureText = (signal) =>
  typeof signal.exposure === 'number'
    ? formatCompactMoney(signal.exposure)
    : (signal.exposureFormatted || '—');

const renderChannelBadge = (signal, isCollapsed) => {
  const channelRaw = (signal.sourceOwn || signal.channel || signal.marketplace || 'amazon').toLowerCase();

  if (channelRaw.includes('shopify')) {
    if (isCollapsed) {
      return (
        <span className="w-6 h-6 rounded-full bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800/60 text-emerald-600 dark:text-emerald-400 inline-flex items-center justify-center text-xs" title="Shopify">
          <i className="fa-brands fa-shopify text-[11px]" />
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200">
        <i className="fa-brands fa-shopify text-[11px]" />
        Shopify
      </span>
    );
  }

  if (channelRaw.includes('amazon')) {
    if (isCollapsed) {
      return (
        <span className="w-6 h-6 rounded-full bg-[#FFFAF0] dark:bg-amber-950/60 border border-[#FBD38D] text-[#DD6B20] inline-flex items-center justify-center text-xs" title="Amazon">
          <i className="fa-brands fa-amazon text-[11px]" />
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-[#FFFAF0] dark:bg-amber-950/60 text-[#DD6B20] dark:text-amber-400 border border-[#FBD38D]">
        <i className="fa-brands fa-amazon text-[11px]" />
        Amazon
      </span>
    );
  }

  // Walmart / Default
  if (isCollapsed) {
    return (
      <span className="w-6 h-6 rounded-full bg-blue-50 dark:bg-blue-950/60 border border-blue-200 dark:border-blue-800/60 text-blue-600 dark:text-blue-400 inline-flex items-center justify-center text-xs" title="Walmart">
        <i className="fa-solid fa-store text-[10px]" />
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-bold bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200">
      <i className="fa-solid fa-store text-[10px]" />
      Walmart
    </span>
  );
};

/** Plain numeric cell — Ads spend / impressions / clicks. */
const metricCell = (value, isCollapsed = false) => (
  <span className={`font-mono tabular font-medium text-gray-700 dark:text-slate-300 whitespace-nowrap ${isCollapsed ? 'text-[11px]' : 'text-[12px]'}`}>
    {value ?? '—'}
  </span>
);

/**
 * The Ads domain reports on campaigns rather than SKUs, so its table carries the
 * media-buying columns the other domains have no values for.
 *
 * Collapsed to 55% beside the simulation panel the same set of columns is kept —
 * nothing is dropped — the widths just tighten and the campaign name absorbs the
 * squeeze.
 */
const adsMetricColumns = (isCollapsed) => [
  {
    key: 'spend',
    header: 'SPEND',
    align: 'right',
    className: isCollapsed
      ? 'w-[62px] whitespace-nowrap align-middle'
      : 'w-[86px] whitespace-nowrap align-middle',
    render: (signal) => metricCell(formatCompactMoney(signal.spend), isCollapsed),
  },
  {
    key: 'impressions',
    header: 'IMPR',
    align: 'right',
    className: isCollapsed
      ? 'w-[58px] whitespace-nowrap align-middle'
      : 'w-[80px] whitespace-nowrap align-middle hidden lg:table-cell',
    render: (signal) => metricCell(formatCompactMagnitude(signal.impressions), isCollapsed),
  },
  {
    key: 'clicks',
    header: 'CLICKS',
    align: 'right',
    className: isCollapsed
      ? 'w-[52px] whitespace-nowrap align-middle'
      : 'w-[74px] whitespace-nowrap align-middle',
    render: (signal) => metricCell(formatCompactMagnitude(signal.clicks), isCollapsed),
  },
  {
    key: 'roas',
    header: 'ROAS',
    align: 'center',
    className: isCollapsed
      ? 'w-[50px] whitespace-nowrap align-middle text-center'
      : 'w-[72px] whitespace-nowrap align-middle text-center',
    render: (signal) => (
      <span className={`font-mono tabular font-bold text-gray-900 dark:text-white whitespace-nowrap ${isCollapsed ? 'text-[11.5px]' : 'text-[12.5px]'}`}>
        {signal.roas || '—'}
      </span>
    ),
  },
];

/**
 * Inventory domain columns
 */
const inventoryMetricColumns = (isCollapsed) => [
  {
    key: 'fulfillmentType',
    header: 'FULFILLMENT',
    align: 'left',
    className: isCollapsed
      ? 'w-[80px] whitespace-nowrap align-middle'
      : 'w-[100px] whitespace-nowrap align-middle',
    render: (signal) => {
      const channelRaw = (signal.sourceOwn || signal.channel || signal.marketplace || 'amazon').toLowerCase();
      const isAmazon = channelRaw.includes('amazon');
      const defaultFulfillment = isAmazon ? 'FBA' : '3PL';
      return (
        <span className={`font-medium text-gray-700 dark:text-slate-300 ${isCollapsed ? 'text-[11px]' : 'text-[12px]'}`}>
          {signal.fulfillmentType || defaultFulfillment}
        </span>
      );
    },
  },
  {
    key: 'stockoutDays',
    header: 'STOCKOUT',
    align: 'left',
    className: isCollapsed
      ? 'w-[70px] whitespace-nowrap align-middle'
      : 'w-[90px] whitespace-nowrap align-middle',
    render: (signal) => (
      <span className={`font-medium text-gray-700 dark:text-slate-300 ${isCollapsed ? 'text-[11px]' : 'text-[12px]'}`}>
        {signal.stockoutDays ? `${signal.stockoutDays} days` : '4 days'}
      </span>
    ),
  },
];

/**
 * Cash domain columns
 */
const cashMetricColumns = (isCollapsed) => [
  {
    key: 'urgency',
    header: 'URGENCY',
    align: 'left',
    className: isCollapsed
      ? 'w-[70px] whitespace-nowrap align-middle'
      : 'w-[90px] whitespace-nowrap align-middle',
    render: (signal) => (
      <span className={`font-medium text-gray-700 dark:text-slate-300 ${isCollapsed ? 'text-[11px]' : 'text-[12px]'}`}>
        {signal.urgency || '≤30 days'}
      </span>
    ),
  },
  {
    key: 'cashDirection',
    header: 'CASH DIRECTION',
    align: 'left',
    className: isCollapsed
      ? 'w-[100px] whitespace-nowrap align-middle'
      : 'w-[140px] whitespace-nowrap align-middle',
    render: (signal) => {
      let direction = signal.cashDirection || 'Inflow Accelerating';
      if (isCollapsed) {
        direction = direction.replace('Accelerating', 'Acc').replace('Reducing', 'Red');
      }
      return (
        <span className={`font-medium text-gray-700 dark:text-slate-300 ${isCollapsed ? 'text-[11px]' : 'text-[12px]'}`}>
          {direction}
        </span>
      );
    },
  },
];

/**
 * ── Responsive Column config for the Workspace Actions table ──
 */
export const getSignalColumns = (isCollapsed = false, activeDomain = 'sales') => {
  const isAds = activeDomain === 'ads';
  const isInventory = activeDomain === 'inventory';
  const isCash = activeDomain === 'cash';

  return [
  {
    key: 'action',
    header: isAds ? 'CAMPAIGN' : 'DESCRIPTION',
    // Collapsed, this is the only elastic column: every other header stays on
    // screen and the description absorbs the squeeze (narrower + a step down in
    // type size) rather than a column being dropped.
    className: isCollapsed ? 'min-w-0 pr-1' : 'min-w-0 pr-2',
    render: (signal) => {
      // Ads rows are identified by campaign name; every other domain leads with
      // the recommendation itself.
      const label = isAds
        ? (signal.campaign || signal.headlineHighlight || signal.headline)
        : (signal.headlineHighlight || signal.headline);
      return (
        <div className="min-w-0 pr-1">
          {/* Same weight in every domain — Ads used to render bold, which read
              as a different kind of row than the other four KPIs. */}
          <p className={`truncate leading-snug font-normal text-gray-800 dark:text-slate-200 ${isCollapsed ? 'text-[11.5px]' : 'text-[12.5px]'}`} title={label}>
            {label || ''}
          </p>
        </div>
      );
    },
  },
  {
    key: 'channel',
    // The collapsed cell is a 24px logo, so the full word would overflow the
    // fixed column and bleed into SKUS.
    header: isCollapsed ? 'CH' : 'CHANNEL',
    className: isCollapsed ? 'w-[38px] whitespace-nowrap align-middle text-center' : 'w-[110px] whitespace-nowrap align-middle',
    render: (signal) => renderChannelBadge(signal, isCollapsed),
  },
  {
    key: 'sku',
    header: 'SKUS',
    className: isCollapsed ? 'w-[44px] whitespace-nowrap align-middle text-center' : 'w-[75px] whitespace-nowrap align-middle',
    render: (signal) => {
      const count = signal.skuCount || signal.affectedSkusCount || 1;
      return (
        <span className={`font-medium text-gray-700 dark:text-slate-300 whitespace-nowrap text-center block w-full ${isCollapsed ? 'text-[11px]' : 'text-[11.5px]'}`}>
          {count}
        </span>
      );
    },
  },
  // Ads carries its own metric spread instead of CATEGORY, in both widths.
  ...(!isAds ? [{
    key: 'category',
    header: 'CATEGORY',
    className: isCollapsed
      ? 'whitespace-nowrap align-middle w-[78px]'
      : 'whitespace-nowrap align-middle w-[110px] hidden md:table-cell',
    render: (signal) => (
      <span className={`font-normal text-gray-600 dark:text-slate-400 truncate block ${isCollapsed ? 'text-[11px] max-w-[72px]' : 'text-[12px] max-w-[100px]'}`}>
        {signal.category || '—'}
      </span>
    ),
  }] : []),
  ...(isAds ? adsMetricColumns(isCollapsed) : []),
  ...(isInventory ? inventoryMetricColumns(isCollapsed) : []),
  ...(isCash ? cashMetricColumns(isCollapsed) : []),
  {
    key: 'impact',
    header: 'IMPACT',
    align: 'left',
    className: isCollapsed ? 'w-[60px] whitespace-nowrap align-middle text-left' : 'w-[80px] whitespace-nowrap align-middle text-left pr-2',
    render: (signal) => (
      <span className={`font-mono tabular font-bold text-gray-900 dark:text-white ${isCollapsed ? 'text-[11.5px]' : 'text-[12.5px]'}`}>
        {exposureText(signal)}
      </span>
    ),
  },
  ];
};

export const SIGNAL_COLUMNS = getSignalColumns(false);
