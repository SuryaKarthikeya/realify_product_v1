import React, { useState } from 'react';
import { formatCompactCurrency } from '@/utils/formatters';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AreaChart, Area, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, Cell, Legend,
} from 'recharts';
import { bsrTrendData, bsrForecastData } from '@/features/screener/data/screenerData';
import StatCard from '@/components/data-display/StatCard';
import KPIDetailModal from '@/features/screener/components/kpi-detail/KPIDetailModal';
import { useFilterStore } from '@/store/useFilterStore';
import ScreenerAlertsPanel from '@/features/screener/components/ScreenerAlertsPanel';
import AnalyticsModal from '@/features/screener/components/AnalyticsModal';
import ClickToExpand from '@/components/ui/ClickToExpand';
import DeepDiveTabBar from '@/components/navigation/DeepDiveTabBar';
import BaseAreaChart from '@/components/data-display/charts/BaseAreaChart';
import useModalToggle from '@/hooks/useModalToggle';
import { kpis } from '@/features/screener/data/bsrDemandKpis';
import ScreenerExpandModal from '@/features/screener/components/ScreenerExpandModal';


const electronicsBSRData = [
  { name: 'Wireless Earbuds', bsr: 850, color: '#3b82f6' },
  { name: 'Smart Watch', bsr: 435, color: '#10b981' },
  { name: 'USB Hub', bsr: 1280, color: '#8b5cf6' },
  { name: 'HD Webcam', bsr: 2150, color: '#f97316' },
  { name: 'Portable Charger', bsr: 3850, color: '#ef4444' },
];

