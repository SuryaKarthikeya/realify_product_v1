import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import DashboardLayout from '@/layouts/DashboardLayout';
import { ROUTES } from '@/constants/routes';
import { DEFAULT_DOMAIN } from '@/features/workspace/workspaceRoutes';

const INSIGHT_TYPE_META = {
  CRITICAL:    { bg: 'bg-red-100 dark:bg-red-900/30',      color: 'text-red-600 dark:text-red-400'      },
  HIGH:        { bg: 'bg-amber-100 dark:bg-amber-900/30',  color: 'text-amber-600 dark:text-amber-400'  },
  OPPORTUNITY: { bg: 'bg-green-100 dark:bg-green-900/30',  color: 'text-green-600 dark:text-green-400'  },
  INSIGHT:     { bg: 'bg-blue-100 dark:bg-blue-900/30',    color: 'text-blue-600 dark:text-blue-400'    },
  MARKET:      { bg: 'bg-purple-100 dark:bg-purple-900/30',color: 'text-purple-600 dark:text-purple-400'},
  PAYMENT:     { bg: 'bg-orange-100 dark:bg-orange-900/30',color: 'text-orange-600 dark:text-orange-400'},
};

const TAB_STATE_DATA = {
  sales: {
    previous: {
      label: 'Before Execution',
      statusLabel: 'Buy Box Declining',
      statusColor: 'text-red-600 dark:text-red-400',
      statusBg: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800/40',
      statusIcon: 'fa-arrow-trend-down',
      metrics: [
        { label: 'Listing Price',      value: '$88.00',   sub: 'Before reprice action',   color: 'text-gray-900 dark:text-slate-100' },
        { label: 'Competitor Price',   value: '$74.99',   sub: 'Active undercutting',      color: 'text-red-600 dark:text-red-400'   },
        { label: 'Buy Box Share',      value: '71%',      sub: 'Down from 94% in 6h',      color: 'text-red-600 dark:text-red-400'   },
        { label: 'Revenue / Day',      value: '$2,236',   sub: 'Est. at 43 units/day',     color: 'text-gray-700 dark:text-slate-300' },
        { label: 'Gross Margin',       value: '58.8%',    sub: 'Above 56.8% floor',        color: 'text-green-600 dark:text-green-400'},
        { label: 'Revenue at Risk',    value: '−$559/day',sub: 'From buy box loss',        color: 'text-red-600 dark:text-red-400'   },
      ],
      timeline: [
        { icon: 'fa-flag',                 color: 'text-red-500',   text: 'Competitor repriced to $74.99',             time: 'Jun 26, 03:30' },
        { icon: 'fa-chart-line',           color: 'text-amber-500', text: 'Buy box dropped 94% → 71% over 6 hours',    time: 'Jun 26, 06:30' },
        { icon: 'fa-triangle-exclamation', color: 'text-red-500',   text: 'Revenue leakage detected: −$559/day',       time: 'Jun 26, 09:28' },
      ],
    },
    current: {
      label: 'After Execution',
      statusLabel: 'Buy Box Recovered',
      statusColor: 'text-green-600 dark:text-green-400',
      statusBg: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800/40',
      statusIcon: 'fa-shield-check',
      metrics: [
        { label: 'Listing Price',      value: '$84.99',    sub: 'Repriced by action',        color: 'text-gray-900 dark:text-slate-100'  },
        { label: 'Competitor Price',   value: '$74.99',    sub: 'Active competitor',          color: 'text-amber-600 dark:text-amber-400' },
        { label: 'Buy Box Share',      value: '94%',       sub: 'Fully recovered',            color: 'text-green-600 dark:text-green-400' },
        { label: 'Revenue / Day',      value: '$3,654',    sub: 'Est. at 43 units/day',       color: 'text-green-600 dark:text-green-400' },
        { label: 'Gross Margin',       value: '56.8%',     sub: 'At target floor',            color: 'text-blue-600 dark:text-blue-400'   },
        { label: 'Revenue Protected',  value: '+$12,400',  sub: 'Est. this week',             color: 'text-green-600 dark:text-green-400' },
      ],
    },
  },
  margin: {
    previous: {
      label: 'Before Execution',
      statusLabel: 'Margin Compressed',
      statusColor: 'text-red-600 dark:text-red-400',
      statusBg: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800/40',
      statusIcon: 'fa-arrow-trend-down',
      metrics: [
        { label: 'Current Price',    value: '$100.00', sub: 'Before adjustment',     color: 'text-gray-900 dark:text-slate-100' },
        { label: 'COGS / Unit',      value: '$42.00',  sub: 'Supplier cost rise',    color: 'text-red-600 dark:text-red-400'   },
        { label: 'Gross Margin',     value: '19.1%',   sub: 'Below 25% target',      color: 'text-red-600 dark:text-red-400'   },
        { label: 'Monthly GM Loss',  value: '−$14,200',sub: 'vs 28% CM2 target',     color: 'text-red-600 dark:text-red-400'   },
        { label: 'Blended CM2',      value: '19.1%',   sub: 'Across affected SKUs',  color: 'text-amber-600 dark:text-amber-400'},
        { label: 'SKUs Affected',    value: '18',      sub: 'Electronics category',  color: 'text-gray-700 dark:text-slate-300' },
      ],
      timeline: [
        { icon: 'fa-file-invoice-dollar', color: 'text-red-500',   text: 'Supplier raised COGS by 12%',           time: 'Jun 25, 14:00' },
        { icon: 'fa-chart-pie',           color: 'text-amber-500', text: 'GM fell to 19.1% across 18 SKUs',        time: 'Jun 25, 18:00' },
        { icon: 'fa-triangle-exclamation',color: 'text-red-500',   text: 'Monthly GM loss of $14,200 detected',    time: 'Jun 26, 09:00' },
      ],
    },
    current: {
      label: 'After Execution',
      statusLabel: 'Margin Restored',
      statusColor: 'text-green-600 dark:text-green-400',
      statusBg: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800/40',
      statusIcon: 'fa-shield-check',
      metrics: [
        { label: 'Updated Price',    value: '$109.00', sub: 'Repriced +9%',          color: 'text-gray-900 dark:text-slate-100'  },
        { label: 'COGS / Unit',      value: '$42.00',  sub: 'Unchanged',             color: 'text-gray-700 dark:text-slate-300'  },
        { label: 'Gross Margin',     value: '28.0%',   sub: 'CM2 target restored',   color: 'text-green-600 dark:text-green-400' },
        { label: 'Monthly GM Gain',  value: '+$14,200',sub: 'vs prior state',        color: 'text-green-600 dark:text-green-400' },
        { label: 'Blended CM2',      value: '28.0%',   sub: 'Across affected SKUs',  color: 'text-green-600 dark:text-green-400' },
        { label: 'SKUs Corrected',   value: '18',      sub: 'All now above target',  color: 'text-blue-600 dark:text-blue-400'   },
      ],
    },
  },
  inventory: {
    previous: {
      label: 'Before Execution',
      statusLabel: 'OOS Risk High',
      statusColor: 'text-red-600 dark:text-red-400',
      statusBg: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800/40',
      statusIcon: 'fa-boxes-stacked',
      metrics: [
        { label: 'Stock on Hand',   value: '50 units',  sub: 'Current inventory',     color: 'text-red-600 dark:text-red-400'   },
        { label: 'Daily Velocity',  value: '14 units',  sub: 'Average sell-through',  color: 'text-gray-700 dark:text-slate-300' },
        { label: 'Days of Cover',   value: '3.6 days',  sub: 'Below 21-day minimum',  color: 'text-red-600 dark:text-red-400'   },
        { label: 'OOS Risk',        value: 'Critical',  sub: 'Within 4 days',         color: 'text-red-600 dark:text-red-400'   },
        { label: 'Lead Time',       value: '18 days',   sub: 'Supplier lead time',    color: 'text-amber-600 dark:text-amber-400'},
        { label: 'Buy Box Risk',    value: 'High',      sub: 'Below Amazon threshold',color: 'text-red-600 dark:text-red-400'   },
      ],
      timeline: [
        { icon: 'fa-boxes-stacked', color: 'text-amber-500', text: 'Stock fell below 21-day cover threshold', time: 'Jun 25, 10:00' },
        { icon: 'fa-triangle-exclamation', color: 'text-red-500', text: 'OOS risk detected: 3.6 days remaining', time: 'Jun 26, 08:00' },
      ],
    },
    current: {
      label: 'After Execution',
      statusLabel: 'Stock Secured',
      statusColor: 'text-green-600 dark:text-green-400',
      statusBg: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800/40',
      statusIcon: 'fa-shield-check',
      metrics: [
        { label: 'Stock on Hand',   value: '50 units',  sub: 'Existing inventory',    color: 'text-gray-700 dark:text-slate-300' },
        { label: 'PO Placed',       value: '500 units', sub: 'Reorder executed',      color: 'text-green-600 dark:text-green-400'},
        { label: 'Days of Cover',   value: '39 days',   sub: 'Above 21-day minimum',  color: 'text-green-600 dark:text-green-400'},
        { label: 'OOS Risk',        value: 'Eliminated',sub: 'After PO arrival',      color: 'text-green-600 dark:text-green-400'},
        { label: 'Lead Time',       value: '18 days',   sub: 'Supplier lead time',    color: 'text-gray-700 dark:text-slate-300' },
        { label: 'Buy Box Risk',    value: 'Resolved',  sub: 'Above Amazon threshold',color: 'text-blue-600 dark:text-blue-400'  },
      ],
    },
  },
  ads: {
    previous: {
      label: 'Before Execution',
      statusLabel: 'Low ROAS',
      statusColor: 'text-red-600 dark:text-red-400',
      statusBg: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800/40',
      statusIcon: 'fa-arrow-trend-down',
      metrics: [
        { label: 'Ad Budget / Mo',  value: '$800',     sub: 'Before adjustment',    color: 'text-gray-900 dark:text-slate-100' },
        { label: 'ROAS',            value: '2.8x',     sub: 'Below 4.0x target',    color: 'text-red-600 dark:text-red-400'   },
        { label: 'ACoS',            value: '44.6%',    sub: 'Above 25% target',     color: 'text-red-600 dark:text-red-400'   },
        { label: 'Monthly Revenue', value: '$2,240',   sub: 'From ad spend',        color: 'text-gray-700 dark:text-slate-300' },
        { label: 'CPC',             value: '$0.94',    sub: 'Avg. cost per click',  color: 'text-amber-600 dark:text-amber-400'},
        { label: 'Impressions',     value: '24,000',   sub: 'Monthly avg.',         color: 'text-gray-700 dark:text-slate-300' },
      ],
      timeline: [
        { icon: 'fa-bullhorn',            color: 'text-amber-500', text: 'ROAS fell to 2.8x across campaigns',  time: 'Jun 24, 00:00' },
        { icon: 'fa-triangle-exclamation',color: 'text-red-500',   text: 'ACoS breach: 44.6% vs 25% target',    time: 'Jun 26, 09:00' },
      ],
    },
    current: {
      label: 'After Execution',
      statusLabel: 'ROAS Improved',
      statusColor: 'text-green-600 dark:text-green-400',
      statusBg: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800/40',
      statusIcon: 'fa-shield-check',
      metrics: [
        { label: 'Ad Budget / Mo',  value: '$2,000',   sub: 'Scaled to target budget', color: 'text-gray-900 dark:text-slate-100'  },
        { label: 'ROAS',            value: '4.1x',     sub: 'Above 4.0x target',       color: 'text-green-600 dark:text-green-400' },
        { label: 'ACoS',            value: '26.2%',    sub: 'Near 25% target',         color: 'text-blue-600 dark:text-blue-400'   },
        { label: 'Monthly Revenue', value: '$8,200',   sub: 'From ad spend',           color: 'text-green-600 dark:text-green-400' },
        { label: 'CPC',             value: '$0.61',    sub: 'Phrase match savings',    color: 'text-green-600 dark:text-green-400' },
        { label: 'Impressions',     value: '39,200',   sub: '+63% vs before',          color: 'text-blue-600 dark:text-blue-400'   },
      ],
    },
  },
  cash: {
    previous: {
      label: 'Before Execution',
      statusLabel: 'Cash Flow Risk',
      statusColor: 'text-red-600 dark:text-red-400',
      statusBg: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800/40',
      statusIcon: 'fa-money-bill-trend-up',
      metrics: [
        { label: 'Invoice Amount',  value: '$42,000',  sub: 'Electronics PO',         color: 'text-gray-900 dark:text-slate-100' },
        { label: 'Due Date',        value: 'Jun 28',   sub: '2 days remaining',        color: 'text-red-600 dark:text-red-400'   },
        { label: 'Cash Runway',     value: '28 days',  sub: 'Below 45-day target',     color: 'text-amber-600 dark:text-amber-400'},
        { label: 'Interest Cost',   value: '$220/mo',  sub: '5.25% cost of capital',  color: 'text-gray-700 dark:text-slate-300' },
        { label: 'Early Pay Disc.', value: '2.5%',     sub: 'Supplier offer',          color: 'text-green-600 dark:text-green-400'},
        { label: 'Potential Saving',value: '$1,050',   sub: 'If paid early',           color: 'text-green-600 dark:text-green-400'},
      ],
      timeline: [
        { icon: 'fa-file-invoice', color: 'text-amber-500', text: 'Large Electronics PO invoice due in 2 days', time: 'Jun 24, 09:00' },
        { icon: 'fa-triangle-exclamation', color: 'text-red-500', text: 'Cash runway flagged below 45-day minimum', time: 'Jun 26, 09:00' },
      ],
    },
    current: {
      label: 'After Execution',
      statusLabel: 'Payment Optimised',
      statusColor: 'text-green-600 dark:text-green-400',
      statusBg: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800/40',
      statusIcon: 'fa-shield-check',
      metrics: [
        { label: 'Invoice Amount',  value: '$42,000',  sub: 'Electronics PO',         color: 'text-gray-900 dark:text-slate-100'  },
        { label: 'New Due Date',    value: 'Jul 13',   sub: '+15 days extended',       color: 'text-green-600 dark:text-green-400' },
        { label: 'Cash Runway',     value: '45 days',  sub: 'At target threshold',     color: 'text-green-600 dark:text-green-400' },
        { label: 'Interest Cost',   value: '$220/mo',  sub: 'Accepted to free cash',   color: 'text-gray-700 dark:text-slate-300'  },
        { label: 'Cash Freed',      value: '$42,000',  sub: 'Operating liquidity',     color: 'text-green-600 dark:text-green-400' },
        { label: 'Runway Extended', value: '+17 days', sub: '28 → 45 days',           color: 'text-blue-600 dark:text-blue-400'   },
      ],
    },
  },
};

