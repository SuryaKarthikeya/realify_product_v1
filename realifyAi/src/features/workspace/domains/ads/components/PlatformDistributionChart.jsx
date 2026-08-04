import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { platformDistribution } from '@/features/workspace/domains/ads/data/adsData';
import { CHART_CATEGORICAL } from '@/utils/chartColors';

const PlatformDistributionChart = () => {
  return (
    <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
      <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100 mb-4">Platform Distribution</h3>
      <div className="flex items-center justify-center mb-6">
        <div className="relative w-48 h-48">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={platformDistribution}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={0}
                dataKey="value"
                stroke="none"
              >
                {platformDistribution.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={CHART_CATEGORICAL[index % CHART_CATEGORICAL.length]} 
                  />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex items-center justify-center flex-col pointer-events-none">
            <p className="text-2xl font-bold text-gray-900 dark:text-slate-100">$124K</p>
            <p className="text-xs text-gray-500 dark:text-slate-400 font-medium">Total Spend</p>
          </div>
        </div>
      </div>
      <div className="space-y-3">
        {platformDistribution.map((platform, idx) => {
          const color = CHART_CATEGORICAL[idx % CHART_CATEGORICAL.length];

          return (
            <div key={idx} className="flex items-center justify-between p-3 rounded-xl border bg-gray-50 dark:bg-slate-800/50 border-gray-100 dark:border-slate-700/50">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full shadow-sm" style={{ backgroundColor: color }}></div>
                <span className="text-sm font-medium text-gray-700 dark:text-slate-300">{platform.name}</span>
              </div>
              <span className="text-sm font-bold text-gray-900 dark:text-slate-100">${(platform.value / 1000)}K ({platform.percentage})</span>
            </div>
          );
        })}
      </div>
      <div className="mt-6 p-4 bg-gray-50 dark:bg-slate-800/50 rounded-xl border border-gray-100 dark:border-slate-700">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-600 dark:text-slate-400 font-medium">Overall ROAS</span>
          <span className="text-xs bg-gray-700 dark:bg-slate-600 text-white px-2 py-1 rounded-lg font-medium shadow-sm">
            <i className="fa-solid fa-arrow-up mr-1 text-[10px]"></i>+18.2%
          </span>
        </div>
        <p className="text-sm font-bold text-gray-900 dark:text-slate-100">4.8x Return</p>
      </div>
    </div>
  );
};

export default PlatformDistributionChart;
