import React from 'react';

const CashDistributionSection = () => {
  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
      <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100 mb-4">Cash Distribution</h3>
      <div className="flex items-center justify-center mb-6">
        <div className="relative w-48 h-48">
          <svg className="w-full h-full transform -rotate-90">
            <circle cx="96" cy="96" r="80" fill="none" stroke="#f3f4f6" strokeWidth="32" className="dark:stroke-slate-800"></circle>
            <circle cx="96" cy="96" r="80" fill="none" style={{ stroke: 'rgb(var(--cb-600))' }} strokeWidth="32"
              strokeDasharray="502.4" strokeDashoffset="125.6"></circle>
            <circle cx="96" cy="96" r="80" fill="none" style={{ stroke: 'rgb(var(--cb-700))' }} strokeWidth="32"
              strokeDasharray="502.4" strokeDashoffset="326.56"></circle>
            <circle cx="96" cy="96" r="80" fill="none" style={{ stroke: 'rgb(var(--cb-800))' }} strokeWidth="32"
              strokeDasharray="502.4" strokeDashoffset="452.16"></circle>
          </svg>
          <div className="absolute inset-0 flex items-center justify-center flex-col">
            <p className="text-2xl font-bold text-gray-900 dark:text-slate-100">$286K</p>
            <p className="text-xs text-gray-500 dark:text-slate-400 font-medium">Total Cash</p>
          </div>
        </div>
      </div>
      <div className="space-y-3">
        <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-700/50">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 bg-cb-600 rounded-full shadow-sm"></div>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Savings</span>
          </div>
          <span className="text-sm font-bold text-gray-900 dark:text-slate-100">$186K (65%)</span>
        </div>
        <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-700/50">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 bg-cb-700 rounded-full shadow-sm"></div>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Payroll</span>
          </div>
          <span className="text-sm font-bold text-gray-900 dark:text-slate-100">$57K (20%)</span>
        </div>
        <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-700/50">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 bg-cb-800 rounded-full shadow-sm"></div>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Operating</span>
          </div>
          <span className="text-sm font-bold text-gray-900 dark:text-slate-100">$43K (15%)</span>
        </div>
      </div>
      <div className="mt-6 p-4 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-700">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-600 dark:text-gray-400 font-medium">Cash Runway</span>
          <span className="text-xs bg-gray-700 dark:bg-slate-600 text-white px-2 py-1 rounded-lg font-medium shadow-sm">
            <i className="fa-solid fa-calendar mr-1"></i>4.2 months
          </span>
        </div>
        <p className="text-sm font-bold text-gray-900 dark:text-slate-100">Healthy Position</p>
      </div>
    </div>
  );
};

export default CashDistributionSection;
