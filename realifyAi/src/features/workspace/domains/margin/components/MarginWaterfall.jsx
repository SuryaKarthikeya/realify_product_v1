import React, { useState } from 'react';
import { formatCompactMoney } from '@/utils/formatters';
import { buildWaterfall } from '@/features/workspace/domains/margin/data/marginWaterfallData';

/** Height of the plot area. Bars are positioned against this in percentages. */
const PLOT_HEIGHT = 320;

const KIND_STYLES = {
  total: { bar: 'bg-blue-500', text: 'text-blue-600 dark:text-blue-400', dot: 'bg-blue-500' },
  deduction: { bar: 'bg-[#dd6b55]', text: 'text-[#c4553f] dark:text-red-400', dot: 'bg-[#dd6b55]' },
  net: { bar: 'bg-emerald-600', text: 'text-emerald-700 dark:text-emerald-400', dot: 'bg-emerald-600' },
};

/**
 * Deductions carry two decimals so small lines stay distinguishable (-$0.86K vs
 * -$1.05K); subtotals read as rounded headlines.
 */
const formatStageValue = (bar) =>
  bar.kind === 'deduction'
    ? `-$${(Math.abs(bar.value) / 1000).toFixed(2)}K`
    : formatCompactMoney(bar.value);

/**
 * Margin waterfall — revenue on the left, net profit on the right, every cost
 * that separates them in between.
 *
 * Built with positioned divs rather than a charting library: the floating bars,
 * the dashed connectors that carry the running total across each gap, and the
 * per-bar labels are all easier to place exactly this way, and it keeps the
 * component dependency-free.
 */
