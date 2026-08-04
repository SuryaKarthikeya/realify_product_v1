import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Legend,
} from 'recharts';
import { oppDistributionData, oppFactorScoresData } from '@/features/screener/data/screenerData';
import StatCard from '@/components/data-display/StatCard';
import KPIDetailModal from '@/features/screener/components/kpi-detail/KPIDetailModal';
import { useFilterStore } from '@/store/useFilterStore';
import ScreenerAlertsPanel from '@/features/screener/components/ScreenerAlertsPanel';
import AnalyticsModal from '@/features/screener/components/AnalyticsModal';
import ClickToExpand from '@/components/ui/ClickToExpand';
import DeepDiveTabBar from '@/components/navigation/DeepDiveTabBar';
import BaseAreaChart from '@/components/data-display/charts/BaseAreaChart';
import useModalToggle from '@/hooks/useModalToggle';
import { kpis } from '@/features/screener/data/opportunityResearchKpis';
import ScreenerExpandModal from '@/features/screener/components/ScreenerExpandModal';


const opportunities = [
  {
    id: 'smart-home-sensors',
    rank: 1,
    title: 'Smart Home Sensors',
    category: 'Home & Kitchen',
    score: 94,
    status: 'Excellent',
    revenue: '$142K/mo',
    competition: 'Very Low',
    density: '0.18',
    reviews: '185',
    margin: '42%',
    icon: 'fa-house-signal'
  },
  {
    id: 'eco-yoga-mats',
    rank: 2,
    title: 'Eco-Friendly Yoga Mats',
    category: 'Sports & Outdoors',
    score: 91,
    status: 'Excellent',
    revenue: '$98K/mo',
    competition: 'Low',
    density: '0.24',
    reviews: '245',
    margin: '38%',
    icon: 'fa-leaf'
  },
  {
    id: 'minimalist-wallets',
    rank: 3,
    title: 'Minimalist RFID Wallets',
    category: 'Accessories',
    score: 88,
    status: 'Very Good',
    revenue: '$125K/mo',
    competition: 'Low',
    density: '0.31',
    reviews: '420',
    margin: '35%',
    icon: 'fa-wallet'
  },
  {
    id: 'desk-organizers',
    rank: 4,
    title: 'Bamboo Desk Organizers',
    category: 'Office Products',
    score: 86,
    status: 'Very Good',
    revenue: '$76K/mo',
    competition: 'Low',
    density: '0.28',
    reviews: '310',
    margin: '32%',
    icon: 'fa-layer-group'
  },
  {
    id: 'pet-grooming',
    rank: 5,
    title: 'Pet Grooming Kits',
    category: 'Pet Supplies',
    score: 83,
    status: 'Very Good',
    revenue: '$89K/mo',
    competition: 'Medium',
    density: '0.45',
    reviews: '580',
    margin: '29%',
    icon: 'fa-paw'
  },
  {
    id: 'travel-cubes',
    rank: 6,
    title: 'Compression Packing Cubes',
    category: 'Luggage & Travel',
    score: 81,
    status: 'Very Good',
    revenue: '$65K/mo',
    competition: 'Medium',
    density: '0.52',
    reviews: '720',
    margin: '28%',
    icon: 'fa-suitcase'
  }
];

// Shared Recharts tooltip style (used across all chart tooltips below).
const tooltipStyle = { backgroundColor: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '8px', color: 'var(--tooltip-text)' };

// Renders <Cell> entries colored per-item for Bar/Pie charts (reused across several charts below).
const renderCells = (data) => data.map((entry, idx) => <Cell key={idx} fill={entry.color} />);

// Icon + title metadata for each expandable opportunity modal panel.
const OPP_EXPAND_MODAL_META = {
  'opportunity-deep-dive': { icon: 'fa-magnifying-glass-chart', title: 'Opportunity Deep Dive' },
  'filter-sort': { icon: 'fa-filter', title: 'Filter & Sort Opportunities' },
  'opportunity-snapshot': { icon: 'fa-camera', title: 'Opportunity Snapshot' },
  'hot-opportunity': { icon: 'fa-fire', title: 'Hot Opportunity' },
  charts: { icon: 'fa-chart-bar', title: 'Opportunity Charts' },
};

