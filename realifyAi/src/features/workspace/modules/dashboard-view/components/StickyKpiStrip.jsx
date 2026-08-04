import React from 'react';

/**
 * Condensed KPI ribbon that pins to the top of the scroll area once the full KPI
 * grid has scrolled out of view, so the numbers stay visible while browsing
 * tables and charts.
 *
 * Structure is deliberately the same as the AI view's CompactKpiStrip: a
 * zero-height sticky shell holding an absolutely-positioned band that bleeds past
 * the scroll container's padding. The previous version animated `max-height` with
 * `overflow-hidden`, which made the shell a clip boundary — so the cards' bottom
 * corners were sliced off and the ribbon read as cut in half. Animating opacity
 * on an unclipped, absolutely-positioned band cannot cut anything off.
 *
 * What this strip adds over the AI view's: these five cards are the dashboard's
 * navigation, so the current domain is marked and clicking one switches to it.
 */

/* Matches StatCard's `metric` selected treatment, so the ribbon and the expanded
   grid mark the current domain the same way. */
const SELECTED =
  'bg-gradient-to-r from-slate-900 to-slate-800 ring-1 ring-slate-900 ' +
  'dark:from-slate-100 dark:to-slate-200 dark:ring-slate-100';

const UNSELECTED =
  'bg-white dark:bg-slate-900 hover:bg-gray-50 dark:hover:bg-slate-800';

const StickyKpiStrip = ({
  kpiIsSticky,
  statsData,
  activeDomain,
  onSelectDomain,
  onDashboardClick,
}) => (
  <div className="sticky top-0 z-50 h-0 overflow-visible pointer-events-none">
    <div
      className={`absolute -left-2 -right-2 -top-2 sm:-left-2.5 sm:-right-2.5 sm:-top-2.5 bg-white dark:bg-[#030712] px-2 pt-2 pb-2 sm:px-2.5 sm:pt-2.5 shadow-[0_4px_12px_-6px_rgba(15,23,42,0.25)] transition-opacity duration-200 ${
        kpiIsSticky ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
      }`}
    >
      <div className="flex items-center gap-2 rounded-2xl border border-[#e2e8f0] dark:border-slate-700 bg-gray-100 dark:bg-slate-800 p-1.5 shadow-sm">
        <div className="grid flex-1 min-w-0 grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-1.5">
          {statsData.map((stat) => {
            const isSelected = stat.domainKey === activeDomain;

            return (
              <button
                key={stat.domainKey}
                type="button"
                onClick={() => onSelectDomain?.(stat.domainKey)}
                aria-current={isSelected ? 'true' : undefined}
                aria-label={`${stat.title} ${stat.value}${isSelected ? ' — current view' : ''}`}
                className={`min-w-0 rounded-xl px-3 py-1.5 flex flex-col items-center justify-center shadow-2xs cursor-pointer transition-colors ${
                  isSelected ? SELECTED : UNSELECTED
                }`}
              >
                <span
                  /* gray-500, not gray-400: at 8.5px uppercase the lighter grey
                     measured 2.54:1 on white, which is what made these labels
                     hard to pick out. */
                  className={`w-full truncate text-center text-[8.5px] font-bold uppercase tracking-widest ${
                    isSelected
                      ? 'text-slate-300 dark:text-slate-600'
                      : 'text-gray-500 dark:text-slate-400'
                  }`}
                >
                  {stat.title}
                </span>
                <div className="flex items-baseline gap-1.5">
                  <span
                    className={`text-[14px] font-bold leading-tight ${
                      isSelected ? 'text-white dark:text-gray-900' : 'text-gray-900 dark:text-white'
                    }`}
                  >
                    {stat.value}
                  </span>
                  <span
                    className={`text-[10px] font-bold ${
                      isSelected
                        ? stat.isPositive
                          ? 'text-emerald-400 dark:text-emerald-600'
                          : 'text-rose-400 dark:text-rose-600'
                        : stat.isPositive
                          ? 'text-emerald-500'
                          : 'text-rose-500'
                    }`}
                  >
                    {stat.change}
                  </span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Toggle reads "on" here — this *is* the dashboard view, so clicking it
            goes back to the AI view. */}
        <div className="hidden sm:flex flex-shrink-0 items-center gap-2 border-l border-gray-200 dark:border-slate-700 pl-3 pr-2">
          <span className="whitespace-nowrap text-[11px] font-bold text-gray-500 dark:text-slate-400">
            Dashboard
          </span>
          <button
            onClick={onDashboardClick}
            aria-label="Switch to AI view"
            className="relative inline-flex h-5 w-9 flex-shrink-0 items-center rounded-full bg-gray-900 dark:bg-slate-100 p-0.5 transition-colors cursor-pointer hover:opacity-80"
          >
            <span className="inline-block h-4 w-4 transform rounded-full bg-white dark:bg-gray-900 shadow-xs transition-transform translate-x-4" />
          </button>
        </div>
      </div>
    </div>
  </div>
);

export default StickyKpiStrip;
