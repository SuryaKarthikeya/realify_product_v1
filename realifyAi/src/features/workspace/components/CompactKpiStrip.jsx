import React from 'react';

/**
 * The ribbon is one row, always. It pins over the page while the user works the
 * table below, so a second row does not read as more information — it covers the
 * content they scrolled down to reach. Enforced here rather than trusting every
 * caller to slice.
 */
const MAX_KPIS = 5;

/**
 * Condensed KPI ribbon that pins to the top of the scroll area once the full KPI
 * grid has scrolled out of view, so the numbers stay readable while working the
 * Actions table.
 *
 * It always mirrors whatever the grid above it is showing: the five domain KPIs
 * while none is selected, or the open domain's sub-KPIs once one is.
 *
 * Layout: a zero-height sticky shell holds an absolutely-positioned band that
 * bleeds past the scroll container's padding on all sides. That padding is not a
 * clip boundary, so without the bleed rows would stay visible in the gap above
 * the ribbon as they scrolled under it.
 */
const CompactKpiStrip = ({ visible, kpis, onKpiClick, onDashboardClick }) => {
  // Only the domain-level cards drill down; sub-KPIs have nowhere to go.
  const Card = onKpiClick ? 'button' : 'div';

  return (
    <div className="sticky top-0 z-40 h-0 overflow-visible pointer-events-none">
      <div
        className={`absolute -left-2 -right-2 -top-2 sm:-left-2.5 sm:-right-2.5 sm:-top-2.5 bg-white dark:bg-[#030712] px-2 pt-2 pb-2 sm:px-2.5 sm:pt-2.5 shadow-[0_4px_12px_-6px_rgba(15,23,42,0.25)] transition-opacity duration-200 ${
          visible ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
      >
        {/* Mirrors the page container so the ribbon lines up with the cards below */}
        <div className="mx-auto max-w-[1600px] px-3 sm:px-4">
          <div className="flex items-center gap-2 rounded-2xl border border-[#e2e8f0] dark:border-slate-700 bg-gray-100 dark:bg-slate-800 p-1.5 shadow-sm">
            <div className="grid flex-1 min-w-0 grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-1.5">
              {kpis.slice(0, MAX_KPIS).map((kpi, i) => (
                <Card
                  /* Index, never the title. Sub-stat cards carry no `key` field,
                     so a title-derived key made all five loading placeholders
                     key on '…' at once. React's reconciler maps children by key,
                     duplicates collapse to one entry, and the four it loses are
                     never unmounted — they stay in the DOM as dead '…' cards,
                     four more on every tab switch. The ribbon is a fixed row of
                     positional slots that never reorder, so the index is the
                     correct identity (same as the expanded grid below it). */
                  key={i}
                  {...(onKpiClick ? { type: 'button', onClick: () => onKpiClick(kpi) } : {})}
                  className={`min-w-0 rounded-xl bg-white dark:bg-slate-900 px-3 py-1.5 flex flex-col items-center justify-center shadow-2xs ${
                    onKpiClick
                      ? 'cursor-pointer transition-colors hover:bg-gray-50 dark:hover:bg-slate-800'
                      : ''
                  }`}
                >
                  <span className="w-full truncate text-center text-[8.5px] font-bold uppercase tracking-widest text-gray-400 dark:text-slate-500">
                    {kpi.title}
                  </span>
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-[14px] font-bold leading-tight text-gray-900 dark:text-white">
                      {kpi.value}
                    </span>
                    <span
                      className={`text-[10px] font-bold ${
                        kpi.isPositive ? 'text-emerald-500' : 'text-rose-500'
                      }`}
                    >
                      {kpi.change}
                    </span>
                  </div>
                </Card>
              ))}
            </div>

            <div className="hidden sm:flex flex-shrink-0 items-center gap-2 border-l border-gray-200 dark:border-slate-700 pl-3 pr-2">
              <span className="whitespace-nowrap text-[11px] font-bold text-gray-500 dark:text-slate-400">
                Dashboard
              </span>
              <button
                onClick={onDashboardClick}
                className="relative inline-flex h-5 w-9 flex-shrink-0 items-center rounded-full bg-gray-200 dark:bg-slate-700 p-0.5 transition-colors cursor-pointer hover:bg-gray-300 dark:hover:bg-slate-600"
              >
                <span className="inline-block h-4 w-4 transform rounded-full bg-white dark:bg-slate-900 shadow-xs transition-transform translate-x-0" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompactKpiStrip;
