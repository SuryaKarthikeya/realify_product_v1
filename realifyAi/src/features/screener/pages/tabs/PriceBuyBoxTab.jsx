import React, { useState } from 'react';
import StatCard from '@/components/data-display/StatCard';
import KPIDetailModal from '@/features/screener/components/kpi-detail/KPIDetailModal';
import { useFilterStore } from '@/store/useFilterStore';
import {
  PieChart, Pie, Cell, Tooltip as RechartsTooltip, ResponsiveContainer, Legend,
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  BarChart, Bar,
} from 'recharts';
import { promoList } from '@/features/screener/data/screenerData';
import CompetitorsAnalysisSection from '@/features/screener/components/price-buybox/CompetitorsAnalysisSection';
import ScreenerAlertsPanel from '@/features/screener/components/ScreenerAlertsPanel';
import AnalyticsModal from '@/features/screener/components/AnalyticsModal';
import ClickToExpand from '@/components/ui/ClickToExpand';
import DeepDiveTabBar from '@/components/navigation/DeepDiveTabBar';
import BaseAreaChart from '@/components/data-display/charts/BaseAreaChart';
import useModalToggle from '@/hooks/useModalToggle';
import { kpis } from '@/features/screener/data/priceBuyBoxKpis';
import PriceBuyBoxExpandContent from '@/features/screener/components/expand-content/PriceBuyBoxExpandContent';
import ScreenerExpandModal from '@/features/screener/components/ScreenerExpandModal';


