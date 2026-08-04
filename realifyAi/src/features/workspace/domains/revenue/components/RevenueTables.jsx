import React, { useRef, useState, useEffect } from 'react';
import SectionHeading from '@/components/data-display/SectionHeading';
import { TD, TR, TableHead } from '@/components/data-display/DenseTable';
import {
  salesTopMovers, salesBottomMovers, salesRevenueData,
  CHAN_STYLE, SPARKLINE_DATA, CARD_COLORS,
} from '@/features/workspace/domains/revenue/data/revenueDashboardData';
import useProductNavigation from '@/hooks/useProductNavigation';
import { dashboardPath } from '@/features/workspace/workspaceRoutes';

const ProductSparkline = ({ idx }) => {
  const raw = SPARKLINE_DATA[idx % SPARKLINE_DATA.length];
  const positive = raw[raw.length - 1] >= raw[0];
  const min = Math.min(...raw), max = Math.max(...raw), range = max - min || 1;
  const W = 80, H = 28;
  const pts = raw.map((v, i) => `${(i / (raw.length - 1)) * W},${H - ((v - min) / range) * (H - 4) - 2}`).join(' ');
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} fill="none">
      <polyline points={pts} stroke={positive ? '#22c55e' : '#ef4444'} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
};

const RevenueTables = () => {
  const { goToProduct, buildFallbackWatchlistItem, NO_SPECIFIC_INSIGHTS } = useProductNavigation();
  const navToProduct = (name, sku, price) => goToProduct({
    name, sku, price, image: null,
    description: `${name} is a key product driving your sales performance.`,
    kpiGroups: [{ label: 'Sales', color: 'text-blue-600 dark:text-blue-400', bgColor: 'bg-blue-50 dark:bg-blue-900/10', kpis: [{ label: 'Total Revenue', value: '—' }, { label: 'Units Sold', value: '—' }, { label: 'Avg Price', value: '—' }, { label: 'Buy Box %', value: '—' }] }],
    insights: NO_SPECIFIC_INSIGHTS,
    watchlistItem: buildFallbackWatchlistItem(name, sku, { velocity: '—', subtext: '' }),
  }, dashboardPath('sales'));

  // ── Product card carousel (Total Revenue) ──────────────────────────────────
  const carouselRef = useRef(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);
  useEffect(() => {
    const el = carouselRef.current;
    if (!el) return;
    const STEP = 252;
    let timer;
    const checkArrows = () => {
      setCanScrollLeft(el.scrollLeft > 2);
      setCanScrollRight(el.scrollLeft + el.clientWidth < el.scrollWidth - 2);
    };
    const tick = () => {
      if (!el) return;
      if (el.scrollLeft + el.clientWidth >= el.scrollWidth - 4) {
        el.scrollTo({ left: 0, behavior: 'smooth' });
      } else {
        el.scrollBy({ left: STEP, behavior: 'smooth' });
      }
    };
    const start = () => { timer = setInterval(tick, 3000); };
    const stop = () => clearInterval(timer);
    start();
    el.addEventListener('mouseenter', stop);
    el.addEventListener('mouseleave', start);
    el.addEventListener('scroll', checkArrows);
    checkArrows();
    return () => {
      stop();
      el.removeEventListener('mouseenter', stop);
      el.removeEventListener('mouseleave', start);
      el.removeEventListener('scroll', checkArrows);
    };
  }, []);
  const scrollCarousel = (dir) => carouselRef.current?.scrollBy({ left: dir * 252, behavior: 'smooth' });

  return (
    <div className="space-y-5">

      {/* ── Total Revenue ── */}
      <div>
        <SectionHeading title="Total Revenue — by Product" />
        <div className="relative">
          {canScrollLeft && (
            <button
              onClick={() => scrollCarousel(-1)}
              className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-8 h-8 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-full shadow-sm flex items-center justify-center text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors -ml-3"
            >
              <i className="fa-solid fa-chevron-left text-[10px]" />
            </button>
          )}
          <div ref={carouselRef} className="flex gap-3 overflow-x-auto pb-1 hide-scrollbar">
            {salesRevenueData.map((r, i) => {
              const chanStyle = CHAN_STYLE[r.channel] || { bg: 'bg-gray-100', text: 'text-gray-600' };
              return (
                <div key={i} onClick={() => navToProduct(r.name, r.sku, r.price)} className="flex-shrink-0 w-[240px] bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4 flex flex-col gap-3 cursor-pointer hover:border-gray-300 dark:hover:border-slate-600 transition-colors">
                  <div className="flex items-start gap-2">
                    <div className={`w-10 h-10 rounded-xl ${CARD_COLORS[i % CARD_COLORS.length]} flex items-center justify-center flex-shrink-0`}>
                      <span className="text-sm font-bold text-gray-500">{r.name[0]}</span>
                    </div>
                    <p className="text-xs font-bold text-gray-900 dark:text-slate-100 leading-tight line-clamp-2 flex-1 min-w-0">{r.name}</p>
                  </div>
                  <span className={`self-start text-[10px] font-semibold px-2 py-0.5 rounded-full ${chanStyle.bg} ${chanStyle.text}`}>{r.channel}</span>
                  <div className="grid grid-cols-3 gap-x-1">
                    <div><p className="text-[9px] text-gray-400 dark:text-slate-500">Units</p><p className="text-[11px] font-semibold text-gray-800 dark:text-slate-200">{r.units}</p></div>
                    <div><p className="text-[9px] text-gray-400 dark:text-slate-500">Price</p><p className="text-[11px] font-semibold text-gray-800 dark:text-slate-200">{r.price}</p></div>
                    <div><p className="text-[9px] text-gray-400 dark:text-slate-500">Revenue</p><p className="text-[11px] font-semibold text-gray-800 dark:text-slate-200 truncate">{r.revenue}</p></div>
                  </div>
                  <div className="flex items-end justify-between mt-auto pt-1.5 border-t border-gray-50 dark:border-slate-800">
                    <div>
                      <p className="text-[9px] text-gray-400 dark:text-slate-500">Net</p>
                      <p className="text-sm font-bold text-green-600 dark:text-green-400">{r.net}</p>
                    </div>
                    <ProductSparkline idx={i} />
                  </div>
                </div>
              );
            })}
          </div>
          {canScrollRight && (
            <button
              onClick={() => scrollCarousel(1)}
              className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-8 h-8 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-full shadow-sm flex items-center justify-center text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors -mr-3"
            >
              <i className="fa-solid fa-chevron-right text-[10px]" />
            </button>
          )}
        </div>
      </div>

      {/* ── Units Sold + Total Orders side by side ── */}
      {/* <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div className="min-w-0">
          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl overflow-hidden">
            <div className="px-4 py-2.5 border-b border-gray-100 dark:border-slate-800 bg-gray-50 dark:bg-slate-800">
              <p className="text-sm font-bold text-gray-900 dark:text-slate-100">Units Sold — by Channel</p>
            </div>
            <div className="overflow-auto max-h-[300px]">
              <table className="w-full">
                <TableHead cols={['SKU', 'Product', 'Top Channel', 'Units', 'Total']} />
                <tbody>
                  {salesUnitsData.map((r, i) => {
                    const chMap = { amazon: r.amazon, shopify: r.shopify, tiktok: r.tiktok, ebay: r.ebay, google: r.google };
                    const topCh = Object.entries(chMap).sort((a, b) => b[1] - a[1])[0];
                    return (
                      <TR key={i} onClick={() => navToProduct(r.name, r.sku)}>
                        <TD className="font-sans text-gray-400 dark:text-slate-500">{r.sku}</TD>
                        <TD className="font-semibold text-gray-900 dark:text-slate-100 max-w-[130px] truncate">{r.name}</TD>
                        <TD className="text-gray-500 dark:text-slate-400 capitalize">{topCh[0]}</TD>
                        <TD className="text-gray-700 dark:text-slate-300">{topCh[1].toLocaleString()}</TD>
                        <TD className="font-bold text-gray-900 dark:text-slate-100">{r.total.toLocaleString()}</TD>
                      </TR>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <div className="min-w-0">
          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl overflow-hidden">
            <div className="px-4 py-2.5 border-b border-gray-100 dark:border-slate-800 bg-gray-50 dark:bg-slate-800">
              <p className="text-sm font-bold text-gray-900 dark:text-slate-100">Total Orders — by Channel</p>
            </div>
            <div className="overflow-auto max-h-[300px]">
              <table className="w-full">
                <TableHead cols={['Channel', 'Orders', 'Units', 'AOV', 'Revenue', '% of Total']} />
                <tbody>
                  {salesOrdersData.map((r, i) => (
                    <TR key={i}>
                      <TD className="font-semibold text-gray-900 dark:text-slate-100">{r.channel}</TD>
                      <TD className="text-gray-700 dark:text-slate-300">{r.orders > 0 ? r.orders : '—'}</TD>
                      <TD className="text-gray-700 dark:text-slate-300">{r.units > 0 ? r.units.toLocaleString() : '—'}</TD>
                      <TD className="text-gray-700 dark:text-slate-300">{r.aov}</TD>
                      <TD className="font-semibold text-gray-900 dark:text-slate-100">{r.revenue}</TD>
                      <TD>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-1.5 bg-gray-100 dark:bg-slate-700 rounded-full overflow-hidden min-w-[40px]">
                            <div className="h-full bg-gray-700 dark:bg-slate-300 rounded-full" style={{ width: r.pct }} />
                          </div>
                          <span className="text-[10px] font-semibold text-gray-500 dark:text-slate-400 whitespace-nowrap">{r.pct}</span>
                        </div>
                      </TD>
                    </TR>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div> */}

      {/* ── AOV table ── */}
      {/* <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div className="min-w-0">
          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl overflow-hidden">
            <div className="px-4 py-2.5 border-b border-gray-100 dark:border-slate-800 bg-gray-50 dark:bg-slate-800">
              <p className="text-sm font-bold text-gray-900 dark:text-slate-100">Avg Order Value — by Product</p>
            </div>
            <div className="overflow-auto max-h-[300px]">
              <table className="w-full">
                <TableHead cols={['SKU', 'Product', 'Orders', 'AOV', 'vs Avg ($302)', '±%']} />
                <tbody>
                  {salesAovData.map((r, i) => (
                    <TR key={i} onClick={() => navToProduct(r.name, r.sku)}>
                      <TD className="font-sans text-gray-400 dark:text-slate-500">{r.sku}</TD>
                      <TD className="font-semibold text-gray-900 dark:text-slate-100 max-w-[130px] truncate">{r.name}</TD>
                      <TD className="text-gray-600 dark:text-slate-400">{r.orders}</TD>
                      <TD className="font-bold text-gray-900 dark:text-slate-100">{r.aov}</TD>
                      <TD className={r.positive ? 'font-semibold text-green-600 dark:text-green-400' : 'font-semibold text-red-500 dark:text-red-400'}>{r.vsAvg}</TD>
                      <TD className={r.positive ? 'font-semibold text-green-600 dark:text-green-400' : 'text-gray-400 dark:text-slate-500'}>{r.pctVsAvg}</TD>
                    </TR>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div> */}

      {/* ── Movers Overview (full width combined) ── */}
      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-100 dark:border-slate-800 bg-gray-50 dark:bg-slate-800 flex items-center gap-2">
          <i className="fa-solid fa-chart-bar text-gray-600 dark:text-slate-300 text-sm" />
          <p className="text-sm font-bold text-gray-900 dark:text-slate-100">Movers Overview (Revenue)</p>
        </div>
        <div className="grid grid-cols-1 xl:grid-cols-2 divide-y xl:divide-y-0 xl:divide-x divide-gray-100 dark:divide-slate-800">
          {/* Top Movers */}
          <div>
            <div className="px-4 py-2 flex items-center gap-2 border-b border-gray-50 dark:border-slate-800/60">
              <i className="fa-solid fa-arrow-trend-up text-green-500 text-xs" />
              <p className="text-xs font-bold text-green-600 dark:text-green-400">Top Movers</p>
            </div>
            <table className="w-full">
              <TableHead cols={['#', 'Product', 'SKU', 'Revenue', 'Change ▲']} />
              <tbody>
                {salesTopMovers.map((item, i) => (
                  <TR key={i} onClick={() => navToProduct(item.name, item.sku)}>
                    <TD>
                      <span className="inline-flex w-5 h-5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full items-center justify-center text-[10px] font-bold">{i + 1}</span>
                    </TD>
                    <TD className="font-semibold text-gray-900 dark:text-slate-100">{item.name}</TD>
                    <TD className="font-sans text-[10px] text-gray-500 dark:text-slate-400">{item.sku}</TD>
                    <TD className="font-semibold text-gray-900 dark:text-slate-100">{item.revenue}</TD>
                    <TD className="font-bold text-green-600 dark:text-green-400">{item.change}</TD>
                  </TR>
                ))}
              </tbody>
            </table>
          </div>
          {/* Bottom Movers */}
          <div>
            <div className="px-4 py-2 flex items-center gap-2 border-b border-gray-50 dark:border-slate-800/60">
              <i className="fa-solid fa-arrow-trend-down text-red-500 text-xs" />
              <p className="text-xs font-bold text-red-600 dark:text-red-400">Bottom Movers</p>
            </div>
            <table className="w-full">
              <TableHead cols={['#', 'Product', 'SKU', 'Revenue', 'Change ▼']} />
              <tbody>
                {salesBottomMovers.map((item, i) => (
                  <TR key={i} onClick={() => navToProduct(item.name, item.sku)}>
                    <TD>
                      <span className="inline-flex w-5 h-5 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-full items-center justify-center text-[10px] font-bold">{i + 1}</span>
                    </TD>
                    <TD className="font-semibold text-gray-900 dark:text-slate-100">{item.name}</TD>
                    <TD className="font-sans text-[10px] text-gray-500 dark:text-slate-400">{item.sku}</TD>
                    <TD className="font-semibold text-gray-900 dark:text-slate-100">{item.revenue}</TD>
                    <TD className="font-bold text-red-500 dark:text-red-400">{item.change}</TD>
                  </TR>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

    </div>
  );
};

export default RevenueTables;
