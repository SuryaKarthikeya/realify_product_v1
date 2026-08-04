import React, { useState } from 'react';
import Modal from '@/components/overlays/Modal';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import DataTable from '@/components/data-display/DataTable';

const mockChartData = [
  { name: '1', value: 12 },
  { name: '2', value: 14 },
  { name: '3', value: 13 },
  { name: '4', value: 15 },
  { name: '5', value: 14 },
  { name: '6', value: 12 },
  { name: '7', value: 13 },
];

const AnalyticsModal = ({ isOpen, onClose, data, tableOnly = false }) => {
  const [activePeriod, setActivePeriod] = useState('30d');
  const [activeChannel, setActiveChannel] = useState('All');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');

  if (!data) return null;

  const isKpi = !!data.title;

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div
        className="bg-white dark:bg-slate-900 w-full max-w-5xl max-h-[92vh] rounded-[1.5rem] shadow-2xl overflow-hidden flex flex-col border border-gray-100 dark:border-slate-800 animate-fadeIn"
        onClick={e => e.stopPropagation()}
      >

        {/* Header */}
        <div className="p-6 flex items-center justify-between border-b border-gray-50 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className={`w-8 h-8 ${isKpi ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-600' : 'bg-blue-100 dark:bg-blue-900/30 text-blue-600'} rounded-lg flex items-center justify-center`}>
              <i className={`fa-solid ${data.icon || 'fa-chart-line'} text-sm`}></i>
            </div>
            <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">
              {isKpi ? `${data.title} · Analysis` : `${data.name} · Analysis`}
            </h2>
          </div>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-400 transition-colors">
            <i className="fa-solid fa-xmark"></i>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-5">

          {!tableOnly && (
            <>
              {/* Universal Filters */}
              <div className="flex flex-wrap items-center gap-4">
                <div className="flex bg-gray-50 dark:bg-slate-800 p-1 rounded-xl border border-gray-100 dark:border-slate-700">
                  {['7d', '30d', '90d', 'Custom'].map(t => (
                    <button
                      key={t}
                      onClick={() => setActivePeriod(t)}
                      className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${activePeriod === t ? 'bg-brand text-white shadow-sm dark:bg-gray-600' : 'text-gray-500 hover:text-gray-700 dark:hover:text-slate-300'}`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
                {activePeriod === 'Custom' && (
                  <div className="flex items-center gap-2">
                    <input
                      type="date"
                      value={customStart}
                      onChange={e => setCustomStart(e.target.value)}
                      className="px-3 py-1.5 text-xs rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-gray-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-brand/30"
                    />
                    <span className="text-xs text-gray-400">to</span>
                    <input
                      type="date"
                      value={customEnd}
                      onChange={e => setCustomEnd(e.target.value)}
                      className="px-3 py-1.5 text-xs rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-gray-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-brand/30"
                    />
                  </div>
                )}
                <div className="flex bg-gray-50 dark:bg-slate-800 p-1 rounded-xl border border-gray-100 dark:border-slate-700">
                  {['All', 'Amazon', 'Shopify'].map(c => (
                    <button
                      key={c}
                      onClick={() => setActiveChannel(c)}
                      className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${activeChannel === c ? 'bg-[#3e93ab] text-white shadow-sm' : 'text-gray-500 hover:text-gray-700 dark:hover:text-slate-300'}`}
                    >
                      {c}
                    </button>
                  ))}
                </div>
              </div>

              {/* Metric Highlights Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {(data.cards || []).map((kpi, idx) => (
                  <div key={idx} className="bg-white dark:bg-slate-800/50 p-5 rounded-2xl border border-gray-100 dark:border-slate-800 shadow-sm transition-transform hover:scale-[1.02]">
                    <p className="text-[10px] font-bold text-gray-400 tracking-wider mb-2">{kpi.label}</p>
                    <h4 className={`text-2xl font-bold ${kpi.color || 'text-slate-800 dark:text-slate-100'} mb-1`}>{kpi.val}</h4>
                    <p className={`text-[10px] font-bold ${kpi.delta ? (kpi.delta.startsWith('-') ? 'text-red-500' : 'text-green-500') : 'text-gray-400'}`}>
                      {kpi.delta || kpi.sub || ''}
                    </p>
                  </div>
                ))}
              </div>

              {/* Interactive Chart Section */}
              <div className="h-[300px] w-full pt-4 flex items-center justify-center">
                {data.chartType === 'donut' ? (
                  <div className="flex items-center gap-5">
                    <div className="relative w-48 h-48">
                      <svg className="w-full h-full transform -rotate-90">
                        <circle cx="96" cy="96" r="80" fill="none" stroke="currentColor" strokeWidth="32" className="text-gray-100 dark:text-slate-800"></circle>
                        <circle cx="96" cy="96" r="80" fill="none" stroke="#0A52E7" strokeWidth="32" strokeDasharray="502.4" strokeDashoffset="125.6"></circle>
                        <circle cx="96" cy="96" r="80" fill="none" stroke="#1D63FF" strokeWidth="32" strokeDasharray="502.4" strokeDashoffset="276.32"></circle>
                        <circle cx="96" cy="96" r="80" fill="none" stroke="#2E4CB9" strokeWidth="32" strokeDasharray="502.4" strokeDashoffset="401.92"></circle>
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center flex-col">
                        <p className="text-2xl font-bold text-gray-900 dark:text-slate-100">100%</p>
                        <p className="text-xs text-gray-500 dark:text-slate-400 font-medium">Total Sales</p>
                      </div>
                    </div>
                    <div className="space-y-3">
                      {(data.donutSegments || []).map((seg, idx) => (
                        <div key={idx} className={`flex items-center justify-between px-4 py-3 rounded-xl border ${seg.bgColor} ${seg.borderColor} min-w-[220px]`}>
                          <div className="flex items-center gap-3">
                            <div className="w-3 h-3 rounded-full shadow-sm flex-shrink-0" style={{ backgroundColor: seg.color }}></div>
                            <span className="text-sm font-medium text-gray-700 dark:text-slate-300">{seg.label}</span>
                          </div>
                          <div className="text-right ml-4">
                            <div className="text-sm font-bold text-gray-900 dark:text-slate-100">{seg.value}</div>
                            {seg.amount && <div className="text-[11px] text-gray-500 dark:text-slate-400">{seg.amount}</div>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data.chartData || mockChartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="primaryGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={isKpi ? "#9333ea" : "#3b82f6"} stopOpacity={0.15} />
                          <stop offset="95%" stopColor={isKpi ? "#9333ea" : "#3b82f6"} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(203, 213, 225, 0.2)" />
                      <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#94a3b8' }} dy={10} />
                      <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#94a3b8' }} />
                      <Tooltip contentStyle={{ backgroundColor: 'var(--tooltip-bg)', border: '1px solid var(--tooltip-border)', borderRadius: '12px', fontSize: '12px', color: 'var(--tooltip-text)' }} />
                      <Area type="monotone" dataKey="value" stroke={isKpi ? "#9333ea" : "#3b82f6"} strokeWidth={3} fillOpacity={1} fill="url(#primaryGradient)" />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </div>
            </>
          )}

          {/* Dynamic Data Table */}
          <div className="pt-4 overflow-hidden">
            <DataTable
              columns={data.tableColumns || []}
              data={data.tableData || []}
              title={isKpi ? "Supporting Factors" : "Performance Metrics"}
            />
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default AnalyticsModal;