const MarginWaterfall = () => {
  const { bars, max, net } = buildWaterfall();
  const [openStage, setOpenStage] = useState(null);

  const pct = (value) => `${(value / max) * 100}%`;
  const active = bars.find((b) => b.key === openStage);

  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4 sm:p-5">
      <h4 className="text-sm font-bold text-gray-900 dark:text-slate-100">Margin Waterfall</h4>
      <p className="text-[12px] text-gray-500 dark:text-slate-400 mt-1">
        How {formatCompactMoney(bars[0].value)} of revenue becomes {formatCompactMoney(net)} of net
        profit. Click any stage to see what&apos;s driving it.
      </p>

      {/* Legend */}
      <div className="flex items-center gap-5 mt-4 mb-2 flex-wrap">
        {[
          { label: 'Running total', kind: 'total' },
          { label: 'Deduction', kind: 'deduction' },
          { label: 'Net profit', kind: 'net' },
        ].map((item) => (
          <div key={item.kind} className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${KIND_STYLES[item.kind].dot}`} />
            <span className="text-[11.5px] font-medium text-gray-600 dark:text-slate-400">{item.label}</span>
          </div>
        ))}
      </div>

      {/* Chart — scrolls horizontally on narrow screens rather than crushing bars */}
      <div className="overflow-x-auto -mx-1 px-1">
        <div className="min-w-[860px]">
          {/* Plot area. pt leaves room for the value label above the tallest bar. */}
          <div className="relative pt-7" style={{ height: PLOT_HEIGHT + 28 }}>

            {/* Connectors sit behind the bars, each at the running total that
                carries from one stage into the next. */}
            <div className="absolute inset-x-0 bottom-0 z-0" style={{ height: PLOT_HEIGHT }}>
              {bars.slice(0, -1).map((bar, i) => {
                const exitLevel = bar.kind === 'deduction' ? bar.base : bar.top;
                const step = 100 / bars.length;
                return (
                  <div
                    key={`link-${bar.key}`}
                    className="absolute border-t border-dashed border-gray-300 dark:border-slate-700"
                    style={{
                      bottom: pct(exitLevel),
                      left: `${(i + 0.5) * step}%`,
                      width: `${step}%`,
                    }}
                  />
                );
              })}
            </div>

            {/* Bars */}
            <div className="relative z-10 flex items-end h-full">
              {bars.map((bar) => {
                const style = KIND_STYLES[bar.kind];
                const isOpen = openStage === bar.key;
                return (
                  <button
                    key={bar.key}
                    onClick={() => setOpenStage(isOpen ? null : bar.key)}
                    aria-expanded={isOpen}
                    className="relative flex-1 h-full group focus:outline-none"
                    title={`${bar.label} — ${formatStageValue(bar)}`}
                  >
                    {/* Value label, pinned just above the bar's top edge */}
                    <span
                      className={`absolute left-0 right-0 text-center text-[11.5px] font-bold whitespace-nowrap ${style.text}`}
                      style={{ bottom: `calc(${pct(bar.top)} + 6px)` }}
                    >
                      {formatStageValue(bar)}
                    </span>

                    <span
                      className={`absolute left-1/2 -translate-x-1/2 w-[46%] rounded-[2px] transition-all ${style.bar} ${
                        isOpen ? 'ring-2 ring-offset-1 ring-gray-900/40 dark:ring-white/40' : 'group-hover:brightness-110'
                      }`}
                      style={{
                        bottom: pct(bar.base),
                        // Floor at 3px so sub-$1K deductions stay visible.
                        height: `max(3px, ${pct(Math.abs(bar.value))})`,
                      }}
                    />
                  </button>
                );
              })}
            </div>
          </div>

          {/* Axis + labels */}
          <div className="border-t border-gray-200 dark:border-slate-700 flex">
            {bars.map((bar) => (
              <div key={`label-${bar.key}`} className="flex-1 px-1 pt-2.5">
                <p
                  className={`text-[11px] text-center leading-tight ${
                    openStage === bar.key
                      ? 'font-bold text-gray-900 dark:text-white'
                      : 'font-medium text-gray-600 dark:text-slate-400'
                  }`}
                >
                  {bar.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Drill-down for the selected stage, else the hint */}
      {active ? (
        <div className="mt-4 rounded-xl border border-gray-100 dark:border-slate-800 bg-gray-50/70 dark:bg-slate-800/40 p-4 animate-in fade-in slide-in-from-top-1 duration-150">
          <div className="flex items-start justify-between gap-3 mb-3">
            <div>
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${KIND_STYLES[active.kind].dot}`} />
                <p className="text-[13px] font-bold text-gray-900 dark:text-white">{active.label}</p>
                <span className={`text-[12px] font-bold ${KIND_STYLES[active.kind].text}`}>
                  {formatStageValue(active)}
                </span>
              </div>
              <p className="text-[11.5px] text-gray-500 dark:text-slate-400 mt-1">{active.note}</p>
            </div>
            <button
              onClick={() => setOpenStage(null)}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-slate-200 transition-colors flex-shrink-0"
              aria-label="Close breakdown"
            >
              <i className="fa-solid fa-xmark text-[13px]" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
            {active.contributors.map((c) => (
              <div
                key={c.label}
                className="rounded-lg bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 px-3 py-2.5"
              >
                <p className="text-[10.5px] text-gray-500 dark:text-slate-400 truncate" title={c.label}>
                  {c.label}
                </p>
                <div className="flex items-baseline gap-1.5 mt-0.5">
                  {c.value !== null && (
                    <span className="text-[13px] font-bold text-gray-900 dark:text-white">
                      {formatCompactMoney(c.value)}
                    </span>
                  )}
                  <span className={`text-[11.5px] font-bold ${c.value === null ? 'text-gray-900 dark:text-white' : 'text-gray-400 dark:text-slate-500'}`}>
                    {c.share}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="mt-4 rounded-xl bg-gray-50 dark:bg-slate-800/40 border border-gray-100 dark:border-slate-800 px-4 py-3">
          <p className="text-[11.5px] text-gray-600 dark:text-slate-400">
            <span className="font-bold text-gray-800 dark:text-slate-200">Tip:</span> click any bar
            above — Revenue, COGS, Gross Profit, or any other stage — to see its biggest contributors.
          </p>
        </div>
      )}
    </div>
  );
};

export default MarginWaterfall;
