import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import DashboardLayout from '@/layouts/DashboardLayout';
import { screenerActionDetails } from '@/features/screener/data/screenerAlerts';

const priorityConfig = {
  'HIGH IMPACT': { pillBg: 'bg-blue-600', pillText: 'text-white', labelText: 'text-blue-600 dark:text-blue-400' },
  'URGENT': { pillBg: 'bg-red-600', pillText: 'text-white', labelText: 'text-red-600 dark:text-red-400' },
  'GROWTH': { pillBg: 'bg-purple-600', pillText: 'text-white', labelText: 'text-purple-600 dark:text-purple-400' },
  'RETENTION': { pillBg: 'bg-emerald-600', pillText: 'text-white', labelText: 'text-emerald-600 dark:text-emerald-400' },
};

const filters = ['All', 'High Impact', 'Urgent', 'Growth', 'Retention'];

const ScreenerActionDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activeFilter, setActiveFilter] = useState('All');

  const action = screenerActionDetails.find(a => a.id === id) || screenerActionDetails[0];
  const cfg = priorityConfig[action.priorityLabel] || priorityConfig['HIGH IMPACT'];

  const filteredActions = activeFilter === 'All'
    ? screenerActionDetails
    : screenerActionDetails.filter(a =>
        a.priorityLabel.toLowerCase().replace(' ', '-') === activeFilter.toLowerCase().replace(' ', '-')
      );

  return (
    <DashboardLayout
      title="Research"
      subtitle="Real-time analytics and predictive insights"
      showTabs={false}
      showAIPrompt={false}
    >
      <div className="flex gap-6 items-start">

        {/* Left — main content */}
        <div className="flex-1 min-w-0">

          {/* Back + Custom Action row */}
          <div className="flex items-center justify-between mb-5">
            <button
              onClick={() => navigate('/research')}
              className="flex items-center gap-1.5 text-sm text-gray-500 dark:text-slate-400 hover:text-gray-800 dark:hover:text-slate-200 transition-colors font-medium"
            >
              <i className="fa-solid fa-arrow-left text-xs"></i>
              Back to Research
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl text-sm font-semibold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition shadow-sm">
              <i className="fa-solid fa-plus text-[10px]"></i>
              Custom Action
            </button>
          </div>

          {/* Main card */}
          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm">
            <div className="p-6">

              {/* Priority + ID + time + Simulate */}
              <div className="flex items-start justify-between mb-5">
                <div className="flex items-center gap-2.5 flex-wrap">
                  <span className={`inline-flex items-center px-3 py-1 ${cfg.pillBg} ${cfg.pillText} text-[10px] font-bold tracking-wider rounded-lg`}>
                    {action.priorityLabel}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-slate-400 font-medium">{action.actionId}</span>
                  <span className="text-gray-300 dark:text-slate-600">·</span>
                  <span className="text-xs text-gray-400 dark:text-slate-500">{action.time}</span>
                </div>
                <button className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg text-sm font-semibold text-gray-600 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-700 transition flex-shrink-0">
                  <i className="fa-solid fa-flask text-xs"></i>
                  Simulate
                </button>
              </div>

              {/* Title */}
              <h2 className="text-2xl font-bold text-gray-900 dark:text-slate-100 mb-7">{action.title}</h2>

              {/* Analysis Insights */}
              <div className="mb-6">
                <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 tracking-widest uppercase mb-2.5">
                  Analysis Insights
                </p>
                <p className="text-sm text-gray-700 dark:text-slate-300 leading-relaxed">{action.analysisText}</p>
              </div>

              {/* Key Metrics */}
              <div className="mb-6">
                <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 tracking-widest uppercase mb-2.5">
                  Key Metrics
                </p>
                <div className="grid grid-cols-2 gap-3">
                  {action.metrics.map((m, i) => (
                    <div key={i} className="bg-gray-50 dark:bg-slate-800/60 rounded-xl p-4 border border-gray-100 dark:border-slate-800">
                      <p className="text-xs text-gray-500 dark:text-slate-400 mb-1.5">{m.label}</p>
                      <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{m.value}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Implementation Plan */}
              <div className="mb-6">
                <p className="text-[10px] font-bold text-gray-400 dark:text-slate-500 tracking-widest uppercase mb-2.5">
                  Implementation Plan
                </p>
                <p className="text-sm font-semibold text-teal-700 dark:text-teal-400 leading-relaxed">
                  {action.implementationPlan}
                </p>
              </div>

              {/* Guardrails & Risks */}
              <div>
                <p className="text-[10px] font-bold text-orange-500 dark:text-orange-400 tracking-widest uppercase mb-2.5">
                  <i className="fa-solid fa-shield-halved mr-1.5"></i>
                  Guardrails & Risks
                </p>
                <p className="text-sm text-gray-600 dark:text-slate-400 leading-relaxed">{action.guardrails}</p>
              </div>

            </div>
          </div>
        </div>

        {/* Right — Actions sidebar */}
        <div className="w-72 shrink-0 sticky top-4">
          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">

            {/* Header */}
            <div className="px-4 py-3.5 border-b border-gray-100 dark:border-slate-800 flex items-center justify-between">
              <h3 className="font-bold text-gray-900 dark:text-slate-100">Actions</h3>
              <span className="w-6 h-6 bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900 text-xs font-bold rounded-full flex items-center justify-center">
                {screenerActionDetails.length}
              </span>
            </div>

            {/* Filter tabs */}
            <div className="px-3 py-2.5 border-b border-gray-100 dark:border-slate-800 flex flex-wrap gap-1.5">
              {filters.map(f => (
                <button
                  key={f}
                  onClick={() => setActiveFilter(f)}
                  className={`px-2.5 py-1 text-xs font-bold rounded-lg transition ${
                    activeFilter === f
                      ? 'bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900'
                      : 'text-gray-500 dark:text-slate-400 hover:bg-gray-100 dark:hover:bg-slate-800'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>

            {/* Action list */}
            <div className="divide-y divide-gray-50 dark:divide-slate-800/60">
              {(filteredActions.length > 0 ? filteredActions : screenerActionDetails).map(a => {
                const isSelected = a.id === action.id;
                const aCfg = priorityConfig[a.priorityLabel] || priorityConfig['HIGH IMPACT'];
                return (
                  <button
                    key={a.id}
                    onClick={() => navigate(`/screener/actions/${a.id}`)}
                    className={`w-full text-left px-4 py-3.5 border-l-[3px] transition hover:bg-gray-50 dark:hover:bg-slate-800/50 ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50/40 dark:bg-blue-900/10'
                        : 'border-transparent'
                    }`}
                  >
                    <span className={`text-[9px] font-bold tracking-widest uppercase ${aCfg.labelText}`}>
                      {a.priorityLabel}
                    </span>
                    <p className={`text-sm font-semibold mt-0.5 leading-snug ${
                      isSelected ? 'text-blue-600 dark:text-blue-400' : 'text-gray-800 dark:text-slate-200'
                    }`}>
                      {a.title}
                    </p>
                    <p className="text-xs text-gray-400 dark:text-slate-500 mt-0.5">{a.time}</p>
                  </button>
                );
              })}
            </div>

          </div>
        </div>

      </div>
    </DashboardLayout>
  );
};

export default ScreenerActionDetailPage;
