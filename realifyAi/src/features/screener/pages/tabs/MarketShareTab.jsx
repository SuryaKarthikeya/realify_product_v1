import React, { useState } from 'react';
import StatCard from '@/components/data-display/StatCard';
import KPIDetailModal from '@/features/screener/components/kpi-detail/KPIDetailModal';
import { useFilterStore } from '@/store/useFilterStore';
import { motion, AnimatePresence } from 'framer-motion';
import {
  PieChart, Pie, Cell, Tooltip as RechartsTooltip, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  ScatterChart, Scatter, ZAxis, LabelList,
} from 'recharts';
import ScreenerAlertsPanel from '@/features/screener/components/ScreenerAlertsPanel';
import AnalyticsModal from '@/features/screener/components/AnalyticsModal';
import ClickToExpand from '@/components/ui/ClickToExpand';
import DeepDiveTabBar from '@/components/navigation/DeepDiveTabBar';
import BaseAreaChart from '@/components/data-display/charts/BaseAreaChart';
import useModalToggle from '@/hooks/useModalToggle';
import { kpis } from '@/features/screener/data/marketShareKpis';
import MarketShareExpandContent from '@/features/screener/components/expand-content/MarketShareExpandContent';
import ScreenerExpandModal from '@/features/screener/components/ScreenerExpandModal';