const BSRDemandTab = () => {
  const [selectedKpiIdx, setSelectedKpiIdx] = useState(0);
  const kpiDetailModal = useModalToggle();
  const dateRange = useFilterStore(s => s.dateRange);
  const [bsrDiveTab, setBsrDiveTab] = useState('kpi');
  const [bsrExpandModal, setBsrExpandModal] = useState(null);
  const [activeModal, setActiveModal] = useState({ isOpen: false, data: null });
  const [expandedCategory, setExpandedCategory] = useState('electronics');

  const selectedKpi = kpis[Math.min(selectedKpiIdx, kpis.length - 1)];

  const handleDetailedView = () => {
    if (bsrDiveTab === 'kpi') {
      setActiveModal({ isOpen: true, data: selectedKpi?.deepDive });
    } else {
      setBsrExpandModal(bsrDiveTab);
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
                <p className="text-sm font-semibold text-gray-900 dark:text-slate-100">Wireless Earbuds surging</p>
                <p className="text-xs text-gray-600 dark:text-slate-400 mt-0.5">BSR improved 1,600 positions in 30 days — peak demand window</p>
              </div>
              <div className="p-3.5 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-700">
                <p className="text-sm font-semibold text-gray-900 dark:text-slate-100">Q4 demand spike expected</p>
                <p className="text-xs text-gray-600 dark:text-slate-400 mt-0.5">Forecast model predicts +45% revenue uplift in Oct-Dec</p>
              </div>
              <div className="p-3.5 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-700">
                <p className="text-sm font-semibold text-gray-900 dark:text-slate-100">Smart Watch demand stable</p>
                <p className="text-xs text-gray-600 dark:text-slate-400 mt-0.5">Consistent #435 BSR; increase inventory for Q4 season</p>
              </div>
            </div>
          </div>

          {/* Mobile alerts */}
          <div className="lg:hidden mb-6">
            <ScreenerAlertsPanel />
          </div>

          {/* BSR Performance by Category */}
          <div className="space-y-5">
            <section id="category-bsr-performance">
              <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-1">BSR Performance by Category</h3>
                    <p className="text-sm text-gray-600 dark:text-slate-400">Compare best seller rankings across product categories</p>
                  </div>
                  <button className="px-4 py-2 bg-brand text-white hover:bg-brand-hover dark:bg-gray-600 dark:hover:bg-gray-500 rounded-xl transition shadow-sm text-sm font-medium">
                    <i className="fa-solid fa-filter mr-2"></i>Filter Categories
                  </button>
                </div>

                <div className="space-y-3">
                  {[
                    { id: 'electronics', label: 'Electronics', count: 42, avg: '#2,145', change: '+285', revenue: '$245K/mo', icon: 'fa-laptop', color: 'blue' },
                    { id: 'home-kitchen', label: 'Home & Kitchen', count: 35, avg: '#3,680', change: '+156', revenue: '$165K/mo', icon: 'fa-blender', color: 'purple' },
                    { id: 'sports', label: 'Sports & Outdoors', count: 28, avg: '#4,520', change: '+92', revenue: '$75K/mo', icon: 'fa-basketball', color: 'green' }
                  ].map((cat) => (
                    <div key={cat.id} className="border border-gray-200 dark:border-slate-800 rounded-xl overflow-hidden">
                      <button
                        onClick={() => setExpandedCategory(expandedCategory === cat.id ? null : cat.id)}
                        className="w-full bg-gray-50 dark:bg-slate-800/50 p-4 hover:bg-gray-100 dark:hover:bg-slate-800 transition cursor-pointer text-left"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4 flex-1">
                            <div className={`w-10 h-10 bg-${cat.color}-100 dark:bg-${cat.color}-900/30 rounded-lg flex items-center justify-center`}>
                              <i className={`fa-solid ${cat.icon} text-${cat.color}-600 dark:text-${cat.color}-400`}></i>
                            </div>
                            <div className="flex-1">
                              <p className="font-semibold text-gray-900 dark:text-slate-100">{cat.label}</p>
                              <p className="text-xs text-gray-500 dark:text-slate-400">{cat.count} products tracked</p>
                            </div>
                            <div className="flex items-center gap-4">
                              <div className="text-right">
                                <p className="font-bold text-gray-900 dark:text-slate-100">{cat.avg}</p>
                                <p className="text-xs text-gray-500 dark:text-slate-400">Avg BSR</p>
                              </div>
                              <span className="px-3 py-1 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded-lg text-sm font-bold border border-green-200 dark:border-green-800">
                                <i className="fa-solid fa-arrow-up mr-1"></i>{cat.change}
                              </span>
                              <span className={`px-3 py-1 bg-${cat.color}-50 dark:bg-${cat.color}-900/20 text-${cat.color}-700 dark:text-${cat.color}-400 rounded-lg text-sm font-bold`}>
                                {cat.revenue}
                              </span>
                            </div>
                          </div>
                          <motion.i
                            animate={{ rotate: expandedCategory === cat.id ? 180 : 0 }}
                            className="fa-solid fa-chevron-down text-gray-400 ml-4"
                          ></motion.i>
                        </div>
                      </button>

                      <AnimatePresence>
                        {expandedCategory === cat.id && (
                          <motion.div
                            initial={{ height: 0 }}
                            animate={{ height: 'auto' }}
                            exit={{ height: 0 }}
                            className="category-products bg-white dark:bg-slate-900 border-t border-gray-200 dark:border-slate-800 overflow-hidden"
                          >
                            <div className="p-6 space-y-4">
                              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                                <div className={`bg-${cat.color === 'blue' ? 'blue' : (cat.color === 'purple' ? 'purple' : 'green')}-50 dark:bg-${cat.color}-900/10 rounded-lg p-4`}>
                                  <p className={`text-xs text-${cat.color}-600 dark:text-${cat.color}-400 font-medium mb-1`}>Top Performer</p>
                                  <p className={`text-lg font-bold text-${cat.color}-900 dark:text-${cat.color}-100`}>{cat.id === 'electronics' ? '#850' : (cat.id === 'home-kitchen' ? '#1,245' : '#2,680')}</p>
                                  <p className="text-xs text-gray-600 dark:text-slate-400 mt-1">{cat.id === 'electronics' ? 'Wireless Earbuds' : (cat.id === 'home-kitchen' ? 'Air Fryer XL' : 'Yoga Mat Premium')}</p>
                                </div>
                                <div className="bg-green-50 dark:bg-green-900/10 rounded-lg p-4">
                                  <p className="text-xs text-green-600 dark:text-green-400 font-medium mb-1">Est. Sales</p>
                                  <p className="text-lg font-bold text-green-900 dark:text-green-100">{cat.revenue.split('/')[0]}</p>
                                  <p className="text-xs text-gray-600 dark:text-slate-400 mt-1">Monthly revenue</p>
                                </div>
                                <div className="bg-purple-50 dark:bg-purple-900/10 rounded-lg p-4">
                                  <p className="text-xs text-purple-600 dark:text-purple-400 font-medium mb-1">Avg Rank Change</p>
                                  <p className="text-lg font-bold text-purple-900 dark:text-purple-100">{cat.change}</p>
                                  <p className="text-xs text-gray-600 dark:text-slate-400 mt-1">Last 30 days</p>
                                </div>
                                <div className="bg-orange-50 dark:bg-orange-900/10 rounded-lg p-4">
                                  <p className="text-xs text-orange-600 dark:text-orange-400 font-medium mb-1">Demand Level</p>
                                  <p className="text-lg font-bold text-orange-900 dark:text-orange-100">{cat.id === 'electronics' ? 'Very High' : (cat.id === 'home-kitchen' ? 'High' : 'Medium')}</p>
                                  <p className="text-xs text-gray-600 dark:text-slate-400 mt-1">Category trend</p>
                                </div>
                              </div>

                              <div className="bg-gray-50 dark:bg-slate-800/30 rounded-lg p-4">
                                <h4 className="font-semibold text-gray-900 dark:text-slate-100 mb-3">Top Products by BSR</h4>
                                <div className="space-y-3">
                                  {cat.id === 'electronics' && [
                                    { name: 'Wireless Earbuds Pro', bsr: '#850', change: '+1,600', sales: '$42K/mo', color: 'blue' },
                                    { name: 'Premium Smart Watch', bsr: '#435', change: 'Stable', sales: '$68K/mo', color: 'green' },
                                    { name: 'USB-C Hub Multi-Port', bsr: '#1,280', change: '+420', sales: '$28K/mo', color: 'purple' }
                                  ].map((prod, i) => (
                                    <div key={i} className="flex items-center gap-3 bg-white dark:bg-slate-900 rounded-lg p-3 hover:shadow-md transition">
                                      <div className={`w-12 h-12 bg-gradient-to-br from-${prod.color}-400 to-${prod.color}-500 rounded-lg flex items-center justify-center text-white font-bold`}>{i + 1}</div>
                                      <div className="flex-1">
                                        <p className="text-sm font-semibold text-gray-900 dark:text-slate-100">{prod.name}</p>
                                        <p className="text-xs text-gray-500 dark:text-slate-400">ASIN: B08XYZ1234</p>
                                      </div>
                                      <div className="text-right">
                                        <p className="text-sm font-bold text-blue-700 dark:text-blue-400">BSR {prod.bsr}</p>
                                        <p className={`text-xs ${prod.change.includes('+') ? 'text-green-600' : 'text-blue-600'}`}>{prod.change}</p>
                                      </div>
                                      <span className="px-3 py-1 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded-lg text-xs font-bold">{prod.sales}</span>
                                      <i className="fa-solid fa-chevron-right text-gray-400"></i>
                                    </div>
                                  ))}
                                </div>
                              </div>

                              {cat.id === 'electronics' && (
                                <div className="h-[350px] w-full">
                                  <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={electronicsBSRData}>
                                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
                                      <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                                      <YAxis reversed axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                                      <RechartsTooltip cursor={{ fill: 'transparent' }} contentStyle={{ backgroundColor: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '12px', color: 'var(--tooltip-text)' }} />
                                      <Bar dataKey="bsr" radius={[4, 4, 0, 0]} barSize={40}>
                                        {electronicsBSRData.map((entry, index) => (
                                          <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                      </Bar>
                                    </BarChart>
                                  </ResponsiveContainer>
                                </div>
                              )}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  ))}
                </div>
              </div>
            </section>
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

            <DeepDiveTabBar>
              {[
                { key: 'kpi', label: selectedKpi?.shortLabel || 'BSR' },
                { key: 'demand-forecast', label: 'Forecast' },
                { key: 'bsr-deepdive', label: 'BSR Deep Dive' },
                { key: 'bsr-highlights', label: 'Highlights' },
                { key: 'demand-trends', label: 'Trends' },
                { key: 'charts', label: 'Charts' },
              ].map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => setBsrDiveTab(key)}
                  className={`px-3 py-3 text-xs font-semibold transition whitespace-nowrap border-b-2 -mb-px ${
                    bsrDiveTab === key
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
                {bsrDiveTab === 'kpi' && (
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
                {bsrDiveTab === 'demand-forecast' && (
                  <div className="p-3 space-y-1.5">
                    {[
                      { label: 'Q3 Forecast', sub: 'Jul - Sep', val: '$448K', colorClass: 'text-blue-600 dark:text-blue-400' },
                      { label: 'Q4 Forecast', sub: 'Oct - Dec', val: '$507K', colorClass: 'text-indigo-600 dark:text-indigo-400' },
                      { label: 'Confidence', sub: 'Model accuracy', val: '88%', colorClass: 'text-green-600 dark:text-green-400' },
                    ].map((item, i) => (
                      <div key={i} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-slate-800/50 rounded-lg">
                        <div className="min-w-0">
                          <p className="text-xs font-medium text-gray-700 dark:text-slate-300 truncate">{item.label}</p>
                          <p className="text-[10px] text-gray-400 dark:text-slate-500 truncate">{item.sub}</p>
                        </div>
                        <span className={`text-xs font-bold ml-2 shrink-0 ${item.colorClass}`}>{item.val}</span>
                      </div>
                    ))}
                  </div>
                )}
                {bsrDiveTab === 'bsr-deepdive' && (
                  <div className="p-3 space-y-1.5">
                    {[
                      { icon: 'fa-headphones', label: 'Wireless Earbuds', sub: 'BSR #850', badge: 'Surging', colorClass: 'text-blue-600 dark:text-blue-400', badgeC: 'text-green-600 dark:text-green-400' },
                      { icon: 'fa-stopwatch', label: 'Smart Watch', sub: 'BSR #435', badge: 'Stable', colorClass: 'text-indigo-600 dark:text-indigo-400', badgeC: 'text-blue-600 dark:text-blue-400' },
                      { icon: 'fa-plug', label: 'USB Hub', sub: 'BSR #1,280', badge: 'Growing', colorClass: 'text-sky-600 dark:text-sky-400', badgeC: 'text-purple-600 dark:text-purple-400' },
                    ].map((item, i) => (
                      <div key={i} className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-slate-800/50 rounded-lg">
                        <i className={`fa-solid ${item.icon} text-xs ${item.colorClass} shrink-0`}></i>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-medium text-gray-700 dark:text-slate-300 truncate">{item.label}</p>
                          <p className="text-[10px] text-gray-400 dark:text-slate-500 truncate">{item.sub}</p>
                        </div>
                        <span className={`text-[10px] font-bold ${item.badgeC} shrink-0`}>{item.badge}</span>
                      </div>
                    ))}
                  </div>
                )}
                {bsrDiveTab === 'bsr-highlights' && (
                  <div className="p-3 space-y-2">
                    {[
                      { label: 'Biggest Mover', value: 'Wireless Earbuds', sub: '+1,600 rank improvement', color: '#10B981' },
                      { label: 'Most Stable', value: 'Smart Watch', sub: 'Consistent #435 BSR', color: '#3B82F6' },
                      { label: 'At Risk', value: 'Portable Charger', sub: 'BSR declining to #3,850', color: '#EF4444' },
                      { label: 'Rising Star', value: 'HD Webcam', sub: 'BSR #2,150 improving', color: '#F97316' },
                    ].map((item, i) => (
                      <div key={i} className="space-y-0.5">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium text-gray-700 dark:text-slate-300">{item.label}</span>
                          <span className="text-xs font-bold" style={{ color: item.color }}>{item.value}</span>
                        </div>
                        <p className="text-[10px] text-gray-400 dark:text-slate-500">{item.sub}</p>
                      </div>
                    ))}
                  </div>
                )}
                {bsrDiveTab === 'demand-trends' && (
                  <div className="p-3 space-y-1.5">
                    {[
                      { label: 'Electronics', val: 'Very High', icon: 'fa-arrow-trend-up', colorClass: 'text-green-600 dark:text-green-400' },
                      { label: 'Home & Kitchen', val: 'High', icon: 'fa-arrow-trend-up', colorClass: 'text-blue-600 dark:text-blue-400' },
                      { label: 'Sports & Outdoors', val: 'Medium', icon: 'fa-minus', colorClass: 'text-amber-600 dark:text-amber-400' },
                    ].map((item, i) => (
                      <div key={i} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-slate-800/50 rounded-lg">
                        <span className="text-xs font-medium text-gray-700 dark:text-slate-300">{item.label}</span>
                        <div className="flex items-center gap-1.5">
                          <i className={`fa-solid ${item.icon} text-[10px] ${item.colorClass}`}></i>
                          <span className={`text-xs font-bold ${item.colorClass}`}>{item.val}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {bsrDiveTab === 'charts' && (
                  <div
                    className="h-full flex flex-col p-3 cursor-pointer"
                    onClick={() => setBsrExpandModal('charts')}
                  >
                    <p className="text-xs font-semibold text-gray-700 dark:text-slate-300 mb-2">BSR Trend (30 Days)</p>
                    <div className="flex-1 pointer-events-none">
                      <ResponsiveContainer width="100%" height={200}>
                        <LineChart data={bsrTrendData}>
                          <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 9 }} />
                          <YAxis reversed axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 9 }} />
                          <RechartsTooltip contentStyle={{ backgroundColor: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '8px', color: 'var(--tooltip-text)' }} />
                          <Line type="monotone" dataKey="earbuds" stroke="#3b82f6" dot={false} strokeWidth={2} name="Earbuds" />
                          <Line type="monotone" dataKey="watch" stroke="#10b981" dot={false} strokeWidth={2} name="Smart Watch" />
                          <Line type="monotone" dataKey="charger" stroke="#ef4444" dot={false} strokeWidth={2} name="Charger" />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                    <ClickToExpand />
                  </div>
                )}
              </div>
              {bsrDiveTab !== 'kpi' && bsrDiveTab !== 'charts' && (
                <button
                  onClick={() => setBsrExpandModal(bsrDiveTab)}
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

      {/* BSR Expand Modal */}
      {bsrExpandModal && (
        <ScreenerExpandModal
          onClose={() => setBsrExpandModal(null)}
          iconWrapClass="bg-blue-100 dark:bg-blue-900/30"
          iconClass={`${
                    bsrExpandModal === 'demand-forecast' ? 'fa-chart-line' :
                    bsrExpandModal === 'bsr-deepdive' ? 'fa-ranking-star' :
                    bsrExpandModal === 'bsr-highlights' ? 'fa-star' :
                    bsrExpandModal === 'demand-trends' ? 'fa-arrow-trend-up' :
                    'fa-chart-area'
                  } text-blue-600 dark:text-blue-400 text-sm`}
          title={bsrExpandModal === 'demand-forecast' ? 'Demand Forecast' :
                   bsrExpandModal === 'bsr-deepdive' ? 'BSR Deep Dive' :
                   bsrExpandModal === 'bsr-highlights' ? 'BSR Highlights' :
                   bsrExpandModal === 'demand-trends' ? 'Demand Trends' :
                   'BSR & Demand Charts'}
          closeIconClass=" text-sm"
        >

              {bsrExpandModal === 'demand-forecast' && (
                <>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    {[
                      { label: 'Q1', val: '$297K', delta: '-15%', bg: 'bg-red-50 dark:bg-red-900/10', border: 'border-red-200 dark:border-red-800', labelC: 'text-red-600 dark:text-red-400', valC: 'text-red-900 dark:text-red-100' },
                      { label: 'Q2', val: '$370K', delta: '+6%', bg: 'bg-blue-50 dark:bg-blue-900/10', border: 'border-blue-200 dark:border-blue-800', labelC: 'text-blue-600 dark:text-blue-400', valC: 'text-blue-900 dark:text-blue-100' },
                      { label: 'Q3', val: '$448K', delta: '+28%', bg: 'bg-green-50 dark:bg-green-900/10', border: 'border-green-200 dark:border-green-800', labelC: 'text-green-600 dark:text-green-400', valC: 'text-green-900 dark:text-green-100' },
                      { label: 'Q4', val: '$507K', delta: '+45%', bg: 'bg-orange-50 dark:bg-orange-900/10', border: 'border-orange-200 dark:border-orange-800', labelC: 'text-orange-600 dark:text-orange-400', valC: 'text-orange-900 dark:text-orange-100' },
                    ].map((item, i) => (
                      <div key={i} className={`${item.bg} border ${item.border} rounded-xl p-4`}>
                        <p className={`text-xs font-bold uppercase tracking-wider mb-1 ${item.labelC}`}>{item.label}</p>
                        <p className={`text-2xl font-bold ${item.valC}`}>{item.val}</p>
                        <p className={`text-sm font-bold mt-1 ${item.labelC}`}>{item.delta} vs baseline</p>
                      </div>
                    ))}
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-gray-900 dark:text-slate-100 mb-4">Annual Demand Forecast</h3>
                    <div className="h-[320px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={bsrForecastData}>
                          <defs>
                            <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="baselineGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#94a3b8" stopOpacity={0.2} />
                              <stop offset="95%" stopColor="#94a3b8" stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
                          <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                          <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={v => formatCompactCurrency(v, { suffix: 'K' })} />
                          <RechartsTooltip contentStyle={{ backgroundColor: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '8px', color: 'var(--tooltip-text)' }} formatter={v => [formatCompactCurrency(v, { decimals: 1, suffix: 'K' })]} />
                          <Legend iconType="circle" />
                          <Area type="monotone" dataKey="forecast" name="Forecast" stroke="#3b82f6" fill="url(#forecastGrad)" strokeWidth={2} />
                          <Area type="monotone" dataKey="baseline" name="Baseline" stroke="#94a3b8" fill="url(#baselineGrad)" strokeWidth={2} strokeDasharray="5 5" />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </>
              )}

              {bsrExpandModal === 'bsr-deepdive' && (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                    {[
                      { name: 'Wireless Earbuds', bsr: '#850', change: '+1,600', revenue: '$42K/mo', status: 'SURGING', bg: 'bg-green-50 dark:bg-green-900/10', border: 'border-green-200 dark:border-green-800', statC: 'text-green-600 dark:text-green-400' },
                      { name: 'Smart Watch', bsr: '#435', change: 'Stable', revenue: '$68K/mo', status: 'STABLE', bg: 'bg-blue-50 dark:bg-blue-900/10', border: 'border-blue-200 dark:border-blue-800', statC: 'text-blue-600 dark:text-blue-400' },
                      { name: 'Portable Charger', bsr: '#3,850', change: '-850', revenue: '$8K/mo', status: 'DECLINING', bg: 'bg-red-50 dark:bg-red-900/10', border: 'border-red-200 dark:border-red-800', statC: 'text-red-600 dark:text-red-400' },
                    ].map((prod, i) => (
                      <div key={i} className={`${prod.bg} border ${prod.border} rounded-2xl p-5`}>
                        <div className="flex items-center gap-3 mb-4">
                          <div className="w-10 h-10 bg-white dark:bg-slate-900 rounded-xl flex items-center justify-center shadow-sm">
                            <span className="text-xl font-black text-gray-400">{i + 1}</span>
                          </div>
                          <div>
                            <p className="font-bold text-gray-900 dark:text-slate-100">{prod.name}</p>
                            <span className={`text-[10px] font-black tracking-widest ${prod.statC}`}>{prod.status}</span>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-xs text-gray-500 dark:text-slate-400">BSR Rank</span>
                            <span className="text-xs font-bold text-gray-900 dark:text-slate-100">{prod.bsr}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-xs text-gray-500 dark:text-slate-400">30d Change</span>
                            <span className={`text-xs font-bold ${prod.statC}`}>{prod.change}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-xs text-gray-500 dark:text-slate-400">Revenue</span>
                            <span className="text-xs font-bold text-green-600 dark:text-green-400">{prod.revenue}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-gray-900 dark:text-slate-100 mb-4">30-Day BSR Trend</h3>
                    <div className="h-[280px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={bsrTrendData}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
                          <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                          <YAxis reversed axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                          <RechartsTooltip contentStyle={{ backgroundColor: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '8px', color: 'var(--tooltip-text)' }} />
                          <Legend iconType="circle" />
                          <Line type="monotone" dataKey="earbuds" stroke="#3b82f6" dot={false} strokeWidth={2} name="Earbuds" />
                          <Line type="monotone" dataKey="watch" stroke="#10b981" dot={false} strokeWidth={2} name="Smart Watch" />
                          <Line type="monotone" dataKey="charger" stroke="#ef4444" dot={false} strokeWidth={2} name="Charger" />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </>
              )}

              {bsrExpandModal === 'bsr-highlights' && (
                <>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    {[
                      { label: 'Biggest Mover', val: 'Earbuds', sub: '+1,600 rank', bg: 'bg-green-50 dark:bg-green-900/10', border: 'border-green-200 dark:border-green-800', labelC: 'text-green-600 dark:text-green-400', valC: 'text-green-900 dark:text-green-100' },
                      { label: 'Most Stable', val: 'Smart Watch', sub: '#435 consistent', bg: 'bg-blue-50 dark:bg-blue-900/10', border: 'border-blue-200 dark:border-blue-800', labelC: 'text-blue-600 dark:text-blue-400', valC: 'text-blue-900 dark:text-blue-100' },
                      { label: 'At Risk', val: 'Portable Charger', sub: 'BSR declining', bg: 'bg-red-50 dark:bg-red-900/10', border: 'border-red-200 dark:border-red-800', labelC: 'text-red-600 dark:text-red-400', valC: 'text-red-900 dark:text-red-100' },
                      { label: 'Rising Star', val: 'HD Webcam', sub: '#2,150 improving', bg: 'bg-orange-50 dark:bg-orange-900/10', border: 'border-orange-200 dark:border-orange-800', labelC: 'text-orange-600 dark:text-orange-400', valC: 'text-orange-900 dark:text-orange-100' },
                    ].map((item, i) => (
                      <div key={i} className={`${item.bg} border ${item.border} rounded-xl p-4`}>
                        <p className={`text-xs font-bold uppercase tracking-wider mb-1 ${item.labelC}`}>{item.label}</p>
                        <p className={`text-lg font-bold ${item.valC}`}>{item.val}</p>
                        <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">{item.sub}</p>
                      </div>
                    ))}
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-gray-900 dark:text-slate-100 mb-4">Product BSR Rankings</h3>
                    <div className="h-[280px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={electronicsBSRData}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
                          <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                          <YAxis reversed axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                          <RechartsTooltip contentStyle={{ backgroundColor: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '8px', color: 'var(--tooltip-text)' }} />
                          <Bar dataKey="bsr" radius={[4, 4, 0, 0]} barSize={40}>
                            {electronicsBSRData.map((entry, index) => (
                              <Cell key={index} fill={entry.color} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </>
              )}

              {bsrExpandModal === 'demand-trends' && (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    {[
                      { label: 'Electronics', val: 'Very High', sub: '+42% YoY growth', icon: 'fa-laptop', bg: 'bg-blue-50 dark:bg-blue-900/10', border: 'border-blue-200 dark:border-blue-800', statC: 'text-blue-600 dark:text-blue-400' },
                      { label: 'Home & Kitchen', val: 'High', sub: '+28% YoY growth', icon: 'fa-blender', bg: 'bg-purple-50 dark:bg-purple-900/10', border: 'border-purple-200 dark:border-purple-800', statC: 'text-purple-600 dark:text-purple-400' },
                      { label: 'Sports & Outdoors', val: 'Medium', sub: '+15% YoY growth', icon: 'fa-basketball', bg: 'bg-green-50 dark:bg-green-900/10', border: 'border-green-200 dark:border-green-800', statC: 'text-green-600 dark:text-green-400' },
                    ].map((cat, i) => (
                      <div key={i} className={`${cat.bg} border ${cat.border} rounded-2xl p-5`}>
                        <div className="flex items-center gap-3 mb-4">
                          <div className="w-10 h-10 bg-white dark:bg-slate-900 rounded-xl flex items-center justify-center shadow-sm">
                            <i className={`fa-solid ${cat.icon} ${cat.statC}`}></i>
                          </div>
                          <div>
                            <p className="font-bold text-gray-900 dark:text-slate-100">{cat.label}</p>
                            <span className={`text-xs font-bold ${cat.statC}`}>{cat.val} Demand</span>
                          </div>
                        </div>
                        <p className="text-sm text-gray-500 dark:text-slate-400">{cat.sub}</p>
                      </div>
                    ))}
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-gray-900 dark:text-slate-100 mb-4">Demand Forecast by Quarter</h3>
                    <div className="h-[280px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={bsrForecastData}>
                          <defs>
                            <linearGradient id="demandForecastGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                              <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
                          <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                          <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={v => formatCompactCurrency(v, { suffix: 'K' })} />
                          <RechartsTooltip contentStyle={{ backgroundColor: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '8px', color: 'var(--tooltip-text)' }} formatter={v => [formatCompactCurrency(v, { decimals: 1, suffix: 'K' })]} />
                          <Area type="monotone" dataKey="forecast" name="Forecast" stroke="#10b981" fill="url(#demandForecastGrad)" strokeWidth={2} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </>
              )}

              {bsrExpandModal === 'charts' && (
                <>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-base font-bold text-gray-900 dark:text-slate-100 mb-4">30-Day BSR Trend</h3>
                      <div className="h-[280px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={bsrTrendData}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
                            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                            <YAxis reversed axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                            <RechartsTooltip contentStyle={{ backgroundColor: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '8px', color: 'var(--tooltip-text)' }} />
                            <Legend iconType="circle" />
                            <Line type="monotone" dataKey="earbuds" stroke="#3b82f6" dot={false} strokeWidth={2} name="Earbuds" />
                            <Line type="monotone" dataKey="watch" stroke="#10b981" dot={false} strokeWidth={2} name="Smart Watch" />
                            <Line type="monotone" dataKey="charger" stroke="#ef4444" dot={false} strokeWidth={2} name="Charger" />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-gray-900 dark:text-slate-100 mb-4">Demand Forecast</h3>
                      <div className="h-[280px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={bsrForecastData}>
                            <defs>
                              <linearGradient id="chartsForecastGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
                            <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                            <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={v => formatCompactCurrency(v, { suffix: 'K' })} />
                            <RechartsTooltip contentStyle={{ backgroundColor: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '8px', color: 'var(--tooltip-text)' }} formatter={v => [formatCompactCurrency(v, { decimals: 1, suffix: 'K' })]} />
                            <Legend iconType="circle" />
                            <Area type="monotone" dataKey="forecast" name="Forecast" stroke="#8b5cf6" fill="url(#chartsForecastGrad)" strokeWidth={2} />
                            <Area type="monotone" dataKey="baseline" name="Baseline" stroke="#94a3b8" fill="transparent" strokeWidth={2} strokeDasharray="5 5" />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>
                </>
              )}

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

export default BSRDemandTab;