const PriceBuyBoxTab = () => {
  const [selectedKpiIdx, setSelectedKpiIdx] = useState(0);
  const kpiDetailModal = useModalToggle();
  const dateRange = useFilterStore(s => s.dateRange);
  const [priceDiveTab, setPriceDiveTab] = useState('kpi');
  const [priceExpandModal, setPriceExpandModal] = useState(null);
  const [activePromo, setActivePromo] = useState(1);
  const [activeModal, setActiveModal] = useState({ isOpen: false, data: null });

  const selectedKpi = kpis[Math.min(selectedKpiIdx, kpis.length - 1)];

  const handleDetailedView = () => {
    if (priceDiveTab === 'kpi') {
      setActiveModal({ isOpen: true, data: selectedKpi?.deepDive });
    } else if (priceDiveTab === 'charts') {
      setPriceExpandModal('price-chart-trend7d');
    } else {
      setPriceExpandModal(priceDiveTab);
    }
  };

  return (
    <>
      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start mb-6">
        {/* Left column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Stat Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {kpis.map((kpi, idx) => (
              <StatCard
                key={idx}
                title={kpi.title}
                value={kpi.value}
                change={kpi.change}
                subtext={kpi.subtext}
                isPositive={kpi.isPositive !== false}
                onClick={() => { setSelectedKpiIdx(idx); kpiDetailModal.open(kpi); }}
              />
            ))}
          </div>

          {/* Insights */}
          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm p-5">
            <h4 className="font-bold text-gray-900 dark:text-slate-100 mb-4">Insights</h4>
            <div className="space-y-2.5">
              <div className="p-3.5 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-700">
                <p className="text-sm font-semibold text-gray-900 dark:text-slate-100">Price Drop Detected</p>
                <p className="text-xs text-gray-600 dark:text-slate-400 mt-0.5">TechMaster dropped Wireless Earbuds to $42.99 (-12%)</p>
              </div>
              <div className="p-3.5 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-700">
                <p className="text-sm font-semibold text-gray-900 dark:text-slate-100">Buy Box Lost</p>
                <p className="text-xs text-gray-600 dark:text-slate-400 mt-0.5">USB-C Hub: competitor undercutting at $27.99 — match or hold position</p>
              </div>
              <div className="p-3.5 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-700">
                <p className="text-sm font-semibold text-gray-900 dark:text-slate-100">MAP Compliance</p>
                <p className="text-xs text-gray-600 dark:text-slate-400 mt-0.5">3 ASINs need immediate price adjustment to stay compliant</p>
              </div>
            </div>
          </div>

          {/* Mobile alerts (xl:hidden for price tab) */}
          <div className="xl:hidden mb-6">
            <ScreenerAlertsPanel />
          </div>

          {/* Tab content */}
          <div className="space-y-6">
            <CompetitorsAnalysisSection />
          </div>
        </div>

        {/* Right column */}
        <div className="lg:col-span-1 space-y-4">
          {/* Deep dive panel */}
          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
            <div className="flex items-center px-4 py-2 border-b border-gray-100 dark:border-slate-800/60">
              <button
                onClick={handleDetailedView}
                className="flex items-center gap-1.5 text-[11px] font-bold text-gray-500 dark:text-slate-400 hover:text-brand dark:hover:text-gray-200 transition-colors group"
              >
                <i className="fa-solid fa-arrow-up-right-from-square text-[9px] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform"></i>
                Detailed View
              </button>
            </div>

            {/* Price & Buy Box deep dive tabs */}
            <DeepDiveTabBar>
              {[
                { key: 'kpi', label: selectedKpi?.shortLabel || 'Price Delta' },
                { key: 'pricing-landscape', label: 'Landscape' },
                { key: 'price-distribution', label: 'Distribution' },
                { key: 'promotions', label: 'Promotions' },
                { key: 'price-monitoring', label: 'Monitoring' },
                { key: 'charts', label: 'Charts' },
              ].map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => setPriceDiveTab(key)}
                  className={`px-3 py-3 text-xs font-semibold transition whitespace-nowrap border-b-2 -mb-px ${
                    priceDiveTab === key
                      ? 'border-brand text-brand dark:text-gray-400 dark:border-gray-400'
                      : 'border-transparent text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-300'
                  }`}
                >
                  {label}
                </button>
              ))}
            </DeepDiveTabBar>
            <div className="flex flex-col" style={{ height: 290 }}>
              <div className="flex-1 overflow-y-auto">
                {priceDiveTab === 'kpi' && (
                  <div
                    className="h-full flex flex-col p-4 cursor-pointer group"
                    onClick={() => setActiveModal({ isOpen: true, data: selectedKpi?.deepDive })}
                  >
                    <div className="flex items-center justify-between px-1 mb-2">
                      <span className="text-xs font-semibold text-gray-700 dark:text-slate-300">{selectedKpi?.title}</span>
                      <span className="text-xs font-bold text-blue-600 dark:text-blue-400">{selectedKpi?.value}</span>
                    </div>
                    <div className="h-[180px] w-full pointer-events-none overflow-hidden">
                      <BaseAreaChart
                        data={selectedKpi?.chartData || []}
                        height={180}
                        areas={[{ key: 'val', name: selectedKpi?.title, color: selectedKpi?.chartColor || '#3b82f6' }]}
                        yAxisFormatter={(v) => `${v}`}
                        tooltipFormatter={(v, n) => [`${v}`, n]}
                      />
                    </div>
                    <ClickToExpand />
                  </div>
                )}
                {priceDiveTab === 'pricing-landscape' && (
                  <div className="p-3 space-y-1.5">
                    {[
                      { label: 'Market Avg Price', value: '$67.84', sub: '2,456 products', colorClass: 'text-blue-600 dark:text-blue-400' },
                      { label: 'Price Volatility', value: 'Medium', sub: '±12% weekly', colorClass: 'text-purple-600 dark:text-purple-400' },
                      { label: 'Your Position', value: '2nd', sub: 'of 47 competitors', colorClass: 'text-green-600 dark:text-green-400' },
                      { label: 'Avg Discount', value: '18%', sub: 'Across category', colorClass: 'text-orange-600 dark:text-orange-400' },
                    ].map((item, i) => (
                      <div key={i} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-slate-800/50 rounded-lg">
                        <div>
                          <p className="text-xs font-medium text-gray-700 dark:text-slate-300">{item.label}</p>
                          <p className="text-[10px] text-gray-400 dark:text-slate-500">{item.sub}</p>
                        </div>
                        <span className={`text-xs font-bold ${item.colorClass}`}>{item.value}</span>
                      </div>
                    ))}
                  </div>
                )}
                {priceDiveTab === 'price-distribution' && (
                  <div className="p-3 space-y-2">
                    {[
                      { label: 'Budget ($0-$30)', pct: 42, color: '#2563eb' },
                      { label: 'Mid-Range ($30-$80)', pct: 35, color: '#7c3aed' },
                      { label: 'Premium ($80-$150)', pct: 18, color: '#ea580c' },
                      { label: 'Luxury ($150+)', pct: 5, color: '#16a34a' },
                    ].map((item, i) => (
                      <div key={i} className="space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium text-gray-700 dark:text-slate-300 truncate">{item.label}</span>
                          <span className="text-xs font-bold ml-2" style={{ color: item.color }}>{item.pct}%</span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-1.5">
                          <div className="h-1.5 rounded-full" style={{ width: `${item.pct}%`, backgroundColor: item.color }}></div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {priceDiveTab === 'promotions' && (
                  <div className="p-3 space-y-2">
                    {promoList.map((promo) => (
                      <div key={promo.id} className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-slate-800/50 rounded-lg border border-gray-200 dark:border-slate-700">
                        <div className="w-7 h-7 bg-blue-50 dark:bg-blue-900/20 rounded-lg flex items-center justify-center shrink-0">
                          <i className={`fa-solid ${promo.icon} text-blue-500 dark:text-blue-400 text-xs`}></i>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-semibold text-gray-800 dark:text-slate-200 truncate">{promo.title}</p>
                          <p className="text-[10px] text-gray-500 dark:text-slate-400 truncate">{promo.type} • {promo.status}</p>
                        </div>
                        <span className="text-[10px] font-bold text-green-600 dark:text-green-400 shrink-0">{promo.avgDiscount}</span>
                      </div>
                    ))}
                  </div>
                )}
                {priceDiveTab === 'price-monitoring' && (
                  <div className="p-3 space-y-2">
                    {[
                      { name: 'Wireless Headphones', price: '$62.99', status: 'Buy Box', dotColor: 'bg-green-500', textColor: 'text-green-600 dark:text-green-400' },
                      { name: 'USB-C Fast Charger', price: '$24.99', status: 'Lost BB', dotColor: 'bg-red-500', textColor: 'text-red-600 dark:text-red-400' },
                      { name: 'Mech Gaming Keyboard', price: '$89.99', status: 'Buy Box', dotColor: 'bg-green-500', textColor: 'text-green-600 dark:text-green-400' },
                      { name: '4K Action Camera', price: '$149.99', status: 'Price Alert', dotColor: 'bg-orange-500', textColor: 'text-orange-600 dark:text-orange-400' },
                    ].map((item, i) => (
                      <div key={i} className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-slate-800/50 rounded-lg border border-gray-200 dark:border-slate-700">
                        <span className={`w-2 h-2 rounded-full shrink-0 ${item.dotColor}`}></span>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-semibold text-gray-800 dark:text-slate-200 truncate">{item.name}</p>
                          <p className={`text-[10px] font-medium ${item.textColor}`}>{item.status}</p>
                        </div>
                        <span className="text-xs font-bold text-gray-700 dark:text-slate-300 shrink-0">{item.price}</span>
                      </div>
                    ))}
                  </div>
                )}
                {priceDiveTab === 'charts' && (
                  <div className="p-3 space-y-2">
                    {[
                      { key: 'price-chart-trend7d', icon: 'fa-chart-line', title: '7 Day Price Trend', sub: 'Your price vs market & competitors' },
                      { key: 'price-chart-trend', icon: 'fa-chart-area', title: 'Price Trend Analysis', sub: '7-day brand comparison' },
                      { key: 'price-chart-buybox', icon: 'fa-trophy', title: 'Buy Box Win Rate', sub: 'Win rate by category' },
                    ].map((chart) => (
                      <button
                        key={chart.key}
                        onClick={() => setPriceExpandModal(chart.key)}
                        className="w-full flex items-center gap-3 p-3 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-200 dark:border-slate-700 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors group text-left"
                      >
                        <div className="w-8 h-8 bg-blue-50 dark:bg-blue-900/20 rounded-lg flex items-center justify-center shrink-0">
                          <i className={`fa-solid ${chart.icon} text-blue-500 dark:text-blue-400 text-xs`}></i>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-semibold text-gray-800 dark:text-slate-200 leading-tight">{chart.title}</p>
                          <p className="text-[10px] text-gray-500 dark:text-slate-400 mt-0.5">{chart.sub}</p>
                        </div>
                        <i className="fa-solid fa-expand text-[10px] text-gray-400 dark:text-slate-500 group-hover:text-gray-600 dark:group-hover:text-slate-300 shrink-0"></i>
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {priceDiveTab !== 'kpi' && priceDiveTab !== 'charts' && (
                <button
                  onClick={() => setPriceExpandModal(priceDiveTab)}
                  className="flex items-center justify-center gap-1 py-2 text-[10px] font-medium text-gray-400 hover:text-gray-700 dark:text-slate-500 dark:hover:text-gray-300 transition-colors border-t border-gray-100 dark:border-slate-800 shrink-0"
                >
                  <i className="fa-solid fa-expand text-[9px]"></i>
                  Click to expand
                </button>
              )}
            </div>
          </div>

          {/* Alerts panel */}
          <ScreenerAlertsPanel compact className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm p-4" />
        </div>
      </div>

      {/* Modals */}
      <AnalyticsModal
        isOpen={activeModal.isOpen}
        onClose={() => setActiveModal({ isOpen: false, data: null })}
        data={activeModal.data}
      />

      {/* Price & Buy Box Deep-Dive Expand Modal */}
      {priceExpandModal && (
        <ScreenerExpandModal
          onClose={() => setPriceExpandModal(null)}
          iconWrapClass="bg-blue-100 dark:bg-blue-900/30"
          iconClass={`${
                    priceExpandModal === 'pricing-landscape' ? 'fa-tags' :
                    priceExpandModal === 'price-distribution' ? 'fa-chart-pie' :
                    priceExpandModal === 'promotions' ? 'fa-gift' :
                    priceExpandModal === 'price-monitoring' ? 'fa-eye' :
                    priceExpandModal === 'price-chart-trend7d' ? 'fa-chart-line' :
                    priceExpandModal === 'price-chart-trend' ? 'fa-chart-area' :
                    'fa-trophy'
                  } text-blue-600 dark:text-blue-400 text-sm`}
          title={priceExpandModal === 'pricing-landscape' ? 'Pricing Landscape Summary' :
                   priceExpandModal === 'price-distribution' ? 'Price Distribution Analysis' :
                   priceExpandModal === 'promotions' ? 'Active Promotions & Deals' :
                   priceExpandModal === 'price-monitoring' ? 'Price Monitoring' :
                   priceExpandModal === 'price-chart-trend7d' ? '7-Day Price Trends' :
                   priceExpandModal === 'price-chart-trend' ? 'Price Trend Analysis' :
                   'Buy Box Win Rate by Category'}
        >
        <PriceBuyBoxExpandContent modalKey={priceExpandModal} activePromo={activePromo} setActivePromo={setActivePromo} />
        </ScreenerExpandModal>
      )}
      <KPIDetailModal
        isOpen={kpiDetailModal.isOpen}
        onClose={kpiDetailModal.close}
        stat={kpiDetailModal.data}
        filterContext={{ dateRange }}
      />
    </>
  );
};

export default PriceBuyBoxTab;
