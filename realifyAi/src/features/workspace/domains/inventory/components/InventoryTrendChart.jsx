import React, { useMemo, useState } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import {
  INVENTORY_CATEGORIES,
  INVENTORY_GRANULARITIES,
  INVENTORY_METRICS,
  formatInventoryMetric,
  inventoryTrends,
} from '@/features/workspace/domains/inventory/data/inventoryData';
import { CHART_CATEGORICAL } from '@/utils/chartColors';
import { useDarkMode } from '@/hooks/useDarkMode';

const GRADIENT_IDS = ['colorElec', 'colorApp', 'colorHome'];

/**
 * Tooltip from ss2: the period, every category with its own dot, then the total
 * under a rule. The total is the point of a stacked-looking chart — without it
 * the reader has to add three numbers in their head.
 */
const TrendTooltip = ({ active, payload, label, metric }) => {
  if (!active || !payload?.length) return null;
  const total = payload.reduce((sum, p) => sum + (p.value || 0), 0);
  const unit = metric === 'value' ? '' : ' units';

  return (
    <div className="rounded-2xl bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 shadow-xl px-4 py-3 min-w-[190px]">
      <p className="text-[13px] font-bold text-gray-900 dark:text-white mb-2">{label}</p>

      <div className="space-y-1.5">
        {payload.map((p) => (
          <p key={p.dataKey} className="text-[12.5px] flex items-center gap-2" style={{ color: p.color }}>
            <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: p.color }} />
            <span className="font-medium">{p.name} :</span>
            <span className="font-semibold ml-auto">
              {formatInventoryMetric(p.value, metric, { compact: metric === 'value' })}
            </span>
          </p>
        ))}
      </div>

      <div className="mt-2 pt-2 border-t border-gray-100 dark:border-slate-800 flex items-center gap-2">
        <span className="text-[12.5px] text-gray-500 dark:text-slate-400">Total :</span>
        <span className="text-[14px] font-bold text-gray-900 dark:text-white ml-auto">
          {formatInventoryMetric(total, metric, { compact: metric === 'value' })}
          <span className="text-[11.5px] font-medium text-gray-400 dark:text-slate-500">{unit}</span>
        </span>
      </div>
    </div>
  );
};

/**
 * Inventory levels over time, by category.
 *
 * Two independent controls: the granularity segmented control picks the period
 * (which changes the x-axis and the number of points), and the Level / Value
 * switch re-expresses the same stock in units or rupees. They compose, so any of
 * the six combinations is reachable.
 *
 * `darkMode` is still accepted for callers that pass it, but defaults to the
 * theme store — DashboardViewPage renders this with no props, which used to leave
 * the axes and tooltip painted for light mode on a dark page.
 */