const OpportunityDetail = ({ id }) => {
  const details = {
    electronics: {
      color: 'blue',
      priority: 'HIGH PRIORITY',
      title: 'Expand Electronics Presence',
      sub: 'Currently #2 with 22.4% share',
      icon: 'fa-laptop',
      stats: [{ l: 'Potential Gain', v: '+3.8%', c: 'blue' }, { l: 'Revenue Impact', v: '+$312K', c: 'green' }, { l: 'Timeline', v: '6 months', c: 'purple' }],
      actions: [
        { h: 'Launch 15 new SKUs in high-demand segments', b: 'Focus on wireless headphones, smart watches, and portable chargers' },
        { h: 'Improve pricing competitiveness by 5%', b: 'Target price-sensitive segments to win market share from competitors' },
        { h: 'Target market leader\'s weak subcategories', b: 'Identify and exploit gaps in gaming accessories and photography equipment' }
      ],
      metrics: [{ l: 'Market Share Target', v: '26.2%', c: 'blue' }, { l: 'New Revenue', v: '$2.15M', c: 'green' }]
    },
    'home-kitchen': {
      color: 'purple',
      priority: 'MEDIUM PRIORITY',
      title: 'Grow Home & Kitchen',
      sub: 'Currently #4 with 16.8% share',
      icon: 'fa-blender',
      stats: [{ l: 'Potential Gain', v: '+2.4%', c: 'purple' }, { l: 'Revenue Impact', v: '+$134K', c: 'green' }, { l: 'Timeline', v: '9 months', c: 'orange' }],
      actions: [
        { h: 'Fill assortment gaps in cookware', b: 'Add premium non-stick sets and cast iron collections' },
        { h: 'Launch seasonal promotions', b: 'Create holiday bundles and back-to-school campaigns' },
        { h: 'Improve product ratings and reviews', b: 'Implement review generation program to boost social proof' }
      ],
      metrics: [{ l: 'Market Share Target', v: '19.2%', c: 'purple' }, { l: 'New Revenue', v: '$1.08M', c: 'green' }]
    },
    sports: {
      color: 'green',
      priority: 'MAINTAIN',
      title: 'Defend Sports Position',
      sub: 'Currently #3 with 19.2% share',
      icon: 'fa-basketball',
      stats: [{ l: 'Share at Risk', v: '-1.2%', c: 'orange' }, { l: 'Competitive Threat', v: 'Medium', c: 'red' }, { l: 'Action Window', v: '3 months', c: 'blue' }],
      actions: [
        { h: 'Monitor competitor pricing closely', b: 'Set up automated alerts for price changes on key SKUs' },
        { h: 'Maintain product availability', b: 'Ensure 99% in-stock rate for top 50 products' },
        { h: 'Strengthen brand positioning', b: 'Invest in content marketing and influencer partnerships' }
      ],
      metrics: [{ l: 'Market Share Target', v: '19.2%+', c: 'green' }, { l: 'Revenue Protect', v: '$730K', c: 'blue' }]
    },
    toys: {
      color: 'orange',
      priority: 'TURNAROUND',
      title: 'Revive Toys & Games',
      sub: 'Currently #6 with 12.3% share',
      icon: 'fa-baby',
      stats: [{ l: 'Current Decline', v: '-3%', c: 'red' }, { l: 'Recovery Potential', v: '+5.2%', c: 'green' }, { l: 'Timeline', v: '12 months', c: 'purple' }],
      actions: [
        { h: 'Expand product portfolio by 40%', b: 'Add trending categories like STEM toys and collectibles' },
        { h: 'Launch aggressive promotions', b: 'Run monthly flash sales and bundle deals to regain momentum' },
        { h: 'Partner with trending brands', b: 'Secure licensing deals with popular franchises and IPs' }
      ],
      metrics: [{ l: 'Market Share Target', v: '17.5%', c: 'orange' }, { l: 'New Revenue', v: '$367K', c: 'green' }]
    }
  }[id];

  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 rounded-xl p-6 h-full shadow-sm">
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className={`px-3 py-1 bg-${details.color}-600 text-white rounded-lg text-xs font-bold`}>{details.priority}</span>
          </div>
          <h4 className="text-2xl font-bold text-gray-900 dark:text-slate-100">{details.title}</h4>
          <p className="text-sm text-gray-600 dark:text-slate-400 mt-1">{details.sub}</p>
        </div>
        <div className={`w-12 h-12 bg-${details.color}-600 rounded-xl flex items-center justify-center shadow-md`}>
          <i className={`fa-solid ${details.icon} text-white text-xl`}></i>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-3 mb-6">
        {details.stats.map((s, i) => (
          <div key={i} className="bg-white dark:bg-slate-900 rounded-lg p-4 border border-white dark:border-slate-800 shadow-sm">
            <p className="text-xs text-gray-500 dark:text-slate-500 mb-1">{s.l}</p>
            <p className={`text-2xl font-bold text-${s.c}-900 dark:text-${s.c}-400`}>{s.v}</p>
          </div>
        ))}
      </div>
      <div className="space-y-4 mb-6">
        <div>
          <p className="text-sm font-bold text-gray-900 dark:text-slate-100 mb-3 tracking-wider">Key Actions:</p>
          <div className="space-y-2">
            {details.actions.map((a, i) => (
              <div key={i} className="flex items-start gap-2 bg-gray-50 dark:bg-slate-800/50 rounded-lg p-3 border border-gray-100 dark:border-slate-700">
                <i className={`fa-solid ${details.id === 'sports' ? 'fa-shield' : (details.id === 'toys' ? 'fa-wrench' : 'fa-check')} text-${details.color}-600 dark:text-${details.color}-400 text-sm mt-0.5`}></i>
                <div>
                  <p className="text-sm font-semibold text-gray-900 dark:text-slate-100">{a.h}</p>
                  <p className="text-xs text-gray-600 dark:text-slate-400">{a.b}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div>
          <p className="text-sm font-bold text-gray-900 dark:text-slate-100 mb-3 tracking-wider">Success Metrics:</p>
          <div className="grid grid-cols-2 gap-3">
            {details.metrics.map((m, i) => (
              <div key={i} className="bg-white dark:bg-slate-900 rounded-lg p-3 border border-white dark:border-slate-800 shadow-sm">
                <p className="text-xs text-gray-500 dark:text-slate-500">{m.l}</p>
                <p className={`font-bold text-${m.c}-900 dark:text-${m.c}-400`}>{m.v}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="flex gap-3">
        <button className={`flex-1 px-4 py-3 bg-${details.color}-600 text-white hover:bg-${details.color}-700 rounded-lg transition font-medium shadow-md shadow-${details.color}-500/20`}>
          <i className="fa-solid fa-rocket mr-2"></i>{details.id === 'toys' ? 'Launch Turnaround' : (details.id === 'sports' ? 'Activate Defense' : 'Launch Initiative')}
        </button>
        <button className="flex-1 px-4 py-3 bg-white dark:bg-slate-900 text-gray-700 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800 border border-gray-200 dark:border-slate-800 rounded-lg transition font-medium">
          <i className="fa-solid fa-download mr-2"></i>Download Plan
        </button>
      </div>
    </div>
  );
};



const EXPAND_MODAL_META = {
  distribution: { icon: 'fa-chart-pie', title: 'Market Share Distribution' },
  'by-category': { icon: 'fa-layer-group', title: 'Market Share by Category' },
  movements: { icon: 'fa-arrow-trend-up', title: 'Recent Market Movements' },
  'chart-positioning': { icon: 'fa-circle-dot', title: 'Competitive Positioning Matrix' },
  'chart-trends': { icon: 'fa-chart-line', title: 'Market Share Trends (12 Months)' },
  charts: { icon: 'fa-chart-line', title: 'Charts' },
};

const MarketShareTab = () => {
  const [selectedKpiIdx, setSelectedKpiIdx] = useState(0);
  const kpiDetailModal = useModalToggle();
  const dateRange = useFilterStore(s => s.dateRange);
  const [mktDiveTab, setMktDiveTab] = useState('kpi');
  const [mktExpandModal, setMktExpandModal] = useState(null);
  const [expandedCategory, setExpandedCategory] = useState('electronics');
  const [selectedOpportunity, setSelectedOpportunity] = useState('electronics');
  const [expandedMovement, setExpandedMovement] = useState('competitor-gain');
  const [activeModal, setActiveModal] = useState({ isOpen: false, data: null });

  const selectedKpi = kpis[Math.min(selectedKpiIdx, kpis.length - 1)];
  const expandModalMeta = EXPAND_MODAL_META[mktExpandModal] || EXPAND_MODAL_META.charts;

  const handleDetailedView = () => {
    if (mktDiveTab === 'kpi') {
      setActiveModal({ isOpen: true, data: selectedKpi?.deepDive });
    } else {
      setMktExpandModal(mktDiveTab);
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
                <p className="text-sm font-semibold text-gray-900 dark:text-slate-100">Competitor Expansion</p>
                <p className="text-xs text-gray-600 dark:text-slate-400 mt-0.5">TechMaster undercut overnight on key ASINs — draft reprice recommended</p>
              </div>
              <div className="p-3.5 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-700">
                <p className="text-sm font-semibold text-gray-900 dark:text-slate-100">Share Erosion Alert</p>
                <p className="text-xs text-gray-600 dark:text-slate-400 mt-0.5">3 ASINs are 8% below MAP — pricing review needed</p>
              </div>
              <div className="p-3.5 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-700">
                <p className="text-sm font-semibold text-gray-900 dark:text-slate-100">Gap Emerged</p>
                <p className="text-xs text-gray-600 dark:text-slate-400 mt-0.5">Pet Bed SP showing 8.6× M-ROAS — strong scale opportunity</p>
              </div>
            </div>
          </div>

          {/* Mobile alerts */}
          <div className="lg:hidden mb-6">
            <ScreenerAlertsPanel />
          </div>

          {/* Market Share Opportunities */}
          <section id="share-opportunities">
            <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
                <div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-1">Market Share Opportunities</h3>
                  <p className="text-sm text-gray-600 dark:text-slate-400">Actionable insights to grow your market position</p>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="space-y-3">
                  {[
                    { id: 'electronics', label: 'Expand Electronics Presence', sub: 'Currently #2 with 22.4% share', priority: 'HIGH PRIORITY', gain: '+3.8%', rev: '+$312K', color: 'blue' },
                    { id: 'home-kitchen', label: 'Grow Home & Kitchen', sub: 'Currently #4 with 16.8% share', priority: 'MEDIUM PRIORITY', gain: '+2.4%', rev: '+$134K', color: 'indigo' },
                    { id: 'sports', label: 'Defend Sports Position', sub: 'Currently #3 with 19.2% share', priority: 'MAINTAIN', gain: '-1.2%', rev: 'Medium', color: 'sky', type: 'Share at Risk', valColor: 'blue' },
                    { id: 'toys', label: 'Revive Toys & Games', sub: 'Currently #6 with 12.3% share', priority: 'TURNAROUND', gain: '-3%', rev: '+5.2%', color: 'slate', type: 'Current Decline', valColor: 'indigo', revType: 'Potential' },
                  ].map((opp) => (
                    <button
                      key={opp.id}
                      onClick={() => setSelectedOpportunity(opp.id)}
                      className={`w-full text-left bg-white dark:bg-slate-900 dark:from-${opp.color}-900/10 dark:to-${opp.color}-900/20 border-2 transition-all rounded-xl p-4 hover:shadow-lg ${selectedOpportunity === opp.id ? `border-${opp.color}-400 dark:border-${opp.color}-600 shadow-md` : `border-${opp.color}-200 dark:border-${opp.color}-800/50`
                        }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className={`px-3 py-1 bg-${opp.color}-100 text-${opp.color}-700 rounded-lg text-xs font-bold`}>{opp.priority}</span>
                        <i className={`fa-solid fa-chevron-right text-${opp.color}-600`}></i>
                      </div>
                      <h4 className="text-lg font-bold text-gray-900 dark:text-slate-100 mb-1">{opp.label}</h4>
                      <p className="text-sm text-gray-600 dark:text-slate-400">{opp.sub}</p>
                      <div className="mt-3 flex items-center gap-3">
                        <div className="flex-1 bg-white dark:bg-slate-900 rounded-lg p-2 shadow-sm border border-white dark:border-slate-800">
                          <p className="text-xs text-gray-500 dark:text-slate-500">{opp.type || 'Potential Gain'}</p>
                          <p className={`font-bold text-${opp.valColor || opp.color}-900 dark:text-${opp.valColor || opp.color}-400`}>{opp.gain}</p>
                        </div>
                        <div className="flex-1 bg-white dark:bg-slate-900 rounded-lg p-2 shadow-sm border border-white dark:border-slate-800">
                          <p className="text-xs text-gray-500 dark:text-slate-500">{opp.revType || (opp.id === 'sports' ? 'Threat Level' : 'Revenue')}</p>
                          <p className={`font-bold text-${opp.id === 'sports' ? 'red' : 'green'}-900 dark:text-${opp.id === 'sports' ? 'red' : 'green'}-400`}>{opp.rev}</p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>

                <div className="lg:col-span-2">
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={selectedOpportunity}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      className="h-full"
                    >
                      <OpportunityDetail id={selectedOpportunity} />
                    </motion.div>
                  </AnimatePresence>
                </div>
              </div>
            </div>
          </section>
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

            {/* Market Share analysis tabs */}
            <DeepDiveTabBar>
              {[
                { key: 'kpi', label: selectedKpi?.shortLabel || 'Mkt Share' },
                { key: 'distribution', label: 'Distribution' },
                { key: 'by-category', label: 'By Category' },
                { key: 'movements', label: 'Movements' },
                { key: 'charts', label: 'Charts' },
              ].map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => setMktDiveTab(key)}
                  className={`px-3 py-3 text-xs font-semibold transition whitespace-nowrap border-b-2 -mb-px ${
                    mktDiveTab === key
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
                {mktDiveTab === 'kpi' && (
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
                {mktDiveTab === 'distribution' && (
                  <div className="p-3 space-y-2">
                    {[
                      { name: 'Market Leader', value: 28.7, color: '#6366f1' },
                      { name: 'TechMaster Pro', value: 22.3, color: '#3b82f6' },
                      { name: 'Your Brand', value: 18.4, color: '#0ea5e9' },
                      { name: 'EliteGadgets', value: 14.8, color: '#8b5cf6' },
                      { name: 'Others', value: 15.8, color: '#94a3b8' },
                    ].map((b, i) => (
                      <div key={i} className="space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium text-gray-700 dark:text-slate-300 truncate">{b.name}</span>
                          <span className="text-xs font-bold ml-2" style={{ color: b.color }}>{b.value}%</span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-1.5">
                          <div className="h-1.5 rounded-full" style={{ width: `${b.value}%`, backgroundColor: b.color }}></div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {mktDiveTab === 'by-category' && (
                  <div className="p-3 space-y-1.5">
                    {[
                      { label: 'Electronics', share: '22.4%', rank: '#2', trend: '+18%', pos: true },
                      { label: 'Home & Kitchen', share: '16.8%', rank: '#4', trend: '+15%', pos: true },
                      { label: 'Sports & Outdoors', share: '19.2%', rank: '#3', trend: '+8%', pos: true },
                      { label: 'Toys & Games', share: '12.3%', rank: '#6', trend: '-3%', pos: false },
                    ].map((cat, i) => (
                      <div key={i} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-slate-800/50 rounded-lg">
                        <span className="text-xs font-medium text-gray-700 dark:text-slate-300 truncate flex-1">{cat.label}</span>
                        <div className="flex items-center gap-1.5 ml-2 shrink-0">
                          <span className="text-xs font-bold text-gray-700 dark:text-slate-200">{cat.share}</span>
                          <span className="text-[9px] px-1 py-0.5 bg-yellow-50 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 rounded font-bold">{cat.rank}</span>
                          <span className={`text-[10px] font-bold ${cat.pos ? 'text-green-600' : 'text-red-500'}`}>{cat.trend}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {mktDiveTab === 'movements' && (
                  <div className="p-3 space-y-2">
                    {[
                      { title: 'Market Leader gained 2.3% in Electronics', status: 'CRITICAL', color: 'blue', time: '3h ago' },
                      { title: 'You gained 1.8% in Home & Kitchen', status: 'POSITIVE', color: 'indigo', time: '1d ago' },
                      { title: 'MegaTech entered Sports category', status: 'MONITOR', color: 'sky', time: '2d ago' },
                      { title: 'Price war in Electronics accessories', status: 'ACTIVE', color: 'slate', time: '5d ago' },
                    ].map((m, i) => (
                      <div key={i} className={`p-2.5 rounded-r-lg border-l-2 bg-${m.color}-50 dark:bg-${m.color}-900/10 border-${m.color}-400`}>
                        <div className="flex items-center gap-1.5 mb-1">
                          <span className={`text-[9px] px-1 py-0.5 bg-${m.color}-600 text-white rounded font-bold`}>{m.status}</span>
                          <span className="text-[9px] text-gray-400 dark:text-slate-500">{m.time}</span>
                        </div>
                        <p className="text-xs text-gray-700 dark:text-slate-300 font-medium leading-tight line-clamp-2">{m.title}</p>
                      </div>
                    ))}
                  </div>
                )}
                {mktDiveTab === 'charts' && (
                  <div className="p-3 space-y-2">
                    {[
                      { key: 'chart-positioning', icon: 'fa-circle-dot', title: 'Competitive Positioning Matrix', sub: 'Market share vs growth rate' },
                      { key: 'chart-trends', icon: 'fa-chart-line', title: 'Market Share Trends', sub: '12-month trend analysis' },
                    ].map((chart) => (
                      <button
                        key={chart.key}
                        onClick={() => setMktExpandModal(chart.key)}
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
              {mktDiveTab !== 'kpi' && mktDiveTab !== 'charts' && (
                <button
                  onClick={() => setMktExpandModal(mktDiveTab)}
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

      {/* Market Share Deep-Dive Expand Modal */}
      {mktExpandModal && (
        <ScreenerExpandModal
          onClose={() => setMktExpandModal(null)}
          iconWrapClass="bg-blue-100 dark:bg-blue-900/30"
          iconClass={`${expandModalMeta.icon} text-blue-600 dark:text-blue-400 text-sm`}
          title={expandModalMeta.title}
        >
        <MarketShareExpandContent modalKey={mktExpandModal} expandedCategory={expandedCategory} setExpandedCategory={setExpandedCategory} expandedMovement={expandedMovement} setExpandedMovement={setExpandedMovement} />
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

export default MarketShareTab;