const getStateData = (domain) => TAB_STATE_DATA[domain] || TAB_STATE_DATA.sales;

const MetricCard = ({ metric, variant }) => (
  <div className={`p-3 rounded-xl border ${
    variant === 'current'
      ? 'border-green-100 dark:border-green-900/30 bg-green-50/30 dark:bg-green-900/10'
      : 'border-gray-100 dark:border-slate-800 bg-white dark:bg-slate-900/60'
  }`}>
    <p className="text-[9px] text-gray-400 dark:text-slate-500 mb-1 uppercase tracking-wide">{metric.label}</p>
    <p className={`text-sm font-bold leading-tight ${metric.color}`}>{metric.value}</p>
    {metric.sub && (
      <p className="text-[9px] text-gray-400 dark:text-slate-500 mt-0.5 leading-tight">{metric.sub}</p>
    )}
  </div>
);

const StateColumn = ({ data, variant }) => {
  const isCurrent = variant === 'current';
  return (
    <div className={`flex-1 min-w-0 rounded-2xl border shadow-sm ${
      isCurrent
        ? 'border-green-200 dark:border-green-800/40 bg-white dark:bg-slate-900'
        : 'border-gray-200 dark:border-slate-700 bg-gray-50/60 dark:bg-slate-900/60'
    } p-5 flex flex-col gap-4`}>

      {/* Column header */}
      <div className={`flex items-start gap-3 pb-4 border-b ${
        isCurrent ? 'border-green-100 dark:border-green-900/30' : 'border-gray-100 dark:border-slate-800'
      }`}>
        <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${
          isCurrent ? 'bg-green-100 dark:bg-green-900/30' : 'bg-gray-100 dark:bg-slate-800'
        }`}>
          <i className={`fa-solid ${isCurrent ? 'fa-circle-check' : 'fa-clock-rotate-left'} text-sm ${
            isCurrent ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-slate-400'
          }`} />
        </div>
        <div className="flex-1 min-w-0">
          <p className={`text-sm font-bold mb-1 ${
            isCurrent ? 'text-green-800 dark:text-green-300' : 'text-gray-700 dark:text-slate-300'
          }`}>
            {data.label}
          </p>
          <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-lg text-[9px] font-bold border ${data.statusBg} ${data.statusColor}`}>
            <i className={`fa-solid ${data.statusIcon} text-[8px]`} />
            {data.statusLabel}
          </span>
        </div>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 gap-2">
        {data.metrics.map((m, i) => (
          <MetricCard key={i} metric={m} variant={variant} />
        ))}
      </div>

      {/* Timeline — only for previous state */}
      {data.timeline?.length > 0 && (
        <div className="mt-auto pt-3 border-t border-gray-100 dark:border-slate-800">
          <p className="text-[9px] font-bold text-gray-400 dark:text-slate-500 uppercase tracking-widest mb-2.5 flex items-center gap-1.5">
            <i className="fa-solid fa-timeline text-[8px]" /> Event Timeline
          </p>
          <div className="space-y-2.5">
            {data.timeline.map((t, i) => (
              <div key={i} className="flex items-start gap-2.5">
                <div className="w-5 h-5 rounded-full bg-gray-100 dark:bg-slate-800 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <i className={`fa-solid ${t.icon} text-[8px] ${t.color}`} />
                </div>
                <div className="min-w-0">
                  <p className="text-[11px] text-gray-700 dark:text-slate-300 leading-snug">{t.text}</p>
                  <p className="text-[9px] text-gray-400 dark:text-slate-500 mt-0.5">{t.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const RollbackPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const stateData = location.state || {};

  const insight     = stateData.insight     || null;
  const domain    = stateData.domain    || DEFAULT_DOMAIN;
  const executedAt  = stateData.executedAt  || null;

  const [isRollingBack, setIsRollingBack] = useState(false);
  const [rolledBack,    setRolledBack]    = useState(false);

  const insightMeta  = INSIGHT_TYPE_META[insight?.type] || INSIGHT_TYPE_META.INSIGHT;
  const { previous, current } = getStateData(domain);

  const handleBack = () => navigate(-1);

  const handleRollback = () => {
    setIsRollingBack(true);
    setTimeout(() => {
      setIsRollingBack(false);
      setRolledBack(true);
    }, 1800);
  };

  return (
    <DashboardLayout title="Intelligence" subtitle="Real-time sales analytics" showSearch={false} showTabs={false}>

      {/* Back */}
      <div className="flex items-center -mt-2 pb-4">
        <button
          onClick={handleBack}
          className="flex items-center gap-2 text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200 transition-colors"
        >
          <i className="fa-solid fa-arrow-left text-sm" />
        </button>
      </div>

      {/* Page header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 flex-wrap mb-2">
          {insight?.type && (
            <span className={`px-2.5 py-1 text-[10px] rounded-lg font-bold uppercase tracking-wider ${insightMeta.bg} ${insightMeta.color}`}>
              {insight.type === 'HIGH' ? 'HIGH IMPACT' : insight.type}
            </span>
          )}
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-bold bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800/40">
            <i className="fa-solid fa-rotate-left text-[9px]" /> ROLLBACK
          </span>
          {executedAt && (
            <span className="text-xs text-gray-400 dark:text-slate-500">Executed {executedAt}</span>
          )}
        </div>
        <h1 className="text-xl font-bold text-gray-900 dark:text-slate-100 leading-snug">
          {insight?.heading || 'Rollback Action'}
        </h1>
        <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
          Review the state changes below before rolling back to restore the previous configuration.
        </p>
      </div>

      {rolledBack ? (
        /* ── Success state ──────────────────────────────────────────── */
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="w-16 h-16 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center mb-4">
            <i className="fa-solid fa-rotate-left text-2xl text-amber-600 dark:text-amber-400" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-2">Rollback Complete</h2>
          <p className="text-sm text-gray-500 dark:text-slate-400 mb-6 max-w-sm leading-relaxed">
            The action has been reversed. Product configuration has been restored to the previous state.
          </p>
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate(ROUTES.WORKSPACE)}
              className="px-5 py-2.5 bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 rounded-xl font-bold text-sm hover:opacity-90 transition-all"
            >
              Back to Intelligence
            </button>
          </div>
        </div>
      ) : (
        /* ── Comparison layout ──────────────────────────────────────── */
        <div className="flex flex-col lg:flex-row items-stretch gap-4 lg:gap-0">

          {/* Previous State */}
          <StateColumn data={previous} variant="previous" />

          {/* Center divider with Rollback button */}
          <div className="flex lg:flex-col items-center justify-center gap-4 py-4 lg:py-0 lg:px-5">
            {/* Top fade line — desktop only */}
            <div className="hidden lg:block w-px flex-1 bg-gradient-to-b from-transparent via-gray-200 dark:via-slate-700 to-transparent" />

            <div className="flex flex-col items-center gap-3">
              {/* Arrow indicator */}
              <div className="flex lg:flex-col items-center gap-2">
                <div className="w-7 h-7 rounded-full border-2 border-dashed border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-900 flex items-center justify-center">
                  <i className="fa-solid fa-arrow-right text-[10px] text-gray-400 dark:text-slate-500 lg:hidden" />
                  <i className="fa-solid fa-arrow-down text-[10px] text-gray-400 dark:text-slate-500 hidden lg:block" />
                </div>
              </div>

              {/* Rollback button */}
              <button
                onClick={handleRollback}
                disabled={isRollingBack}
                className={`flex flex-col items-center gap-1.5 px-5 py-3.5 rounded-2xl font-bold text-xs transition-all shadow-lg whitespace-nowrap border ${
                  isRollingBack
                    ? 'bg-amber-400 dark:bg-amber-600 border-amber-300 dark:border-amber-700 text-white cursor-not-allowed opacity-70'
                    : 'bg-amber-500 hover:bg-amber-600 active:scale-95 border-amber-400 dark:border-amber-600 text-white shadow-amber-500/25'
                }`}
              >
                {isRollingBack ? (
                  <>
                    <i className="fa-solid fa-circle-notch fa-spin text-base" />
                    <span>Rolling back…</span>
                  </>
                ) : (
                  <>
                    <i className="fa-solid fa-rotate-left text-base" />
                    <span>Rollback to</span>
                    <span>Previous State</span>
                  </>
                )}
              </button>

              <p className="text-[9px] text-gray-400 dark:text-slate-500 text-center max-w-[80px] leading-tight hidden lg:block">
                This will undo the executed action
              </p>
            </div>

            {/* Bottom fade line — desktop only */}
            <div className="hidden lg:block w-px flex-1 bg-gradient-to-b from-transparent via-gray-200 dark:via-slate-700 to-transparent" />
          </div>

          {/* Current State */}
          <StateColumn data={current} variant="current" />
        </div>
      )}
    </DashboardLayout>
  );
};

export default RollbackPage;