const InventoryTrendChart = ({ darkMode }) => {
  const [isDark] = useDarkMode();
  const dark = darkMode ?? isDark;

  const [granularity, setGranularity] = useState(INVENTORY_GRANULARITIES[0]);
  const [metric, setMetric] = useState('level');

  const data = useMemo(() => inventoryTrends(granularity, metric), [granularity, metric]);
  const meta = INVENTORY_METRICS[metric];
  const isValue = metric === 'value';

  return (
    <div className="w-full h-full min-h-[400px] flex flex-col">

      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100">Inventory Trends</h3>
          <p className="text-sm text-gray-600 dark:text-slate-400 mt-0.5">
            Track your inventory levels and value over time
          </p>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {INVENTORY_GRANULARITIES.map((g) => (
            <button
              key={g}
              onClick={() => setGranularity(g)}
              aria-pressed={granularity === g}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                granularity === g
                  ? 'bg-[#2c2c2c] dark:bg-slate-100 text-white dark:text-slate-900 shadow-sm'
                  : 'bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 text-gray-700 dark:text-slate-300'
              }`}
            >
              {g}
            </button>
          ))}
        </div>
      </div>

      {/* ── Metric switch ── */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 mt-4">
        <div className="rounded-2xl border border-gray-200 dark:border-slate-800 p-1.5 flex items-center gap-1 self-start">
          {/* Each side is clickable as well as the switch itself: the labels look
              like targets, so they should behave like them. */}
          {['level', 'value'].map((key) => {
            const m = INVENTORY_METRICS[key];
            const on = metric === key;
            const control = (
              <button
                key={key}
                onClick={() => setMetric(key)}
                aria-pressed={on}
                className={`flex items-center gap-2.5 rounded-xl px-3 py-2 transition-colors text-left ${
                  on ? 'bg-indigo-50 dark:bg-indigo-950/40' : 'hover:bg-gray-50 dark:hover:bg-slate-800/60'
                }`}
              >
                <span
                  className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    on
                      ? 'bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400'
                      : 'bg-gray-100 dark:bg-slate-800 text-gray-400 dark:text-slate-500'
                  }`}
                >
                  <i className={`fa-solid ${m.icon} text-[13px]`} />
                </span>
                <span className="min-w-0">
                  <span
                    className={`block text-[13px] font-bold leading-tight ${
                      on ? 'text-indigo-600 dark:text-indigo-400' : 'text-gray-500 dark:text-slate-400'
                    }`}
                  >
                    {m.label}
                  </span>
                  <span className="block text-[11.5px] text-gray-500 dark:text-slate-500 leading-tight mt-0.5">
                    {m.sub}
                  </span>
                </span>
              </button>
            );

            /* The switch sits between the two sides, as in ss2. */
            return key === 'level'
              ? [
                  control,
                  <button
                    key="switch"
                    onClick={() => setMetric(isValue ? 'level' : 'value')}
                    role="switch"
                    aria-checked={isValue}
                    aria-label="Show inventory value instead of units"
                    className="relative w-11 h-6 rounded-full bg-indigo-500 flex-shrink-0 mx-1 transition-colors outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
                  >
                    <span
                      className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white shadow transition-transform ${
                        isValue ? 'translate-x-5' : 'translate-x-0'
                      }`}
                    />
                  </button>,
                ]
              : control;
          })}
        </div>
      </div>

      {/* ── Chart ── */}
      <p className="text-[12px] text-gray-500 dark:text-slate-400 mt-3 mb-1">{meta.axis}</p>

      <div className="flex-1 min-h-[280px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 6, right: 10, left: 0, bottom: 0 }}
          >
            <defs>
              {INVENTORY_CATEGORIES.map((c, i) => (
                <linearGradient key={c.key} id={GRADIENT_IDS[i]} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={CHART_CATEGORICAL[i]} stopOpacity={0.14} />
                  <stop offset="95%" stopColor={CHART_CATEGORICAL[i]} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>

            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={dark ? '#1e293b' : '#e2e8f0'} />
            <XAxis
              dataKey="name"
              axisLine={false}
              tickLine={false}
              tick={{ fill: dark ? '#94a3b8' : '#64748b', fontSize: 12 }}
              dy={10}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: dark ? '#94a3b8' : '#64748b', fontSize: 12 }}
              tickFormatter={(v) => formatInventoryMetric(v, metric, { compact: true })}
              width={isValue ? 56 : 44}
            />
            <Tooltip
              content={<TrendTooltip metric={metric} />}
              cursor={{ stroke: dark ? '#475569' : '#94a3b8', strokeWidth: 1 }}
            />
            <Legend verticalAlign="bottom" height={36} iconType="circle" />

            {INVENTORY_CATEGORIES.map((c, i) => (
              <Area
                key={c.key}
                type="monotone"
                dataKey={c.key}
                name={c.name}
                stroke={CHART_CATEGORICAL[i]}
                strokeWidth={3}
                fillOpacity={1}
                fill={`url(#${GRADIENT_IDS[i]})`}
                activeDot={{ r: 4, strokeWidth: 2, stroke: dark ? '#0f172a' : '#ffffff' }}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default InventoryTrendChart;