const OpportunityResearchTab = () => {
  const [selectedKpiIdx, setSelectedKpiIdx] = useState(0);
  const kpiDetailModal = useModalToggle();
  const dateRange = useFilterStore(s => s.dateRange);
  const [oppDiveTab, setOppDiveTab] = useState('kpi');
  const [oppExpandModal, setOppExpandModal] = useState(null);
  const [activeModal, setActiveModal] = useState({ isOpen: false, data: null });
  const [expandedRow, setExpandedRow] = useState('smart-home-sensors');

  const selectedKpi = kpis[Math.min(selectedKpiIdx, kpis.length - 1)];
  const modalMeta = OPP_EXPAND_MODAL_META[oppExpandModal] || OPP_EXPAND_MODAL_META.charts;

  const handleDetailedView = () => {
    if (oppDiveTab === 'kpi') {
      setActiveModal({ isOpen: true, data: selectedKpi?.deepDive });
    } else {
      setOppExpandModal(oppDiveTab);
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
                <p className="text-sm font-semibold text-gray-900 dark:text-slate-100">Smart Home Sensors — top pick</p>
                <p className="text-xs text-gray-600 dark:text-slate-400 mt-0.5">Score 94/100 with Very Low competition (0.18 density)</p>
              </div>
              <div className="p-3.5 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-700">
                <p className="text-sm font-semibold text-gray-900 dark:text-slate-100">67% of opps have Low competition</p>
                <p className="text-xs text-gray-600 dark:text-slate-400 mt-0.5">High entry window before market matures</p>
              </div>
              <div className="p-3.5 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-700">
                <p className="text-sm font-semibold text-gray-900 dark:text-slate-100">Home & Kitchen leads categories</p>
                <p className="text-xs text-gray-600 dark:text-slate-400 mt-0.5">38 opportunities averaging 87 score in this category</p>
              </div>
            </div>
          </div>

          {/* Mobile alerts */}
          <div className="lg:hidden mb-6">
            <ScreenerAlertsPanel />
          </div>

          {/* Opportunity Table */}
          <div className="space-y-5">
            <section id="opportunity-table">
              <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
                <div className="p-5 border-b border-gray-100 dark:border-slate-800">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100 mb-1">Opportunity Ranking</h3>
                      <p className="text-sm text-gray-500 dark:text-slate-400">Click any item to expand details</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <select className="px-3 py-1.5 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-lg text-sm focus:ring-2 focus:ring-brand/30 dark:focus:ring-gray-500/30 dark:text-slate-200">
                        <option>Sort by Score</option>
                        <option>Sort by Revenue</option>
                        <option>Sort by Competition</option>
                      </select>
                    </div>
                  </div>
                </div>
                <div className="p-4 space-y-2">
                  {opportunities.map((opp) => (
                    <div
                      key={opp.id}
                      className={`opp-row bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl overflow-hidden transition hover:shadow-sm cursor-pointer ${expandedRow === opp.id ? 'ring-1 ring-gray-300 dark:ring-slate-700' : ''}`}
                      onClick={() => setExpandedRow(expandedRow === opp.id ? null : opp.id)}
                    >
                      <div className="opp-row-header flex items-center gap-4 p-4">
                        <div className="w-8 h-8 bg-gray-100 dark:bg-slate-800 rounded-lg flex items-center justify-center flex-shrink-0">
                          <span className="text-sm font-bold text-gray-500 dark:text-slate-400">{opp.rank}</span>
                        </div>
                        <div className="w-9 h-9 bg-gray-50 dark:bg-slate-800/50 rounded-lg flex items-center justify-center flex-shrink-0">
                          <i className={`fa-solid ${opp.icon} text-gray-400 dark:text-slate-500`}></i>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-gray-900 dark:text-slate-100 truncate">{opp.title}</p>
                          <p className="text-xs text-gray-500 dark:text-slate-400">{opp.category}</p>
                        </div>
                        <div className="flex items-center gap-3 flex-shrink-0">
                          <span className={`text-lg font-bold ${opp.score >= 90 ? 'text-emerald-600 dark:text-emerald-400' : 'text-blue-600 dark:text-blue-400'}`}>{opp.score}</span>
                          <span className={`px-2 py-0.5 ${opp.score >= 90 ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-400' : 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-400'} rounded text-xs font-medium border hidden sm:inline-block`}>{opp.status}</span>
                          <span className="text-sm font-semibold text-gray-700 dark:text-slate-300">{opp.revenue}</span>
                          <motion.i
                            animate={{ rotate: expandedRow === opp.id ? 180 : 0 }}
                            className="fa-solid fa-chevron-down text-gray-400 text-xs"
                          ></motion.i>
                        </div>
                      </div>

                      <AnimatePresence>
                        {expandedRow === opp.id && (
                          <motion.div
                            initial={{ height: 0 }}
                            animate={{ height: 'auto' }}
                            exit={{ height: 0 }}
                            className="overflow-hidden"
                          >
                            <div className="px-4 pb-4 pt-0 border-t border-gray-100 dark:border-slate-800">
                              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
                                <div className="bg-gray-50 dark:bg-slate-800/50 rounded-lg p-3">
                                  <p className="text-xs text-gray-500 dark:text-slate-400">Competition</p>
                                  <p className={`text-sm font-semibold ${opp.competition.includes('Low') ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}`}>{opp.competition}</p>
                                  <p className="text-xs text-gray-400 dark:text-slate-500 mt-0.5">Density: {opp.density}</p>
                                </div>
                                <div className="bg-gray-50 dark:bg-slate-800/50 rounded-lg p-3">
                                  <p className="text-xs text-gray-500 dark:text-slate-400">Avg Reviews</p>
                                  <p className="text-sm font-semibold text-gray-700 dark:text-slate-200">{opp.reviews}</p>
                                  <p className="text-xs text-gray-400 dark:text-slate-500 mt-0.5">barrier to entry</p>
                                </div>
                                <div className="bg-gray-50 dark:bg-slate-800/50 rounded-lg p-3">
                                  <p className="text-xs text-gray-500 dark:text-slate-400">Est. Margin</p>
                                  <p className="text-sm font-semibold text-gray-700 dark:text-slate-200">{opp.margin}</p>
                                  <p className="text-xs text-gray-400 dark:text-slate-500 mt-0.5">potential</p>
                                </div>
                                <div className="bg-gray-50 dark:bg-slate-800/50 rounded-lg p-3">
                                  <p className="text-xs text-gray-500 dark:text-slate-400">Est. Revenue</p>
                                  <p className="text-sm font-semibold text-gray-700 dark:text-slate-200">{opp.revenue.split('/')[0]}</p>
                                  <p className="text-xs text-gray-400 dark:text-slate-500 mt-0.5">per month</p>
                                </div>
                              </div>
                              <div className="flex items-center gap-2 mt-3">
                                <button className="px-3 py-1.5 bg-gray-900 dark:bg-slate-100 dark:text-slate-900 text-white hover:bg-gray-800 rounded-lg text-xs font-medium transition">
                                  <i className="fa-solid fa-magnifying-glass mr-1"></i>Deep Research
                                </button>
                                <button className="px-3 py-1.5 bg-white dark:bg-slate-800 text-gray-700 dark:text-slate-300 border border-gray-200 dark:border-slate-700 hover:bg-gray-50 rounded-lg text-xs font-medium transition">
                                  <i className="fa-regular fa-bookmark mr-1"></i>Save
                                </button>
                                <button className="px-3 py-1.5 bg-white dark:bg-slate-800 text-gray-700 dark:text-slate-300 border border-gray-200 dark:border-slate-700 hover:bg-gray-50 rounded-lg text-xs font-medium transition">
                                  <i className="fa-solid fa-chart-line mr-1"></i>Track
                                </button>
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  ))}
                </div>
                <div className="p-4 border-t border-gray-100 dark:border-slate-800 flex items-center justify-between">
                  <p className="text-sm text-gray-500 dark:text-slate-400">Showing 6 of 145 opportunities</p>
                  <button className="px-4 py-2 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 text-gray-700 dark:text-slate-300 hover:bg-gray-50 rounded-lg text-sm font-medium transition">
                    Load More
                  </button>
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
                { key: 'kpi', label: selectedKpi?.shortLabel || 'Opps' },
                { key: 'opportunity-deep-dive', label: 'Deep Dive' },
                { key: 'filter-sort', label: 'Filter & Sort' },
                { key: 'opportunity-snapshot', label: 'Snapshot' },
                { key: 'hot-opportunity', label: 'Hot Pick' },
                { key: 'charts', label: 'Charts' },
              ].map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => setOppDiveTab(key)}
                  className={`px-3 py-3 text-xs font-semibold transition whitespace-nowrap border-b-2 -mb-px ${
                    oppDiveTab === key
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
                {oppDiveTab === 'kpi' && (
                  <div
                    className="h-full flex flex-col p-4 cursor-pointer group"
                    onClick={() => setActiveModal({ isOpen: true, data: selectedKpi?.deepDive })}
                  >
                    <div className="flex items-center justify-between px-1 mb-2">
                      <span className="text-xs font-semibold text-gray-700 dark:text-slate-300">{selectedKpi?.title}</span>
                      <span className="text-xs font-bold text-purple-600 dark:text-purple-400">{selectedKpi?.value}</span>
                    </div>
                    <div className="h-[180px] w-full pointer-events-none overflow-hidden">
                      <BaseAreaChart
                        data={selectedKpi?.chartData || []}
                        height={180}
                        areas={[{ key: 'val', name: selectedKpi?.title, color: selectedKpi?.chartColor || '#8b5cf6' }]}
                        yAxisFormatter={(v) => `${v}`}
                        tooltipFormatter={(v, n) => [`${v}`, n]}
                      />
                    </div>
                    <ClickToExpand />
                  </div>
                )}
                {oppDiveTab === 'opportunity-deep-dive' && (
                  <div className="p-3 space-y-1.5">
                    {[
                      { label: 'Smart Home Sensors', sub: 'Score 94 • $142K/mo', val: 'Excellent', colorClass: 'text-green-600 dark:text-green-400' },
                      { label: 'Eco Yoga Mats', sub: 'Score 91 • $98K/mo', val: 'Excellent', colorClass: 'text-green-600 dark:text-green-400' },
                      { label: 'RFID Wallets', sub: 'Score 88 • $125K/mo', val: 'Very Good', colorClass: 'text-blue-600 dark:text-blue-400' },
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
                {oppDiveTab === 'filter-sort' && (
                  <div className="p-3 space-y-2">
                    {[
                      { label: '90+ Score', value: 12, sub: 'Excellent tier', color: '#10B981' },
                      { label: '80-89 Score', value: 35, sub: 'Very Good tier', color: '#3B82F6' },
                      { label: '70-79 Score', value: 48, sub: 'Good tier', color: '#8B5CF6' },
                      { label: 'Below 70', value: 50, sub: 'Fair/Below avg', color: '#F97316' },
                    ].map((item, i) => (
                      <div key={i} className="space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium text-gray-700 dark:text-slate-300">{item.label}</span>
                          <span className="text-xs font-bold" style={{ color: item.color }}>{item.value} opps</span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-1.5">
                          <div className="h-1.5 rounded-full" style={{ width: `${(item.value / 50) * 100}%`, backgroundColor: item.color }}></div>
                        </div>
                        <p className="text-[10px] text-gray-400 dark:text-slate-500">{item.sub}</p>
                      </div>
                    ))}
                  </div>
                )}
                {oppDiveTab === 'opportunity-snapshot' && (
                  <div className="p-3 space-y-1.5">
                    {[
                      { label: 'Total Opportunities', val: '145', sub: '+23 new this month', colorClass: 'text-purple-600 dark:text-purple-400' },
                      { label: 'Avg Opportunity Score', val: '84/100', sub: 'Quality index', colorClass: 'text-blue-600 dark:text-blue-400' },
                      { label: 'Avg Monthly Revenue', val: '$99K', sub: 'Per opportunity', colorClass: 'text-green-600 dark:text-green-400' },
                      { label: 'Low Competition', val: '67%', sub: 'Of all opps', colorClass: 'text-orange-600 dark:text-orange-400' },
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
                {oppDiveTab === 'hot-opportunity' && (
                  <div className="p-3 space-y-2">
                    <div className="p-3 bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800 rounded-xl">
                      <div className="flex items-center gap-2 mb-1">
                        <i className="fa-solid fa-fire text-green-600 dark:text-green-400 text-sm"></i>
                        <span className="text-xs font-bold text-green-700 dark:text-green-400">HOT PICK</span>
                      </div>
                      <p className="text-sm font-bold text-gray-900 dark:text-slate-100">Smart Home Sensors</p>
                      <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">Score 94 • $142K/mo • Very Low competition</p>
                    </div>
                    {[
                      { label: 'Opp Score', val: '94/100', icon: 'fa-star', colorClass: 'text-green-600 dark:text-green-400' },
                      { label: 'Competition', val: 'Very Low', icon: 'fa-shield', colorClass: 'text-blue-600 dark:text-blue-400' },
                      { label: 'Est. Margin', val: '42%', icon: 'fa-percent', colorClass: 'text-purple-600 dark:text-purple-400' },
                    ].map((item, i) => (
                      <div key={i} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-slate-800/50 rounded-lg">
                        <div className="flex items-center gap-2">
                          <i className={`fa-solid ${item.icon} text-xs ${item.colorClass}`}></i>
                          <span className="text-xs font-medium text-gray-700 dark:text-slate-300">{item.label}</span>
                        </div>
                        <span className={`text-xs font-bold ${item.colorClass}`}>{item.val}</span>
                      </div>
                    ))}
                  </div>
                )}
                {oppDiveTab === 'charts' && (
                  <div
                    className="h-full flex flex-col p-3 cursor-pointer"
                    onClick={() => setOppExpandModal('charts')}
                  >
                    <p className="text-xs font-semibold text-gray-700 dark:text-slate-300 mb-2">Score Distribution</p>
                    <div className="flex-1 pointer-events-none">
                      <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={oppDistributionData}>
                          <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 8 }} />
                          <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 9 }} />
                          <RechartsTooltip contentStyle={tooltipStyle} />
                          <Bar dataKey="value" radius={[3, 3, 0, 0]} barSize={24}>
                            {renderCells(oppDistributionData)}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                    <ClickToExpand />
                  </div>
                )}
              </div>
              {oppDiveTab !== 'kpi' && oppDiveTab !== 'charts' && (
                <button
                  onClick={() => setOppExpandModal(oppDiveTab)}
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

      {/* Opportunity Expand Modal */}
      {oppExpandModal && (
        <ScreenerExpandModal
          onClose={() => setOppExpandModal(null)}
          iconWrapClass="bg-purple-100 dark:bg-purple-900/30"
          iconClass={`${modalMeta.icon} text-purple-600 dark:text-purple-400 text-sm`}
          title={modalMeta.title}
          closeIconClass=" text-sm"
        >

              {oppExpandModal === 'opportunity-deep-dive' && (
                <>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    {[
                      { label: 'Total Opps', val: '145', sub: '+23 new', bg: 'bg-purple-50 dark:bg-purple-900/10', border: 'border-purple-200 dark:border-purple-800', labelC: 'text-purple-600 dark:text-purple-400', valC: 'text-purple-900 dark:text-purple-100' },
                      { label: 'Excellent', val: '12', sub: 'Score 90+', bg: 'bg-green-50 dark:bg-green-900/10', border: 'border-green-200 dark:border-green-800', labelC: 'text-green-600 dark:text-green-400', valC: 'text-green-900 dark:text-green-100' },
                      { label: 'Very Good', val: '35', sub: 'Score 80-89', bg: 'bg-blue-50 dark:bg-blue-900/10', border: 'border-blue-200 dark:border-blue-800', labelC: 'text-blue-600 dark:text-blue-400', valC: 'text-blue-900 dark:text-blue-100' },
                      { label: 'Good', val: '48', sub: 'Score 70-79', bg: 'bg-indigo-50 dark:bg-indigo-900/10', border: 'border-indigo-200 dark:border-indigo-800', labelC: 'text-indigo-600 dark:text-indigo-400', valC: 'text-indigo-900 dark:text-indigo-100' },
                    ].map((item, i) => (
                      <div key={i} className={`${item.bg} border ${item.border} rounded-xl p-4`}>
                        <p className={`text-xs font-bold uppercase tracking-wider mb-1 ${item.labelC}`}>{item.label}</p>
                        <p className={`text-2xl font-bold ${item.valC}`}>{item.val}</p>
                        <p className={`text-xs mt-1 font-medium ${item.labelC}`}>{item.sub}</p>
                      </div>
                    ))}
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-gray-900 dark:text-slate-100 mb-4">Top Opportunities Ranked</h3>
                    <div className="space-y-3">
                      {opportunities.slice(0, 4).map((opp) => (
                        <div key={opp.id} className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-800">
                          <div className="w-10 h-10 bg-white dark:bg-slate-900 rounded-xl flex items-center justify-center shadow-sm">
                            <span className="text-lg font-black text-gray-400">#{opp.rank}</span>
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-bold text-gray-900 dark:text-slate-100">{opp.title}</p>
                            <p className="text-xs text-gray-500 dark:text-slate-400">{opp.category}</p>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="text-right">
                              <p className={`text-lg font-bold ${opp.score >= 90 ? 'text-green-600 dark:text-green-400' : 'text-blue-600 dark:text-blue-400'}`}>{opp.score}</p>
                              <p className="text-xs text-gray-400 dark:text-slate-500">Score</p>
                            </div>
                            <div className="text-right">
                              <p className="text-sm font-bold text-green-600 dark:text-green-400">{opp.revenue}</p>
                              <p className="text-xs text-gray-400 dark:text-slate-500">Revenue</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {oppExpandModal === 'filter-sort' && (
                <>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-base font-bold text-gray-900 dark:text-slate-100 mb-4">Score Distribution</h3>
                      <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={oppDistributionData}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
                            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 10 }} />
                            <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                            <RechartsTooltip contentStyle={tooltipStyle} />
                            <Bar dataKey="value" radius={[4, 4, 0, 0]} barSize={32}>
                              {renderCells(oppDistributionData)}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-gray-900 dark:text-slate-100 mb-4">Opportunity Factor Scores</h3>
                      <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={oppFactorScoresData} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
                            <XAxis type="number" domain={[0, 100]} axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                            <YAxis type="category" dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 10 }} width={120} />
                            <RechartsTooltip contentStyle={tooltipStyle} />
                            <Bar dataKey="score" radius={[0, 4, 4, 0]} barSize={24}>
                              {renderCells(oppFactorScoresData)}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>
                </>
              )}

              {oppExpandModal === 'opportunity-snapshot' && (
                <>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    {[
                      { label: 'Total Opportunities', val: '145', sub: '+23 vs last month', bg: 'bg-purple-50 dark:bg-purple-900/10', border: 'border-purple-200 dark:border-purple-800', labelC: 'text-purple-600 dark:text-purple-400', valC: 'text-purple-900 dark:text-purple-100' },
                      { label: 'Avg Opp Score', val: '84/100', sub: 'Quality index', bg: 'bg-blue-50 dark:bg-blue-900/10', border: 'border-blue-200 dark:border-blue-800', labelC: 'text-blue-600 dark:text-blue-400', valC: 'text-blue-900 dark:text-blue-100' },
                      { label: 'Avg Revenue', val: '$99K/mo', sub: 'Per opportunity', bg: 'bg-green-50 dark:bg-green-900/10', border: 'border-green-200 dark:border-green-800', labelC: 'text-green-600 dark:text-green-400', valC: 'text-green-900 dark:text-green-100' },
                      { label: 'Low Competition', val: '67%', sub: 'Of all opps', bg: 'bg-orange-50 dark:bg-orange-900/10', border: 'border-orange-200 dark:border-orange-800', labelC: 'text-orange-600 dark:text-orange-400', valC: 'text-orange-900 dark:text-orange-100' },
                    ].map((item, i) => (
                      <div key={i} className={`${item.bg} border ${item.border} rounded-xl p-4`}>
                        <p className={`text-xs font-bold uppercase tracking-wider mb-1 ${item.labelC}`}>{item.label}</p>
                        <p className={`text-xl font-bold ${item.valC}`}>{item.val}</p>
                        <p className={`text-xs mt-1 font-medium ${item.labelC}`}>{item.sub}</p>
                      </div>
                    ))}
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-gray-900 dark:text-slate-100 mb-4">All Opportunities Overview</h3>
                    <div className="space-y-2">
                      {opportunities.map((opp) => (
                        <div key={opp.id} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-800">
                          <span className="text-sm font-black text-gray-400 w-5 shrink-0">{opp.rank}</span>
                          <i className={`fa-solid ${opp.icon} text-xs text-gray-400 dark:text-slate-500 shrink-0`}></i>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-gray-900 dark:text-slate-100 truncate">{opp.title}</p>
                            <p className="text-xs text-gray-500 dark:text-slate-400 truncate">{opp.category}</p>
                          </div>
                          <span className={`text-sm font-bold ${opp.score >= 90 ? 'text-green-600 dark:text-green-400' : 'text-blue-600 dark:text-blue-400'}`}>{opp.score}</span>
                          <span className="text-sm font-semibold text-gray-700 dark:text-slate-300 hidden sm:block">{opp.revenue}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {oppExpandModal === 'hot-opportunity' && (
                <>
                  <div className="bg-gradient-to-br from-green-50 to-emerald-100 dark:from-green-900/10 dark:to-emerald-900/20 border-2 border-green-200 dark:border-green-800 rounded-3xl p-6 shadow-inner">
                    <div className="flex items-start justify-between mb-5">
                      <div>
                        <span className="px-3 py-1 bg-white/80 dark:bg-slate-900/80 text-gray-900 dark:text-slate-100 rounded-lg text-xs font-black tracking-widest border border-current opacity-60 mb-3 inline-block uppercase italic">
                          Hot Opportunity
                        </span>
                        <h4 className="text-3xl font-black text-gray-900 dark:text-slate-100 tracking-tight leading-tight">Smart Home Sensors</h4>
                        <p className="text-gray-600 dark:text-slate-400 mt-2 font-medium">Home & Kitchen • Score 94/100</p>
                      </div>
                      <div className="w-16 h-16 bg-white dark:bg-slate-900 rounded-2xl flex items-center justify-center shadow-xl border border-green-200">
                        <i className="fa-solid fa-house-signal text-3xl text-green-600"></i>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-5">
                      {[
                        { label: 'REVENUE', val: '$142K/mo', color: 'green' },
                        { label: 'COMPETITION', val: 'Very Low', color: 'blue' },
                        { label: 'MARGIN', val: '42%', color: 'purple' },
                        { label: 'AVG REVIEWS', val: '185', color: 'orange' },
                      ].map((m, i) => (
                        <div key={i} className="bg-white/60 dark:bg-slate-900/60 backdrop-blur-md rounded-2xl p-5 border border-white dark:border-slate-800 shadow-sm">
                          <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">{m.label}</p>
                          <p className={`text-xl font-black text-${m.color}-700 dark:text-${m.color}-400`}>{m.val}</p>
                        </div>
                      ))}
                    </div>
                    <div>
                      <h4 className="text-sm font-black text-gray-900 dark:text-slate-100 uppercase tracking-widest opacity-60 mb-4">Factor Scores</h4>
                      <div className="h-[220px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={oppFactorScoresData} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(255,255,255,0.3)" />
                            <XAxis type="number" domain={[0, 100]} axisLine={false} tickLine={false} tick={{ fill: '#6b7280', fontSize: 10 }} />
                            <YAxis type="category" dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#6b7280', fontSize: 10 }} width={120} />
                            <RechartsTooltip contentStyle={tooltipStyle} />
                            <Bar dataKey="score" radius={[0, 4, 4, 0]} barSize={20}>
                              {renderCells(oppFactorScoresData)}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>
                </>
              )}

              {oppExpandModal === 'charts' && (
                <>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-base font-bold text-gray-900 dark:text-slate-100 mb-4">Score Distribution</h3>
                      <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={oppDistributionData}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
                            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 10 }} />
                            <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                            <RechartsTooltip contentStyle={tooltipStyle} />
                            <Bar dataKey="value" radius={[4, 4, 0, 0]} barSize={32}>
                              {renderCells(oppDistributionData)}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-gray-900 dark:text-slate-100 mb-4">Opportunity by Score Tier</h3>
                      <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={oppDistributionData}
                              cx="50%"
                              cy="50%"
                              innerRadius={70}
                              outerRadius={100}
                              paddingAngle={5}
                              dataKey="value"
                            >
                              {renderCells(oppDistributionData)}
                            </Pie>
                            <RechartsTooltip />
                            <Legend iconType="circle" />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-gray-900 dark:text-slate-100 mb-4">Top Opportunity Factor Scores</h3>
                    <div className="h-[220px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={oppFactorScoresData} layout="vertical">
                          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="currentColor" className="text-gray-200 dark:text-slate-700" />
                          <XAxis type="number" domain={[0, 100]} axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                          <YAxis type="category" dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 10 }} width={120} />
                          <RechartsTooltip contentStyle={tooltipStyle} />
                          <Bar dataKey="score" radius={[0, 4, 4, 0]} barSize={24}>
                            {renderCells(oppFactorScoresData)}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
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

export default OpportunityResearchTab;
