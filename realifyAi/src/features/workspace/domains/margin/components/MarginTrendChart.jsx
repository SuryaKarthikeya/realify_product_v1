import React from 'react';
import BaseAreaChart from '@/components/data-display/charts/BaseAreaChart';
import { CHART_PALETTE } from '@/utils/chartColors';
import { marginTrendData } from '@/features/workspace/domains/margin/data/marginData';
import { formatPercentage } from '@/utils/formatters';

const MarginTrendChart = ({ darkMode }) => {
  return (
    <div className="w-full h-full min-h-[400px]">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
        <div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-slate-100 mb-1">Margin Trend Analysis</h3>
          <p className="text-sm text-gray-600 dark:text-slate-400">7-day gross margin with cost breakdown</p>
        </div>
        <div className="flex items-center gap-2">
          <button className="px-3 py-1.5 bg-brand text-white rounded-lg text-sm font-medium shadow-sm dark:bg-gray-600">Daily</button>
          <button className="px-3 py-1.5 bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 text-gray-700 dark:text-slate-300 rounded-lg text-sm font-medium transition">Weekly</button>
          <button className="px-3 py-1.5 bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 text-gray-700 dark:text-slate-300 rounded-lg text-sm font-medium transition">Monthly</button>
        </div>
      </div>
      
      <div className="h-[300px] w-full">
        <BaseAreaChart 
          data={marginTrendData}
          darkMode={darkMode}
          yAxisFormatter={(val) => formatPercentage(val / 100, 0)}
          tooltipFormatter={(val) => [formatPercentage(val / 100, 1), 'Margin']}
          areas={[
            { key: 'margin', name: 'Gross Margin %', color: CHART_PALETTE.primary }
          ]}
        />
      </div>
      
      <div className="flex items-center justify-center gap-6 mt-4">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-gray-300 dark:bg-slate-700 rounded-full"></div>
          <span className="text-xs text-gray-600 dark:text-slate-400 font-medium">Target (42%)</span>
        </div>
      </div>
    </div>
  );
};

export default MarginTrendChart;
